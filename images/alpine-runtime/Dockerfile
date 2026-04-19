# base-alpine-runtime — minimal runtime for statically-linked Go / Rust
# binaries. Designed to replace the 40+ "FROM alpine:3.19 && apk add
# ca-certificates && addgroup && adduser" stanzas that are scattered
# across tesserix Go service Dockerfiles.
#
# Ships:
#   * ca-certificates — required for TLS calls to *.googleapis.com etc.
#   * tini            — PID 1 signal handler. K8s delivers SIGTERM on
#                       shutdown; without a proper init, Go binaries miss
#                       the zombie-reap + SIGINT propagation for their
#                       child goroutines.
#   * tzdata          — every reporting / cron service in our fleet
#                       needs IANA zones at runtime.
#   * non-root user (uid 10001 gid 10001)
FROM alpine:3.23

RUN apk update \
    && apk add --no-cache \
        ca-certificates \
        tini \
        tzdata \
    && addgroup -g 10001 -S app \
    && adduser  -u 10001 -S app -G app \
    && rm -rf /var/cache/apk/*

USER 10001:10001
WORKDIR /home/app

# Tini as PID 1. Consumers override CMD with their binary path.
ENTRYPOINT ["/sbin/tini", "--"]
CMD ["/bin/sh"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Alpine 3.23 runtime — ca-certs, tini, tzdata, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
