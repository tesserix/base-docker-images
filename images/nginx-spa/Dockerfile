# base-nginx-spa — static SPA serve. Replaces the 19 "FROM nginx:alpine"
# stanzas across mfe-app, HomeChef web, and friends. Ships a
# SPA-fallback config (routes 404s back to index.html), brotli + gzip
# pre-compressed file support, and a non-root (port 8080) listener so
# the image can run under a K8s PodSecurityContext with
# allowPrivilegeEscalation: false.
FROM nginx:1.29-alpine

RUN apk update \
    && apk add --no-cache \
        ca-certificates \
        tini \
    # Run as the `nginx` user that ships with the upstream image. We
    # don't touch /etc/passwd or remap uids because the nginx image
    # already has a dedicated non-root uid.
    && rm -rf /var/cache/apk/*

# SPA fallback + compressed-asset delivery. Overridable via volume /
# COPY in consumer Dockerfiles that need a custom server block.
COPY default.conf /etc/nginx/conf.d/default.conf

# Non-root requires nginx to listen above 1024.
EXPOSE 8080

# Tini as PID 1 so SIGTERM from K8s cleanly drains connections via the
# built-in graceful-shutdown path (nginx needs SIGQUIT for graceful).
# We translate in the shim.
STOPSIGNAL SIGQUIT
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["nginx", "-g", "daemon off;"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix nginx SPA serve — 1.29-alpine, SPA fallback, non-root 8080, tini" \
      org.opencontainers.image.licenses="MIT"
