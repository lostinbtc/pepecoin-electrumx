FROM python:3.13-slim-trixie

ENV HOME=/data ALLOW_ROOT=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential ca-certificates libleveldb-dev && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /opt/electrumx
COPY LICENCE README.md MANIFEST.in pyproject.toml entrypoint.sh ./
COPY src ./src
RUN chmod +x entrypoint.sh && \
    python -m pip install --no-cache-dir --upgrade pip setuptools wheel && \
    python -m pip install --no-cache-dir --no-build-isolation '.[uvloop]'

WORKDIR /data
ENTRYPOINT ["/opt/electrumx/entrypoint.sh"]
