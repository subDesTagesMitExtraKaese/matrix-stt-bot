# main image
FROM python:3.9-bullseye
WORKDIR /app/

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libolm-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Whisper
RUN pip install git+https://github.com/openai/whisper.git

ADD requirements.txt .

RUN pip install -r requirements.txt && \
  apt-get autoremove -y

VOLUME /data/

ADD ./*.py /app/

CMD ["python3", "-u", "main.py"]