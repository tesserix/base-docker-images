# base-node-builder-22 — build stage for Next.js / Turborepo monorepos
# pinned to Node 22 (Jod LTS). Used by mark8ly, tesserix-blog,
# tesserix-home, HomeChef portals, most of mfe-app.
#
# Includes:
#   * libc6-compat — required by Next.js's SWC binary on Alpine
#   * corepack enabled — npm / pnpm / yarn without extra hoops
#   * git — many monorepos use it for workspace resolution + build-time
#     `git rev-parse` calls to bake a build id
#   * non-root build user baked at 10001 so `USER 10001:10001` works
#     out of the box and npm doesn't complain about running as root
FROM node:22-alpine

# The brace-expansion step patches CVE-2026-14257 (DoS via unbounded
# expansion). npm bundles brace-expansion 5.0.7; both npm 11.18.0 and
# 12.0.1 still ship 5.0.7, so upgrading npm does NOT clear the finding —
# this is why the 2026-07-25 weekly rebuild failed its Trivy gate. npm
# carries exactly one copy of the package and 5.0.7/5.0.8 have identical
# file layouts, so dropping 5.0.8 over it is a safe in-place fix.
# Remove this once npm bundles >= 5.0.8.
RUN apk update \
    && apk upgrade --no-cache \
    && apk add --no-cache \
        libc6-compat \
        git \
        ca-certificates \
    && addgroup -g 10001 -S app \
    && adduser  -u 10001 -S app -G app \
    && npm install -g npm@11 corepack@latest \
    && npm install -g --prefix /tmp/be brace-expansion@5.0.8 \
    && cp -R /tmp/be/lib/node_modules/brace-expansion/. \
             /usr/local/lib/node_modules/npm/node_modules/brace-expansion/ \
    && rm -rf /tmp/be \
    && corepack enable \
    && rm -rf /var/cache/apk/*

# Build stage: still root here because consumer Dockerfiles often need
# to write into /app; switch to 10001 explicitly in the runtime stage.
WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 22 (Jod LTS) builder — libc6-compat, corepack, git, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
