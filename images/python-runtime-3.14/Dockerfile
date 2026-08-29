# base-python-runtime-3.14 — Python 3.14 runtime for FastAPI / worker
# services. Same contents as the 3.13 line, one minor ahead: the ADK
# develops and releases on 3.14, so agent services can start there
# instead of trailing a minor behind their own SDK.
#
# We stay on slim (not alpine) because most ML / data libraries ship
# glibc wheels; alpine's musl forces source compiles that balloon
# build time and break vendor support.
# Overridden by tools/resolve_base.py in CI; this default is what a local build gets.
ARG BASE_IMAGE=python:3.14.7-slim
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# ca-certificates → TLS to PyPI / GCS / external APIs
# tini            → PID 1 signal handler
# curl            → healthcheck probes without polluting app deps
# tzdata          → zoneinfo for schedulers / timestamp reports
RUN apt-get update \
    && apt-get upgrade -y --no-install-recommends \
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
      org.opencontainers.image.description="Tesserix Python 3.14 runtime — debian slim, tini, curl, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
