FROM python:3.9-alpine3.18

ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get -y install \
    build-essential libpcre3 libpcre3-dev zlib1g zlib1g-dev libssl-dev wget && apt install -y wkhtmltopdf

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .