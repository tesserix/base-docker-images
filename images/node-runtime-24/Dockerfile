# base-node-runtime-24 — Node 24 runtime stage. Mirror of
# base-node-runtime-22 for Krypton-based apps.
FROM node:24-alpine

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

ENTRYPOINT ["/sbin/tini", "--"]
CMD ["node", "--version"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Node 24 runtime — libc6-compat, tini, non-root nextjs 10001" \
      org.opencontainers.image.licenses="MIT"
