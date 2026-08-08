# build image
FROM debian:13-slim AS builder
WORKDIR /app/
RUN apt-get update \
 && apt-get install -y \
    build-essential wget cmake git \
    pkg-config glslc spirv-headers \
    libvulkan-dev \
    libavcodec-dev libavformat-dev libavutil-dev libswresample-dev \
    libopenblas-dev \
    python3 python3-pip python3-venv \
 && rm -rf /var/lib/apt/lists/*

# Install Whisper.cpp
COPY whisper.cpp/ .
RUN cmake -B build -DGGML_BLAS=ON -DGGML_BLAS_VENDOR=OpenBLAS -DGGML_VULKAN=ON -DWHISPER_COMMON_FFMPEG=ON && \
    cmake --build build --config Release

# Install Python dependencies
COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# main image
FROM debian:13-slim
WORKDIR /app/

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget libopenblas0 libgomp1 libvulkan1 \
    libavcodec61 libavformat61 libavutil59 libswresample5 \
    ca-certificates python3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy Python venv and built binaries
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/build/bin/whisper-cli .
COPY --from=builder /app/build/bin/libwhisper.so* .
COPY --from=builder /app/build/bin/libggml*.so* .
COPY --from=builder /app/build/bin/libparakeet.so* .

ENV PATH="/opt/venv/bin:$PATH"
     
RUN ./whisper-cli --help > /dev/null

VOLUME /data/

COPY ./*.py /app/
COPY ./whisper.cpp/models/download-ggml-model.sh /app/

CMD ["python3", "-u", "main.py"]
