FROM python:3.11

ENV PYTHONIOENCODING utf-8

WORKDIR /app

RUN apt-get update && apt-get install libgl1 -y

RUN pip install selenium openai scikit-image