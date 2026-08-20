# base-python-adk-3.13 — the Tesserix ADK, pre-installed, on the hardened
# Python runtime. Every AI agent service starts here instead of from
# python:*, so no agent repo hand-pins an ADK release URL again.
#
# Built after base-python-runtime-3.13 in the same weekly run, so it never
# inherits last week's patched runtime.
ARG BASE_IMAGE=ghcr.io/tesserix/base-python-runtime-3.13:weekly
FROM ${BASE_IMAGE}

# Resolved from the latest tesserix/agent-development-kit release by
# tools/resolve_base.py. The matching wheel is downloaded and checked against
# its build provenance by the workflow before it reaches this context.
ARG ADK_VERSION

USER root
COPY wheels/ /tmp/wheels/

# Pinned to ADK_VERSION so the resolved argument and the wheel actually in the
# context cannot silently disagree. Extras are installed in full: an agent that
# needs Temporal or pgvector should not need a different base image.
RUN python -m venv /opt/adk-venv \
    && /opt/adk-venv/bin/pip install --no-cache-dir --upgrade pip \
    && /opt/adk-venv/bin/pip install --no-cache-dir --find-links /tmp/wheels \
        "tesserix-adk[all]==${ADK_VERSION#v}" \
    && rm -rf /tmp/wheels \
    && chown -R 10001:10001 /opt/adk-venv

USER 10001:10001

# Consumers install their own dependencies into this same venv, which is why it
# is writable by the runtime uid.
ENV VIRTUAL_ENV=/opt/adk-venv \
    PATH=/opt/adk-venv/bin:$PATH \
    TESSERIX_ADK_VERSION=${ADK_VERSION}

LABEL org.opencontainers.image.source="https://github.com/tesserix/base-docker-images" \
      org.opencontainers.image.description="Tesserix Python 3.13 runtime with the ADK pre-installed — non-root 10001" \
      org.opencontainers.image.licenses="MIT"
