import json
import re
from pathlib import Path

import pytest

import resolve_base as rb

IMAGES = Path(__file__).resolve().parent.parent / "images"


class TestVersionKey:
    def test_orders_patch_numerically_not_lexically(self):
        assert rb.version_key("3.13.10-slim") > rb.version_key("3.13.9-slim")

    def test_orders_on_the_trailing_variant_when_the_version_ties(self):
        assert rb.version_key("1.26.3-alpine3.23") > rb.version_key("1.26.3-alpine3.22")

    def test_reads_a_date_stamped_tag_as_one_number(self):
        assert rb.version_key("trixie-20260815-slim") > rb.version_key("trixie-20260101-slim")


class TestSelectLatest:
    def test_picks_the_highest_matching_tag(self):
        tags = ["3.13.1-slim", "3.13.11-slim", "3.13.2-slim"]
        assert rb.select_latest(tags, r"^3\.13\.\d+-slim$") == "3.13.11-slim"

    def test_ignores_tags_outside_the_tracked_line(self):
        tags = ["3.13.1-slim", "3.14.0-slim", "3.13.2-slim", "3.13.2-alpine"]
        assert rb.select_latest(tags, r"^3\.13\.\d+-slim$") == "3.13.2-slim"

    def test_raises_when_nothing_matches_rather_than_falling_back(self):
        with pytest.raises(rb.ResolutionError):
            rb.select_latest(["latest", "3.12.1-slim"], r"^3\.13\.\d+-slim$")


class TestDockerHub:
    def test_follows_pagination_until_the_next_link_is_empty(self):
        pages = {
            "https://hub.docker.com/v2/repositories/library/python/tags?page_size=100&name=3.13.": {
                "results": [{"name": "3.13.1-slim"}],
                "next": "https://hub.docker.com/v2/next",
            },
            "https://hub.docker.com/v2/next": {"results": [{"name": "3.13.2-slim"}], "next": None},
        }
        tags = rb.fetch_docker_hub_tags("library/python", "3.13.", fetch_json=pages.__getitem__)
        assert tags == ["3.13.1-slim", "3.13.2-slim"]

    def test_stops_at_the_page_cap_so_a_bad_filter_cannot_spin(self):
        forever = {"results": [{"name": "3.13.1-slim"}], "next": "https://hub.docker.com/v2/loop"}
        calls = []

        def fetch_json(url):
            calls.append(url)
            return forever

        rb.fetch_docker_hub_tags("library/python", "3.13.", fetch_json=fetch_json, max_pages=3)
        assert len(calls) == 3


class TestResolve:
    def test_docker_hub_source_returns_tag_pinned_by_digest(self):
        source = rb.Source(
            kind="docker-hub", repo="library/python", name_filter="3.13.", pattern=r"^3\.13\.\d+-slim$"
        )
        ref = rb.resolve(
            source,
            fetch_tags=lambda *_, **__: ["3.13.4-slim", "3.13.5-slim"],
            fetch_digest=lambda ref: "sha256:" + "a" * 64,
        )
        assert ref == "python:3.13.5-slim@sha256:" + "a" * 64

    def test_registry_tag_source_resolves_the_digest_of_a_fixed_tag(self):
        source = rb.Source(kind="registry-tag", repo="gcr.io/distroless/static", tag="nonroot")
        ref = rb.resolve(source, fetch_digest=lambda ref: "sha256:" + "b" * 64)
        assert ref == "gcr.io/distroless/static:nonroot@sha256:" + "b" * 64

    def test_github_release_source_returns_the_latest_stable_tag(self):
        source = rb.Source(kind="github-release", repo="tesserix/agent-development-kit")
        assert rb.resolve(source, fetch_release=lambda repo: "v0.51.0") == "v0.51.0"

    def test_digest_is_omitted_when_pinning_is_turned_off(self):
        source = rb.Source(
            kind="docker-hub", repo="library/alpine", name_filter="3.", pattern=r"^3\.\d+\.\d+$"
        )
        ref = rb.resolve(source, fetch_tags=lambda *_, **__: ["3.24.1"], with_digest=False)
        assert ref == "alpine:3.24.1"


