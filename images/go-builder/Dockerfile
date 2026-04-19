# base-go-builder — Go build stage used by every tesserix Go service.
#
# Includes: git (go mod), ca-certificates (module proxy TLS), tzdata (tests
# that load zoneinfo). Nothing else — runtime binaries get cross-compiled
# out of this image into base-alpine-runtime / base-distroless-static, so
# this stage never ships to production.
#
# Non-root user is baked at 10001 so consumers can `USER 10001:10001` in
# their own Dockerfile without adding duplicate adduser commands.
FROM golang:1.26-alpine

# Force each weekly rebuild to pull the freshest apk index — without
# --purge, the layer cache can silently hold month-old package sets.
RUN apk update \
    && apk add --no-cache \
        git \
        ca-certificates \
        tzdata \
    && addgroup -g 10001 -S app \
    && adduser  -u 10001 -S app -G app \
    && rm -rf /var/cache/apk/*

# Sensible Go defaults for every downstream build: smaller caches, no
# interactive prompts, deterministic output (-trimpath baked into the
# typical `go build` we run downstream).
ENV CGO_ENABLED=0 \
    GOOS=linux \
    GOFLAGS="-buildvcs=false"

USER 10001:10001
WORKDIR /workspace

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Go builder base (alpine + git + tzdata + non-root 10001)" \
      org.opencontainers.image.licenses="MIT"
