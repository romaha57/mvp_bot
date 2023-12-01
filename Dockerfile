FROM python:3.9-alpine3.18

ENV PYTHONUNBUFFERED=1

RUN sudo apt install -y wkhtmltopdf

RUN mkdir /app

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .