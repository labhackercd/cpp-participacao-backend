FROM python:3.6-alpine
ENV PYTHONUNBUFFERED 1

RUN apk update && apk add postgresql-dev gcc python3-dev musl-dev
RUN apk add --no-cache bash

RUN mkdir -p /var/labhacker/participacao_backend

WORKDIR /var/labhacker/participacao_backend
COPY requirements.txt /var/labhacker/participacao_backend/
RUN pip install -r requirements.txt
COPY . /var/labhacker/participacao_backend/

RUN chmod 755 start_web.sh
RUN chmod 755 start_celery_beat.sh