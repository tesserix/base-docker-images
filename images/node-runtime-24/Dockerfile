# base-node-runtime-24 — Node 24 runtime stage. Mirror of
# base-node-runtime-22 for Krypton-based apps.
# Overridden by tools/resolve_base.py in CI; this default is what a local build gets.
ARG BASE_IMAGE=node:24.19.0-alpine3.24
FROM ${BASE_IMAGE}

# brace-expansion (CVE-2026-69152) and ip-address (CVE-2026-69192) are
# patched in place over npm's bundled copies — see base-node-builder-22
# for the rationale. Remove once npm bundles the fixed versions.
RUN apk update \
    && apk upgrade --no-cache \
    && apk add --no-cache \
        libc6-compat \
        ca-certificates \
        tini \
        tzdata \
    && npm install -g npm@11 corepack@latest \
    && npm install -g --prefix /tmp/patched \
        brace-expansion@5.0.9 \
        ip-address@10.3.1 \
    && for p in brace-expansion ip-address; do \
         cp -R /tmp/patched/lib/node_modules/$p/. \
               /usr/local/lib/node_modules/npm/node_modules/$p/; \
       done \
    && rm -rf /tmp/patched \
    && addgroup -g 10001 -S nextjs \
    && adduser  -u 10001 -S nextjs -G nextjs \
    && rm -rf /var/cache/apk/*

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

USER 10001:10001
WORKDIR /app

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "--version"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 24 runtime — libc6-compat, tini, non-root nextjs 10001" \
      org.opencontainers.image.licenses="MIT"
