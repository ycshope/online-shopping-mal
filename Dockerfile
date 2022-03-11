# syntax=docker/dockerfile:1
FROM python:3.9
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code

COPY requirements.txt /code/
COPY deploy.py /code/

RUN apt-get update && apt-get install vim -y \
    && pip install --upgrade pip && pip3 install -r requirements.txt

# RUN python deploy.py
COPY . /code/