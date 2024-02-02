FROM nginx

RUN set -eux; \
    savedAptMark="$(apt-mark showmanual)"; \
    apt-get update; \
    # install system dependencies
    apt-get install -y \
       telnet

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d /etc/nginx/conf.d
COPY templates /etc/nginx/templates

RUN mkdir -p /var/www/html/log/nginx;
RUN touch /var/www/html/log/nginx/error.log
RUN touch /var/www/html/log/nginx/access.log
RUN chown nginx:nginx /var/www/html/log/nginx/error.log
RUN chown nginx:nginx /var/www/html/log/nginx/access.log

EXPOSE 80
EXPOSE 443