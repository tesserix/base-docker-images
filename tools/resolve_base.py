#!/usr/bin/env python3
"""Resolve the latest upstream base image for each image in images/.

The weekly rebuild passes the result to `docker build --build-arg BASE_IMAGE=...`,
so an upstream minor release is picked up without a commit, while the resolved
digest keeps the build reproducible after the fact.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

IMAGES = Path(__file__).resolve().parent.parent / "images"
KINDS = frozenset({"docker-hub", "registry-tag", "github-release"})
HUB = "https://hub.docker.com/v2/repositories"


class ResolutionError(RuntimeError):
    pass


@dataclass(frozen=True)
class Source:
    kind: str
    repo: str
    name_filter: str | None = None
    pattern: str | None = None
    tag: str | None = None
    build_args: dict[str, dict] | None = None


def load_source(image_dir: Path) -> Source:
    config = json.loads((image_dir / "base-source.json").read_text())
    if config["kind"] not in KINDS:
        raise ResolutionError(f"{image_dir.name}: unknown kind {config['kind']!r}")
    return Source(**config)


def resolve_build_args(source: Source, **fetchers) -> dict[str, str]:
    args = {"BASE_IMAGE": resolve(source, **fetchers)}
    for name, spec in (source.build_args or {}).items():
        if spec["kind"] not in KINDS:
            raise ResolutionError(f"{name}: unknown kind {spec['kind']!r}")
        args[name] = resolve(Source(**spec), **fetchers)
    return args


def version_key(tag: str) -> tuple[int, ...]:
    return tuple(int(n) for n in re.findall(r"\d+", tag))


def select_latest(tags: list[str], pattern: str) -> str:
    matching = [t for t in tags if re.match(pattern, t)]
    if not matching:
        raise ResolutionError(f"no tag matched {pattern!r} in {len(tags)} candidates")
    return max(matching, key=version_key)


def _get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 — https literal
        return json.load(response)


def fetch_docker_hub_tags(
    repo: str, name_filter: str, *, fetch_json=_get_json, max_pages: int = 5
) -> list[str]:
    url = f"{HUB}/{repo}/tags?page_size=100&name={name_filter}"
    tags: list[str] = []
    for _ in range(max_pages):
        page = fetch_json(url)
        tags.extend(result["name"] for result in page["results"])
        url = page.get("next")
        if not url:
            break
    return tags


def fetch_digest(ref: str, *, run=subprocess.run) -> str:
    command = ["docker", "buildx", "imagetools", "inspect", ref, "--format", "{{.Manifest.Digest}}"]
    result = run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise ResolutionError(f"could not inspect {ref}: {result.stderr.strip()}")
    return result.stdout.strip()


def fetch_release(repo: str, *, run=subprocess.run) -> str:
    command = ["gh", "release", "list", "--repo", repo, "--exclude-pre-releases",
               "--limit", "1", "--json", "tagName", "--jq", ".[0].tagName"]
    result = run(command, capture_output=True, text=True)
    tag = result.stdout.strip()
    if result.returncode != 0 or not tag:
        raise ResolutionError(f"no stable release found for {repo}: {result.stderr.strip()}")
    return tag


ARG_LINE = re.compile(r"^ARG BASE_IMAGE=(\S+)$", re.M)


def sync_default(dockerfile: str, ref: str) -> tuple[str, bool]:
    match = ARG_LINE.search(dockerfile)
    if not match:
        raise ResolutionError("no `ARG BASE_IMAGE=` line to sync")
    if match[1] == ref:
        return dockerfile, False
    return dockerfile[: match.start(1)] + ref + dockerfile[match.end(1) :], True


def _image_name(repo: str) -> str:
    return repo.removeprefix("library/")


def resolve(
    source: Source,
    *,
    fetch_tags=fetch_docker_hub_tags,
    fetch_digest=fetch_digest,
    fetch_release=fetch_release,
    with_digest: bool = True,
) -> str:
    if source.kind == "github-release":
        return fetch_release(source.repo)

    if source.kind == "registry-tag":
        ref = f"{source.repo}:{source.tag}"
    else:
        tags = fetch_tags(source.repo, source.name_filter)
        ref = f"{_image_name(source.repo)}:{select_latest(tags, source.pattern)}"

    return f"{ref}@{fetch_digest(ref)}" if with_digest else ref


def _image_dirs() -> list[Path]:
    return sorted(p for p in IMAGES.iterdir() if (p / "base-source.json").is_file())


def _sync_all(with_digest: bool) -> int:
    drifted = []
    for image in _image_dirs():
        dockerfile = image / "Dockerfile"
        ref = resolve(load_source(image), with_digest=with_digest)
        updated, changed = sync_default(dockerfile.read_text(), ref)
        if changed:
            dockerfile.write_text(updated)
            drifted.append(f"{image.name}: {ref}")
    print("\n".join(drifted) if drifted else "every image is on its latest upstream")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", nargs="?", help="directory name under images/")
    parser.add_argument("--all", action="store_true", help="resolve every image as JSON")
    parser.add_argument("--no-digest", action="store_true", help="skip digest pinning")
    parser.add_argument("--build-args", action="store_true",
                        help="print every KEY=VALUE this image's build needs")
    parser.add_argument("--sync", action="store_true",
                        help="rewrite each Dockerfile's ARG default to the resolved version")
    args = parser.parse_args(argv)

    with_digest = not args.no_digest
    if args.sync:
        return _sync_all(with_digest)

    if args.all:
        resolved = {
            path.name: resolve(load_source(path), with_digest=with_digest)
            for path in sorted(IMAGES.iterdir())
            if (path / "base-source.json").is_file()
        }
        print(json.dumps(resolved, indent=2))
        return 0

    if not args.image:
        parser.error("give an image name or --all")

    source = load_source(IMAGES / args.image)
    if args.build_args:
        resolved = resolve_build_args(source, with_digest=with_digest)
        print("\n".join(f"{key}={value}" for key, value in resolved.items()))
    else:
        print(resolve(source, with_digest=with_digest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
