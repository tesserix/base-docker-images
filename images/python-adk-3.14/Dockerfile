# base-python-adk-3.14 — the Tesserix ADK, pre-installed, on the hardened
# Python 3.14 runtime. The ADK develops and releases on CPython 3.14, so
# this is the line new agent services should start from; the 3.13 image
# stays for services that have not moved yet.
#
# Built from base-python-runtime-3.14 in the same weekly run, so it never
# inherits last week's patched runtime.
ARG BASE_IMAGE=ghcr.io/tesserix/base-python-runtime-3.14:weekly
FROM ${BASE_IMAGE}

# Resolved to the latest tesserix/agent-development-kit release by
# tools/resolve_base.py. The matching wheel is downloaded and its
# provenance checked by the build workflow before it reaches this context.
ARG ADK_VERSION

USER root
COPY wheels/ /tmp/wheels/

# Pinned to the resolved ADK_VERSION so the argument and the wheel actually
# in context cannot silently disagree. Extras installed in full: an agent
# needing Temporal or pgvector should not need a different base image.
RUN python -m venv /opt/adk-venv \
    && /opt/adk-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/adk-venv/bin/pip install --no-cache-dir --find-links /tmp/wheels \
        "tesserix-adk[all]==${ADK_VERSION#v}" \
    && rm -rf /tmp/wheels \
    && chown -R 10001:10001 /opt/adk-venv

USER 10001:10001

# Consumers install their own dependencies into the same venv, which is why
# it is writable by the runtime uid.
ENV VIRTUAL_ENV=/opt/adk-venv \
    PATH=/opt/adk-venv/bin:$PATH \
    TESSERIX_ADK_VERSION=${ADK_VERSION}

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Python 3.14 with the ADK pre-installed, non-root 10001" \
      org.opencontainers.image.licenses="MIT"
