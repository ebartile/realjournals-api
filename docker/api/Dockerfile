FROM python:3.9

LABEL maintainer="info@realjournals.com"

ARG APP_ENV
ARG DEBIAN_FRONTEND=noninteractive
ARG HOST_GID

ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

### Install various tools
RUN apt update
RUN apt install -y wget curl build-essential \
       gettext git redis gunicorn supervisor

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install setuptools wheel mt5linux

RUN mkdir -p /var/www/html/log;
RUN mkdir -p /var/www/html/log/supervisord;
RUN touch /var/www/html/log/supervisord/supervisord.log;
RUN touch /var/www/html/log/supervisord/celery.log;
RUN touch /var/www/html/log/supervisord/celery-error.log;
RUN touch /var/www/html/log/supervisord/gunicorn.log;
RUN touch /var/www/html/log/supervisord/gunicorn-error.log;
RUN touch /var/www/html/log/supervisord/supervisord.log;

RUN mkdir -p /var/run/supervisord;
RUN touch /var/run/supervisord/supervisord.pid;

RUN chmod -R 777 /var/www/html/log/supervisor*;
RUN chmod -R 777 /var/run;

COPY scripts/start-container.sh /usr/local/bin/start-container
COPY supervisord.conf /var/supervisord.conf
COPY cron.schedule /var/cron.schedule

RUN chmod u+x /usr/local/bin/start-container
RUN chmod 0644 /var/cron.schedule

RUN groupadd --force -g $HOST_GID realjournals
RUN useradd -mg $HOST_GID realjournals

ENV DJANGO_SETTINGS_MODULE=realjournals.settings

WORKDIR /var/www/html

EXPOSE 8000

ENTRYPOINT ["start-container"]
