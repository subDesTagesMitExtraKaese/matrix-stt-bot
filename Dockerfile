# build image
FROM ubuntu:22.04 AS builder
WORKDIR /app/

RUN apt-get update && \
  apt-get install -y build-essential wget cmake git \
  && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Install Whisper.cpp
ADD whisper.cpp/ /app/
RUN cmake -B build && cmake --build build --config Release

# main image
FROM python:3.12-slim-bullseye
WORKDIR /app/

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libolm-dev gcc make wget\
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

ADD requirements.txt .

RUN pip install -r requirements.txt && \
  apt-get remove -y gcc make && \
  apt-get autoremove -y

COPY --from=builder /app/build/bin/whisper-cli /app/

VOLUME /data/

ADD ./*.py /app/
ADD ./whisper.cpp/models/download-ggml-model.sh /app/

ARG PRELOAD_MODEL
ENV PRELOAD_MODEL ${PRELOAD_MODEL}
RUN if [ -n "$PRELOAD_MODEL" ]; then /app/download-ggml-model.sh "$PRELOAD_MODEL" "/app"; fi

CMD ["python3", "-u", "main.py"]