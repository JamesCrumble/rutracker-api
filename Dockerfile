FROM python:3.13-slim-bullseye as build
WORKDIR /build

COPY requirements.txt /build/requirements.txt

RUN apt-get update && \
    apt-get clean

RUN pip install --upgrade pip
RUN pip install -Ur requirements.txt


FROM build

WORKDIR /python-api
COPY . /python-api

CMD ["python", "main.py"]