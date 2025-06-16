# build image
FROM ubuntu:24.04 AS builder
WORKDIR /app/

RUN apt-get update \
 && apt-get install -y \
    build-essential wget cmake git

# Install Whisper.cpp
ADD whisper.cpp/ .
RUN cmake -B build && cmake --build build --config Release

FROM python:3.13-slim-bookworm AS py-builder
WORKDIR /app/

RUN apt-get update \
 && apt-get install -y \
    build-essential wget cmake git \
    libolm-dev gcc g++ make libffi-dev

# Install dependencies
ADD requirements.txt .
RUN pip install --prefix="/python-libs" --no-warn-script-location -r requirements.txt

# main image
FROM python:3.13-slim-bookworm
WORKDIR /app/

RUN apt-get update && apt-get install -y \
ffmpeg wget \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

COPY --from=py-builder /python-libs /usr/local
COPY --from=py-builder /usr/local/lib/libolm* /usr/local/lib/
COPY --from=builder /app/build/bin/whisper-cli /app/build/src/libwhisper* /app/build/ggml/src/libggml* /app/

RUN ./whisper-cli --help > /dev/null

VOLUME /data/

ADD ./*.py /app/
ADD ./whisper.cpp/models/download-ggml-model.sh /app/

CMD ["python3", "-u", "main.py"]