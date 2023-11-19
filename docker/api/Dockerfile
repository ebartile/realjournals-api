FROM python:3.11

LABEL maintainer="info@realjournals.com"

ARG APP_ENV
ARG DEBIAN_FRONTEND=noninteractive
ARG HOST_GID

ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

### Install various tools
RUN apt update
RUN apt install -y wget curl build-essential \
       gettext git redis gunicorn supervisor

# install Real Journals dependencies
RUN python -m pip install --upgrade pip
RUN python -m pip install wheel

RUN mkdir -p /var/log/supervisord;
RUN touch /var/log/supervisord/supervisord.log;
RUN touch /var/log/supervisord/celery.log;
RUN touch /var/log/supervisord/celery-error.log;
RUN touch /var/log/supervisord/gunicorn.log;
RUN touch /var/log/supervisord/gunicorn-error.log;
RUN touch /var/log/supervisord/supervisord.log;

RUN mkdir -p /var/run/supervisord;
RUN touch /var/run/supervisord/supervisord.pid;

RUN chmod -R 777 /var/log/supervisor*;
RUN chmod -R 777 /var/run;

COPY scripts/start-container.sh /usr/local/bin/start-container
COPY supervisord.conf /var/supervisord.conf
COPY cron.schedule /var/cron.schedule

RUN chmod u+x /usr/local/bin/start-container
RUN chmod 0644 /var/cron.schedule

COPY scripts/start-container.sh /usr/local/bin/start-container
RUN chmod u+x /usr/local/bin/start-container
RUN groupadd --force -g $HOST_GID realjournals
RUN useradd -mg $HOST_GID realjournals

ENV DJANGO_SETTINGS_MODULE=realjournals.settings

USER $HOST_GID

WORKDIR /var/www/html/

EXPOSE 8080

ENTRYPOINT ["start-container"]
