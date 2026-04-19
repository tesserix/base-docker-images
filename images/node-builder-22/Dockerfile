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
FROM node:25-alpine

RUN apk update \
    && apk add --no-cache \
        libc6-compat \
        git \
        ca-certificates \
    && addgroup -g 10001 -S app \
    && adduser  -u 10001 -S app -G app \
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
