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
  is built with `docker build --pull` so upstream alpine / debian /
  node index refreshes are picked up.
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

## Dependabot

`.github/dependabot.yml` scans every image's `FROM` line weekly. If
Node, Alpine, Debian, Python, or nginx publishes an off-cycle CVE fix,
Dependabot raises a PR same-day. Merging that PR triggers
`weekly-rebuild.yml` via the `paths: images/**` filter, so the new
upstream lands in `:weekly` + `:latest` within minutes instead of
waiting for Saturday.

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
2. Add a `Dockerfile` (and any companion config like `default.conf`).
3. Add `<name>` to the matrix in `.github/workflows/weekly-rebuild.yml`.
4. Add a `dependabot.yml` entry for the new directory.
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
| `SMTP_USERNAME`   | `notify-security-failure` job                        |
| `SMTP_PASSWORD`   | `notify-security-failure` job (Gmail app password)   |
