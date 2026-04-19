# base-node-runtime-22 — runtime stage for Next.js standalone bundles
# built with `output: "standalone"`. Paired with base-node-builder-22.
#
# Stripped down vs the builder:
#   * no git
#   * no corepack
#   * libc6-compat retained (sharp/next SWC still need it at runtime)
#   * tini baked for clean SIGTERM → NODE_EXIT propagation
#   * non-root `nextjs` user (uid 10001) — Next.js convention
FROM node:22-alpine

RUN apk update \
    && apk add --no-cache \
        libc6-compat \
        ca-certificates \
        tini \
        tzdata \
    && addgroup -g 10001 -S nextjs \
    && adduser  -u 10001 -S nextjs -G nextjs \
    && rm -rf /var/cache/apk/*

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

USER 10001:10001
WORKDIR /app

# Tini as PID 1. Consumers override CMD with `node apps/<foo>/server.js`.
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "--version"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 22 runtime — libc6-compat, tini, non-root nextjs 10001" \
      org.opencontainers.image.licenses="MIT"
