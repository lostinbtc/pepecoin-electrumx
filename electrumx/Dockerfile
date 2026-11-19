ARG PYTHON_BASE_IMAGE=python:3.13.18-slim-trixie@sha256:e48f59cdba69a3cbd9ed2cf0f348d90d45a8d350d98134cf1070bc106ee9ed90
FROM ${PYTHON_BASE_IMAGE} AS builder

ENV HOME=/data ALLOW_ROOT=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential ca-certificates libleveldb-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/electrumx
COPY LICENCE README.md MANIFEST.in pyproject.toml entrypoint.sh requirements-runtime.txt ./
COPY src ./src
RUN chmod +x entrypoint.sh && \
    python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir --no-build-isolation -c requirements-runtime.txt '.[uvloop]'

# Build tools and their headers are not part of the shipped runtime.
FROM ${PYTHON_BASE_IMAGE} AS runtime
ENV HOME=/data ALLOW_ROOT=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends ca-certificates libleveldb1d && \
    rm -rf /var/lib/apt/lists/* && \
    python -m pip uninstall -y pip
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /opt/electrumx/entrypoint.sh /opt/electrumx/entrypoint.sh
COPY LICENCE /usr/share/doc/electrumx/LICENCE
# pip bundles its own libraries; neither pip nor setuptools/wheel are needed to serve.
RUN python -m pip uninstall -y pip setuptools wheel packaging && \
    python -c 'import electrumx, plyvel, aiohttp, aiorpcx, uvloop, websockets'

WORKDIR /data
ENTRYPOINT ["/opt/electrumx/entrypoint.sh"]
