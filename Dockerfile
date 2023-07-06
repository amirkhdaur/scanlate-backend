FROM python:latest

RUN mkdir /usr/src/app/
WORKDIR /usr/src/app/

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . .