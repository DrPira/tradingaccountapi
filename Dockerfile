FROM alpine:3.12

MAINTAINER Erik Pira "erik.pira@gmail.com"

RUN apk add --no-cache python3 py3-pip python3-dev build-base

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

WORKDIR /app/App

ENV PYTHONIOENCODING=utf-8

CMD ["gunicorn", "--config", "gunicorn.cfg", "--log-level", "info", "--pid", "pidfile",  "app:app"]
