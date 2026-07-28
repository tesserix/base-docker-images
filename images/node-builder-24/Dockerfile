# base-node-builder-24 — Node 24 (Krypton LTS) build stage. Mirror of
# base-node-builder-22; downstream consumers pick whichever LTS they
# need. node:24-alpine tracks Krypton, the current active LTS.
FROM node:24-alpine

# brace-expansion step patches CVE-2026-14257 — see base-node-builder-22
# for the full rationale. npm bundles 5.0.7 and no npm release ships
# 5.0.8 yet, so the copy is the fix. Remove once npm bundles >= 5.0.8.
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

WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 24 (Krypton LTS) builder — libc6-compat, corepack, git, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
