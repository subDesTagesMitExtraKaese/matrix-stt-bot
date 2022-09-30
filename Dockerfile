FROM python:3.9-bullseye
WORKDIR /app/

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg libolm-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# Install Whisper
RUN pip install git+https://github.com/openai/whisper.git

# Install model files
RUN whisper --model tiny dummy.wav; exit 0
#RUN whisper --model base dummy.wav; exit 0
#RUN whisper --model small dummy.wav; exit 0
#RUN whisper --model medium dummy.wav; exit 0
#RUN whisper --model large dummy.wav; exit 0
#RUN whisper --model tiny.en dummy.wav; exit 0
#RUN whisper --model base.en dummy.wav; exit 0
#RUN whisper --model small.en dummy.wav; exit 0
#RUN whisper --model medium.en dummy.wav; exit 0

ADD requirements.txt /app/

RUN pip install -r requirements.txt

VOLUME /data/

ADD . /app/

CMD ["python", "-u", "main.py"]