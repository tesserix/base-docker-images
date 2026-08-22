# base-node-builder-24 — Node 24 (Krypton LTS) build stage. Mirror of
# base-node-builder-22; downstream consumers pick whichever LTS they
# need. node:24-alpine tracks Krypton, the current active LTS.
# Overridden by tools/resolve_base.py in CI; this default is what a local build gets.
ARG BASE_IMAGE=node:24.19.0-alpine3.24
FROM ${BASE_IMAGE}

# Vulnerable brace-expansion, ip-address, and tar releases are patched in
# place over npm's bundled copies — see base-node-builder-22 for the
# rationale and removal versions.
RUN apk update \
    && apk upgrade --no-cache \
    && apk add --no-cache \
        libc6-compat \
        git \
        ca-certificates \
    && addgroup -g 10001 -S app \
    && adduser  -u 10001 -S app -G app \
    && npm install -g npm@11 corepack@latest \
    && npm install -g --prefix /tmp/patched \
        brace-expansion@5.0.9 \
        ip-address@10.3.1 \
        tar@7.5.21 \
    && for p in brace-expansion ip-address tar; do \
         cp -R /tmp/patched/lib/node_modules/$p/. \
               /usr/local/lib/node_modules/npm/node_modules/$p/; \
       done \
    && rm -rf /tmp/patched \
    && corepack enable \
    && rm -rf /var/cache/apk/*

WORKDIR /workspace
ENV NEXT_TELEMETRY_DISABLED=1 \
    NPM_CONFIG_UPDATE_NOTIFIER=false \
    NPM_CONFIG_FUND=false

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 24 (Krypton LTS) builder — libc6-compat, corepack, git, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
