FROM python:3.9-alpine3.18

ENV PYTHONUNBUFFERED=1

RUN mkdir /bot

WORKDIR /bot

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD ["python", "-m", "bot.main"]