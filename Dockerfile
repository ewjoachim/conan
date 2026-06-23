FROM php:8.2-apache

# Activer mod_rewrite + extension SQLite
RUN a2enmod rewrite \
    && docker-php-ext-install pdo_sqlite

# Autoriser .htaccess
RUN sed -i 's/AllowOverride None/AllowOverride All/g' /etc/apache2/apache2.conf

COPY . /var/www/html/

# Le dossier data/ sera monté depuis l'hôte (volume)
RUN mkdir -p /var/www/html/data \
    && chown -R www-data:www-data /var/www/html \
    && chmod -R 755 /var/www/html \
    && chmod -R 775 /var/www/html/data

EXPOSE 80
