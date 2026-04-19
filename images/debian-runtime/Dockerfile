# base-debian-runtime — Debian 13 (trixie) slim runtime. Replaces the
# 20 FanZone "FROM debian:bookworm-slim && apt-get install -y
# ca-certificates tzdata tini" stanzas. Debian 13 went stable in 2025
# and brings the glibc / openssl patches that close the main
# upstream HIGH CVEs.
#
# Use this instead of base-alpine-runtime when:
#   * the binary dynamically links glibc
#   * vendor SDKs only publish glibc wheels (e.g. Stripe Go SDK does
#     link net/http → glibc via cgo when CGO_ENABLED=1)
#   * you need apt packages for op-time tools
FROM debian:trixie-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        tini \
        tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    && groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid 10001 --home-dir /home/app --create-home app

USER 10001:10001
WORKDIR /home/app

ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["/bin/bash"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Debian 13 (trixie) slim runtime — tini, ca-certs, tzdata, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
