# build image
FROM ubuntu:24.04 AS builder
WORKDIR /app/
RUN apt-get update \
 && apt-get install -y \
    build-essential wget cmake git \
    libvulkan-dev glslc \
    libavcodec-dev libavformat-dev libavutil-dev \
    libolm-dev gcc g++ make libffi-dev \
    libopenblas-dev \
    python3 python3-pip python3-venv \
 && rm -rf /var/lib/apt/lists/*

# Install Whisper.cpp
COPY whisper.cpp/ .
RUN cmake -B build -DGGML_BLAS=1 -DGGML_VULKAN=1 -D WHISPER_FFMPEG=yes && \
    cmake --build build --config Release

# Set Python path
ENV PATH="/usr/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# main image
FROM ubuntu:24.04
WORKDIR /app/

RUN apt-get update && apt-get install -y \
    wget libopenblas0 libvulkan1 libavcodec60 libavformat60 libavutil58 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy Python venv and set up environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /app/build/bin/whisper-cli /app/
COPY --from=builder /app/build/src/libwhisper* /app/
COPY --from=builder /app/build/ggml/src/libggml* /app/
COPY --from=builder /app/build/ggml/src/ggml-*/libggml* /app/
     
RUN ./whisper-cli --help > /dev/null

VOLUME /data/

COPY ./*.py /app/
COPY ./whisper.cpp/models/download-ggml-model.sh /app/

CMD ["python3", "-u", "main.py"]