class TestBuildArgs:
    def test_always_carries_the_resolved_base_image(self):
        source = rb.Source(kind="registry-tag", repo="gcr.io/distroless/static", tag="nonroot")
        args = rb.resolve_build_args(source, fetch_digest=lambda ref: "sha256:" + "c" * 64)
        assert args == {"BASE_IMAGE": "gcr.io/distroless/static:nonroot@sha256:" + "c" * 64}

    def test_resolves_each_declared_extra_from_its_own_source(self):
        source = rb.Source(
            kind="registry-tag",
            repo="ghcr.io/tesserix/base-python-runtime-3.13",
            tag="weekly",
            build_args={
                "ADK_VERSION": {"kind": "github-release", "repo": "tesserix/agent-development-kit"}
            },
        )
        args = rb.resolve_build_args(
            source,
            fetch_digest=lambda ref: "sha256:" + "d" * 64,
            fetch_release=lambda repo: "v0.51.0",
        )
        assert args["ADK_VERSION"] == "v0.51.0"
        assert args["BASE_IMAGE"].startswith("ghcr.io/tesserix/base-python-runtime-3.13:weekly@")

    def test_rejects_an_extra_the_resolver_does_not_understand(self):
        source = rb.Source(kind="registry-tag", repo="x/y", tag="t",
                           build_args={"NOPE": {"kind": "carrier-pigeon", "repo": "x/y"}})
        with pytest.raises(rb.ResolutionError):
            rb.resolve_build_args(source, fetch_digest=lambda ref: "sha256:" + "e" * 64)


class TestSyncDefault:
    DOCKERFILE = (
        "# header comment\n"
        "ARG BASE_IMAGE=python:3.13.14-slim\n"
        "FROM ${BASE_IMAGE}\n"
        "RUN echo BASE_IMAGE=python:3.13.14-slim\n"
    )

    def test_rewrites_the_arg_default_to_the_resolved_reference(self):
        updated, changed = rb.sync_default(self.DOCKERFILE, "python:3.13.15-slim")
        assert changed is True
        assert "ARG BASE_IMAGE=python:3.13.15-slim\n" in updated

    def test_reports_no_change_when_the_default_is_already_current(self):
        updated, changed = rb.sync_default(self.DOCKERFILE, "python:3.13.14-slim")
        assert changed is False
        assert updated == self.DOCKERFILE

    def test_touches_only_the_arg_line(self):
        updated, _ = rb.sync_default(self.DOCKERFILE, "python:3.13.15-slim")
        assert "RUN echo BASE_IMAGE=python:3.13.14-slim\n" in updated
        assert updated.startswith("# header comment\n")

    def test_raises_when_there_is_no_arg_to_sync(self):
        with pytest.raises(rb.ResolutionError):
            rb.sync_default("FROM python:3.13.14-slim\n", "python:3.13.15-slim")


class TestRepositoryConsistency:
    """Every image must be resolvable, and its committed default must obey its own rule."""

    def image_dirs(self):
        return sorted(p for p in IMAGES.iterdir() if (p / "Dockerfile").is_file())

    def test_every_image_declares_a_source(self):
        missing = [p.name for p in self.image_dirs() if not (p / "base-source.json").is_file()]
        assert missing == []

    def test_every_dockerfile_builds_from_an_overridable_arg(self):
        offenders = []
        for image in self.image_dirs():
            body = (image / "Dockerfile").read_text()
            if not re.search(r"^ARG BASE_IMAGE=\S+$", body, re.M):
                offenders.append(image.name)
            elif not re.search(r"^FROM \$\{BASE_IMAGE\}", body, re.M):
                offenders.append(image.name)
        assert offenders == []

    def test_committed_default_matches_the_pattern_the_resolver_tracks(self):
        drifted = []
        for image in self.image_dirs():
            source = rb.load_source(image)
            if source.pattern is None:
                continue
            default = re.search(r"^ARG BASE_IMAGE=(\S+)$", (image / "Dockerfile").read_text(), re.M)[1]
            tag = default.split("@", 1)[0].rsplit(":", 1)[-1]
            if not re.match(source.pattern, tag):
                drifted.append(f"{image.name}: {tag} !~ {source.pattern}")
        assert drifted == []

    def test_every_source_config_is_a_kind_the_resolver_understands(self):
        for image in self.image_dirs():
            config = json.loads((image / "base-source.json").read_text())
            assert config["kind"] in rb.KINDS, f"{image.name}: {config['kind']}"
            for name, spec in (config.get("build_args") or {}).items():
                assert spec["kind"] in rb.KINDS, f"{image.name}.{name}: {spec['kind']}"

    def test_every_image_in_the_matrix_has_a_directory_and_vice_versa(self):
        workflow = (IMAGES.parent / ".github/workflows/weekly-rebuild.yml").read_text()
        in_matrix = set(re.findall(r"^\s+- (\S+)$", workflow, re.M))
        on_disk = {p.name for p in self.image_dirs()}
        assert on_disk <= in_matrix, f"not built by CI: {sorted(on_disk - in_matrix)}"
