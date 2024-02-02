FROM elestio/metatrader5:latest

LABEL maintainer="info@realjournals.com"

USER root

ENV HOME /home/kasm-user
WORKDIR $HOME
RUN chown -R root:root $HOME

ARG APP_ENV
ARG DEBIAN_FRONTEND=noninteractive
ARG HOST_GID

ENV TZ=UTC
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONFAULTHANDLER=1

### Install various tools
RUN add-apt-repository ppa:deadsnakes/ppa
RUN apt update
RUN apt install -y wget curl build-essential \
       gettext git redis gunicorn supervisor winbind python3.9

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 2
RUN update-alternatives --config python3

COPY ./scripts/install_tools.sh /dockerstartup/install/
RUN bash /dockerstartup/install/install_tools.sh

RUN wine /dockerstartup/python.exe -m pip install --upgrade pip
RUN wine /dockerstartup/python.exe -m pip install wheel MetaTrader5 rpyc

RUN curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
RUN python3 get-pip.py
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install setuptools wheel mt5linux

COPY scripts/vnc_startup.sh /usr/local/bin/vnc_startup
RUN chmod u+x /usr/local/bin/vnc_startup

EXPOSE 18812

ENTRYPOINT ["vnc_startup"]
