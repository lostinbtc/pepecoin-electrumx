# PHP fixes CVE-2026-109618 and CVE-2026-109619. Overrides must pass the guard.
ARG PHP_BASE_IMAGE=php:8.2.35-apache-bookworm@sha256:5714c8607608e50d880a5f222fab556edecd4a11b9c50c81fce1c7932c1cf604
FROM ${PHP_BASE_IMAGE}

# Debian backports CVE-2026-111497; the full package revision is authoritative.
RUN set -eux; \
    . /etc/os-release; \
    test "$VERSION_CODENAME" = bookworm; \
    apt-get update; \
    apt-get upgrade -y; \
    apt-get install -y --no-install-recommends libbrotli1; \
    apt-get purge -y --auto-remove $PHPIZE_DEPS libc6-dev linux-libc-dev; \
    dpkg --compare-versions "$(dpkg-query -W -f='${Version}' libbrotli1)" ge '1.0.9-2+deb12u1'; \
    php -r 'exit(PHP_MAJOR_VERSION === 8 && PHP_MINOR_VERSION === 2 && version_compare(PHP_VERSION, "8.2.35", ">=") ? 0 : 1);'; \
    rm -rf /var/lib/apt/lists/*

WORKDIR /var/www/html
COPY assets ./assets
COPY views ./views
COPY src ./src
COPY index.php login.html .htaccess LICENSE ./
COPY data/.htaccess data/hoster.json ./data/
RUN chown -R www-data:www-data /var/www/html/data
