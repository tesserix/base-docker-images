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

The minimal consumer Dockerfile looks like:

```dockerfile
# Build stage
FROM ghcr.io/tesserix/base-go-builder:latest AS build
WORKDIR /src
COPY . .
RUN go build -ldflags="-s -w" -o /out/app ./cmd/app

# Runtime
FROM ghcr.io/tesserix/base-alpine-runtime:latest
COPY --from=build /out/app /app
CMD ["/app"]
```

No `apk add`, no `adduser`, no `USER` — all of that is baked. If the
consumer needs extra packages (e.g. a CA bundle, a glibc-only lib), it
adds them on top in its own stage.

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
