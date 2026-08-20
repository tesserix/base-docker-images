# tesserix / base-docker-images

[![Weekly base-image rebuild](https://github.com/tesserix/base-docker-images/actions/workflows/weekly-rebuild.yml/badge.svg?branch=main)](https://github.com/tesserix/base-docker-images/actions/workflows/weekly-rebuild.yml)
[![Dependabot Updates](https://github.com/tesserix/base-docker-images/actions/workflows/dependabot/dependabot-updates/badge.svg?branch=main)](https://github.com/tesserix/base-docker-images/actions/workflows/dependabot/dependabot-updates)

Company-owned base Docker images. One canonical, hardened set for every
app and service in the tesserix org — so upstream CVEs get patched in
one place and every downstream Dockerfile stays lean and consistent.

Every image is published to **`ghcr.io/tesserix/base-*`** and scanned
weekly; anything that doesn't pass the Trivy CRITICAL+HIGH gate never
reaches the registry.

## Images

| Name                                        | Upstream                             | Purpose                                                                 |
|---------------------------------------------|--------------------------------------|-------------------------------------------------------------------------|
| `ghcr.io/tesserix/base-go-builder`          | `golang:1.26-alpine`                 | Go build stage — git, tzdata, ca-certs, non-root 10001                  |
| `ghcr.io/tesserix/base-alpine-runtime`      | `alpine:3.23`                        | Minimal runtime for Go / Rust static binaries — tini, tzdata, ca-certs, non-root 10001 |
| `ghcr.io/tesserix/base-node-builder-22`     | `node:22-alpine`                     | Next.js / Turborepo build stage for Node 22 (Jod LTS)                   |
| `ghcr.io/tesserix/base-node-runtime-22`     | `node:22-alpine`                     | Next.js standalone runtime for Node 22                                  |
| `ghcr.io/tesserix/base-node-builder-24`     | `node:24-alpine`                     | Next.js / Turborepo build stage for Node 24 (Krypton LTS)               |
| `ghcr.io/tesserix/base-node-runtime-24`     | `node:24-alpine`                     | Next.js standalone runtime for Node 24                                  |
| `ghcr.io/tesserix/base-nginx-spa`           | `nginx:1.29-alpine`                  | Static SPA serve — SPA fallback, brotli/gzip, non-root :8080            |
| `ghcr.io/tesserix/base-python-runtime-3.13` | `python:3.13-slim`                   | Python runtime for FastAPI / worker services — tini, curl, ca-certs     |
| `ghcr.io/tesserix/base-debian-runtime`      | `debian:trixie-slim`                 | Glibc-linked runtime when musl is not an option                         |
| `ghcr.io/tesserix/base-distroless-static`   | `gcr.io/distroless/static:nonroot`   | Pass-through for Go static binaries — zero shell, uid 65532             |

## Tags

| Tag          | Meaning                                                                           |
|--------------|-----------------------------------------------------------------------------------|
| `:latest`    | Alias of `:weekly`. Pick this when you want patches automatically.                |
| `:weekly`    | Moving tag, last green weekly build.                                              |
| `:YYYYMMDD`  | Immutable per-week tag (e.g. `:20260425`). Pin this when you want deliberate upgrades. |
| `:sha-<12>`  | Git-anchored immutable tag. Useful for reproducing a downstream build.            |

## Lifecycle

- **Every Saturday 03:00 UTC** — `weekly-rebuild.yml` runs. Each image
  resolves its latest upstream version (below) and is built with
  `docker build --pull` so upstream index refreshes are picked up.
- **Trivy gate** — CRITICAL + HIGH fail the build; nothing reaches the
  registry until it scans clean.
- **Security alert** — a red weekly run emails
  `samyak.rout@gmail.com`, `mahesh.sangawar@gmail.com`,
  `unidevidp@gmail.com` via Gmail SMTP (`SMTP_USERNAME` and
  `SMTP_PASSWORD` repo secrets required).
- **Downstream notify** — opt-in consumer repos (FanZone, mark8ly,
  HomeChef) get a
  `repository_dispatch: tesserix-base-images-updated` after a
  successful weekly run. Each consumer ships its own
  `base-image-refresh.yml` that rebuilds on receipt.

## Upstream version resolution

No Dockerfile hard-codes the upstream version it builds on. Each image
declares where its base comes from in `images/<name>/base-source.json`,
and `tools/resolve_base.py` resolves the latest release on that line at
build time:

```bash
python3 tools/resolve_base.py python-runtime-3.13
# python:3.13.15-slim@sha256:…

python3 tools/resolve_base.py --all --no-digest    # every image, no registry round-trip
```

The weekly job passes the result as `--build-arg BASE_IMAGE=…`, so an
upstream patch or minor release is picked up without a commit. The
resolved reference is pinned by digest and recorded on the built image
as `org.opencontainers.image.base.name`, so a published image can always
be traced back to the exact upstream layer it was built on.

An image may declare extra build arguments alongside its base, each resolved
from its own source. `python-adk-3.13` uses this to track the latest ADK
release:

```json
{
  "kind": "registry-tag",
  "repo": "ghcr.io/tesserix/base-python-runtime-3.13",
  "tag": "weekly",
  "build_args": {
    "ADK_VERSION": { "kind": "github-release", "repo": "tesserix/agent-development-kit" }
  }
}
```

**How far each image floats is set by its name.** Where the name states
a version — `node-runtime-22`, `python-runtime-3.13` — the resolver stays
inside that line and only advances the patch. Where it does not —
`go-builder`, `alpine-runtime`, `nginx-spa` — it advances to the latest
minor as well. Changing that promise means renaming the image, not
loosening the pattern.

The `ARG BASE_IMAGE=` default committed in each Dockerfile is the version
that was latest when it was last touched. It exists so a local
`docker build` is reproducible and so Dependabot still has a literal to
bump; CI always overrides it.

Resolution failing closed is deliberate: if a pattern stops matching,
the build fails and the previous week's image keeps serving, rather than
silently falling back to a stale base. `tools/test_resolve_base.py` runs
as a gate before any image is built, and asserts that every image has a
source, builds `FROM ${BASE_IMAGE}`, and carries a default that its own
pattern still matches.

## Off-cycle bumps

`upstream-drift.yml` runs daily. It resolves every image, rewrites any
`ARG BASE_IMAGE=` default that has fallen behind, and opens a single PR.
Merging it triggers `weekly-rebuild.yml` via the `paths: images/**`
filter, so an off-cycle CVE fix from Node, Alpine, Debian, Python or
nginx lands in `:weekly` + `:latest` the same day instead of waiting for
Saturday.

This used to be Dependabot's job. Dependabot's Docker parser does not
expand `ARG` in a `FROM` line ([dependabot-core#10190][dc10190]) — under
`FROM ${BASE_IMAGE}` it reports the image as no longer a dependency and
closes its own PRs. `.github/dependabot.yml` therefore keeps only the
`github-actions` ecosystem.

[dc10190]: https://github.com/dependabot/dependabot-core/issues/10190

## Consumer pattern

### Go services — distroless-static is the default

`base-go-builder` sets `CGO_ENABLED=0`, so Go binaries come out fully
static. That means **`base-distroless-static` is the right runtime base
for every Go service** — it's smaller, has no shell, no package manager,
and a smaller CVE surface than alpine.

```dockerfile
# Build stage — CGO_ENABLED=0 is baked in
FROM ghcr.io/tesserix/base-go-builder:latest AS build
WORKDIR /src
COPY . .
RUN go build -trimpath -ldflags="-s -w" -o /out/app ./cmd/app

# Runtime — distroless/static:nonroot, ca-certs + tzdata, uid 65532
FROM ghcr.io/tesserix/base-distroless-static:latest
COPY --from=build --chown=10001:10001 /out/app /app
CMD ["/app"]
```

Notes:

- Go's runtime handles `SIGTERM` directly via `signal.Notify`, so the
  `tini` PID-1 wrapper isn't needed — Go binaries are safe as PID 1.
- The image's `USER` is `nonroot` (uid 65532), but K8s
  `securityContext.runAsUser` overrides it. Binaries from `go build`
  are mode `0755`, so any uid can execute them — `--chown=10001:10001`
  is for hygiene, not correctness.
- Multi-binary services (server + migrate + seed) just stack more
  `COPY --from=build` lines in the same runtime stage; one image, one
  pull, K8s `command:` chooses which binary runs.
- Reference migration: see the four mark8ly Go services in
  `tesserix/mark8ly/services/{auth-bff,otto,platform-api,marketplace-api}/Dockerfile`.

### When to use base-alpine-runtime instead

Pick `base-alpine-runtime` only when you genuinely need a shell at
runtime, e.g.:

- The container forks/execs sub-processes (Bash entrypoints, init
  scripts, multi-process supervisors).
- The runtime has to call `apk add` for a glibc-only or musl-only lib
  not already bundled in the binary.
- The healthcheck is `wget` / `curl` rather than a TCP/HTTP probe
  handled by K8s directly.

In every other case, prefer distroless.

### AI agents — always base-python-adk-3.13

Agent services must not start `FROM python:*`, and must never hand-pin a
`tesserix-adk` release URL. The base image already carries the ADK:

```dockerfile
FROM ghcr.io/tesserix/base-python-adk-3.13:20260822
WORKDIR /app
COPY pyproject.toml ./
COPY src ./src
# /opt/adk-venv is on PATH and writable by uid 10001; the ADK is already in it.
RUN pip install --no-cache-dir .
CMD ["uvicorn", "my_agent.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

The installed version is readable at runtime as `TESSERIX_ADK_VERSION`, and
recorded on the image as `org.opencontainers.image.base.name`.

Because the ADK is private and not on PyPI, the wheel is downloaded from its
release assets by `weekly-rebuild.yml` and checked with
`gh attestation verify --signer-workflow` before the build starts. That check
fails closed — a bundle signed by anything other than the ADK's own
`release.yml` is rejected.

Verification uses the provenance bundle attached to the release rather than the
attestations API, because the API is a separate fine-grained PAT permission
while the bundle needs only `contents:read`. Security is unchanged: the bundle
carries a Sigstore signature bound to the release workflow's identity, so
substituting it does not produce a passing verification. A local build of this image therefore needs the wheel fetched
first:

```bash
gh release download v0.51.0 --repo tesserix/agent-development-kit \
  --pattern '*.whl' --dir images/python-adk-3.13/wheels
```

### Other languages

| Language | Runtime base |
|---|---|
| Go (static, default) | `base-distroless-static` |
| Go (cgo / dynamic) | `base-debian-runtime` |
| Node.js (Next.js standalone) | `base-node-runtime-22` or `base-node-runtime-24` |
| Static SPAs (Vite/CRA) | `base-nginx-spa` |
| Python (FastAPI / workers) | `base-python-runtime-3.13` |
| Anything needing a shell | `base-alpine-runtime` |

## Adding a new image

1. `mkdir images/<name>`
2. Add a `Dockerfile` with `ARG BASE_IMAGE=<pinned default>` and
   `FROM ${BASE_IMAGE}` (plus any companion config like `default.conf`).
3. Add `base-source.json` declaring the upstream repo and tag pattern.
4. Add `<name>` to the matrix in `.github/workflows/weekly-rebuild.yml` —
   `build-matrix` for an image built on an upstream base, `build-derived` for
   one built on another tesserix base.
5. Open a PR. CI builds, Trivy-scans, and publishes `sha-*` only. The
   moving tags switch over on the next Saturday rebuild (or manual
   `workflow_dispatch`).

## Opting-in a consumer repo

In the consumer repo, add:

```yaml
# .github/workflows/base-image-refresh.yml
name: Base Image Refresh
on:
  repository_dispatch:
    types: [tesserix-base-images-updated]
  workflow_dispatch:
jobs:
  rebuild:
    runs-on: ubuntu-latest
    steps:
      - env: { GH_TOKEN: ${{ github.token }} }
        run: gh workflow run ci.yml --repo ${{ github.repository }} --ref main
```

Then add the consumer repo's slug to the `consumers` array in
`weekly-rebuild.yml::notify-consumers`.

## Required secrets

| Secret            | Used by                                              |
|-------------------|------------------------------------------------------|
| `TESSERIX_K8S_BOT`| PAT with `repo:write` on every consumer repo (for `repository_dispatch`) |
| `ADK_READ_TOKEN`  | PAT with `contents:read` on `tesserix/agent-development-kit` (resolve, download and verify the ADK wheel) |
| `SMTP_USERNAME`   | `notify-security-failure` job                        |
| `SMTP_PASSWORD`   | `notify-security-failure` job (Gmail app password)   |
