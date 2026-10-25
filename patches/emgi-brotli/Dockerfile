# Compatibility patch: keep the exact original combined image and its interfaces.
FROM emgi2/pepecoin-electrum@sha256:b4325c274ce5aed5ecb42719738a1a5d25a07ef1669ad48551bd85cc6dcb284b

# CVE-2026-111497: Debian trixie's security backport, not bookworm's revision.
RUN set -eux; \
    . /etc/os-release; \
    test "$VERSION_CODENAME" = trixie; \
    apt-get update; \
    apt-get install -y --only-upgrade --no-install-recommends libbrotli1; \
    dpkg --compare-versions "$(dpkg-query -W -f='${Version}' libbrotli1)" ge '1.1.0-2+deb13u1'; \
    rm -rf /var/lib/apt/lists/*
