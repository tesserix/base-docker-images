# base-node-builder-24 — Node 24 (Krypton LTS) build stage. Mirror of
# base-node-builder-22; downstream consumers pick whichever LTS they
# need. node:24-alpine tracks Krypton, the current active LTS.
FROM node:24-alpine

RUN apk update \
    && apk add --no-cache \
        libc6-compat \
        git \
        ca-certificates \
    && addgroup -g 10001 -S app \
    && adduser  -u 10001 -S app -G app \
    && corepack enable \
    && rm -rf /var/cache/apk/*

WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 24 (Krypton LTS) builder — libc6-compat, corepack, git, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
