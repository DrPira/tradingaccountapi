FROM python:3.10-alpine3.17

MAINTAINER Erik Pira "erik.pira@gmail.com"

# RUN apk add --no-cache py3-pip

# RUN apt install -y libblas-dev liblapack-dev gfortran python3-pip

# RUN apt install -y python3-pip

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

COPY . /app

WORKDIR /app/App

ENV PYTHONIOENCODING=utf-8

CMD ["gunicorn", "--config", "gunicorn.cfg", "--log-level", "info", "--pid", "pidfile",  "app:app"]
