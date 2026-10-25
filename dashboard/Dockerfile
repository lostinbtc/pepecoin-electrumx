FROM php:8.2-apache-bookworm

WORKDIR /var/www/html
COPY assets ./assets
COPY views ./views
COPY src ./src
COPY index.php login.html .htaccess LICENSE ./
COPY data/.htaccess data/hoster.json ./data/
RUN chown -R www-data:www-data /var/www/html/data
