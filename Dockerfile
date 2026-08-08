# build image
FROM debian:trixie AS builder
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

# Set Python path
ENV PATH="/usr/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# main image
FROM debian:trixie
WORKDIR /app/

RUN apt-get update && apt-get install -y --no-install-recommends \
    wget libopenblas0 libgomp1 libvulkan1 libavcodec-dev libavformat-dev libavutil-dev libswresample-dev ca-certificates python3 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* /var/cache/apt/archives/*

# Copy Python venv and set up environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --from=builder /app/build/bin/whisper-cli /app/
COPY --from=builder /app/build/bin/libwhisper.so* /app/
COPY --from=builder /app/build/bin/libggml.so* /app/
COPY --from=builder /app/build/bin/libggml-base.so* /app/
COPY --from=builder /app/build/bin/libggml-cpu.so* /app/
COPY --from=builder /app/build/bin/libggml-blas.so* /app/
COPY --from=builder /app/build/bin/libggml-vulkan.so* /app/
COPY --from=builder /app/build/bin/libparakeet.so* /app/
     
RUN ./whisper-cli --help > /dev/null

VOLUME /data/

COPY ./*.py /app/
COPY ./whisper.cpp/models/download-ggml-model.sh /app/

CMD ["python3", "-u", "main.py"]
