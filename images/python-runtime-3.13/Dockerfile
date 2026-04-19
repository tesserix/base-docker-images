# base-python-runtime-3.13 — Python 3.13 runtime for FastAPI / worker
# services. Replaces the stock-analysis + devai + social-media-scrapper
# "FROM python:3.12-slim && apt-get install tini curl ca-certificates"
# stanzas.
#
# We stay on slim (not alpine) because most ML / data libraries ship
# glibc wheels; alpine's musl forces source compiles that balloon
# build time and break vendor support.
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ca-certificates → TLS to PyPI / GCS / external APIs
# tini            → PID 1 signal handler
# curl            → healthcheck probes without polluting app deps
# tzdata          → zoneinfo for schedulers / timestamp reports
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        ca-certificates \
        tini \
        curl \
        tzdata \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/cache/apt/* \
    && groupadd --system --gid 10001 app \
    && useradd  --system --uid 10001 --gid 10001 --home-dir /home/app --create-home app

USER 10001:10001
WORKDIR /home/app

# Tini propagates SIGTERM to the python process so K8s graceful-
# shutdown actually fires the uvicorn / celery handlers.
ENTRYPOINT ["/usr/bin/tini", "--"]
CMD ["python", "--version"]

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Python 3.13 runtime — debian slim, tini, curl, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
