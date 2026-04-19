# base-distroless-static — thin passthrough of gcr.io/distroless/static:nonroot.
#
# Why re-publish under the tesserix namespace? One registry, one ignorable
# ignore-list, one pull-through cache. Consumer Dockerfiles just say:
#
#   FROM ghcr.io/tesserix/base-distroless-static:latest
#
# …and we own when the weekly rebuild swings to a freshly-patched upstream
# digest. Nothing is added on top — distroless/static already ships
# ca-certificates, tzdata, /etc/passwd with a `nonroot` user (uid 65532),
# and no shell.
FROM gcr.io/distroless/static:nonroot

# No RUN possible (no shell). Labels are the only mutation.
LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix distroless-static passthrough (upstream gcr.io/distroless/static:nonroot)" \
      org.opencontainers.image.licenses="Apache-2.0"
