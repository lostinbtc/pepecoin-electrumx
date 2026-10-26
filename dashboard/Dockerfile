# Optional dashboard only; the ElectrumX daemon image is unchanged.
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a

# Use maintained distribution packages, not locally compiled replacement libraries.
# Minimum revisions retain the reviewed PHP/Brotli/XML/zlib fixes on rebuilds.
RUN set -eux; \
    apk upgrade --no-cache; \
    apk add --no-cache 'apache2>=2.4.69-r0' 'php84>=8.4.27-r0' \
        php84-apache2 php84-session php84-ctype php84-openssl php84-curl \
        'brotli-libs>=1.2.1-r0' 'libxml2>=2.13.9-r2' 'zlib>=1.3.2-r1'; \
    addgroup -g 33 dashboard; \
    adduser -D -H -u 33 -G dashboard dashboard; \
    mkdir -p /run/apache2 /var/www/html/data; \
    php84 -r 'exit(PHP_MAJOR_VERSION === 8 && PHP_MINOR_VERSION === 4 && version_compare(PHP_VERSION, "8.4.27", ">=") ? 0 : 1);'

WORKDIR /var/www/html
COPY httpd.conf /etc/apache2/httpd.conf
COPY php-security.ini /etc/php84/conf.d/99-dashboard.ini
COPY assets ./assets
COPY views ./views
COPY src ./src
COPY index.php login.html .htaccess LICENSE ./
COPY data/.htaccess data/hoster.json ./data/
RUN chown -R 33:33 /var/www/html/data && httpd -t
EXPOSE 80
STOPSIGNAL SIGWINCH
CMD ["httpd", "-D", "FOREGROUND"]
