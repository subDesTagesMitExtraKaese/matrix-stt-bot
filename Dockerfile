FROM python:3-bullseye-slim
WORKDIR /app/

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libolm-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ADD requirements.txt .

RUN pip install -r requirements.txt

# Install Whisper
ADD whisper.cpp/ .
RUN cd whisper.cpp && \
    make tiny && \
    cp main ../whisper && \
    cp models/ .. && \
    cd .. && \
    rm -rf whisper.cpp/

VOLUME /data/

ADD . /app/

CMD ["python", "-u", "main.py"]