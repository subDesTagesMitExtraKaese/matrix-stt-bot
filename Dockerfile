# build image
FROM debian:bullseye-slim AS builder
WORKDIR /build/
RUN apt-get update && apt-get install --no-install-recommends -y \
    make gcc g++ wget \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Whisper.cpp
ADD whisper.cpp/ /build/
RUN gcc -pthread -O3 -march=native -c ggml.c && \
    g++ -pthread -O3 -std=c++11 -c main.cpp && \
    g++ -pthread -o main ggml.o main.o

# main image
FROM python:3.9-slim-bullseye
WORKDIR /app/

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libolm-dev gcc make wget\
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ADD requirements.txt .

RUN pip install -r requirements.txt && \
  apt-get remove -y gcc make && \
  apt-get autoremove -y

COPY --from=builder /build/main /app/

VOLUME /data/

ADD ./*.py /app/

CMD ["python3", "-u", "main.py"]