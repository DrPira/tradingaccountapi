FROM ubuntu:22.04

MAINTAINER Erik Pira "erik.pira@gmail.com"

RUN apt update --allow-unauthenticated

# RUN apt install -y libblas-dev liblapack-dev gfortran python3-pip

RUN apt install -y python3-pip

COPY requirements.txt /app/requirements.txt

WORKDIR /app

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . /app

WORKDIR /app/App

ENV PYTHONIOENCODING=utf-8

CMD ["gunicorn", "--config", "gunicorn.cfg", "--log-level", "info", "--pid", "pidfile",  "app:app"]
