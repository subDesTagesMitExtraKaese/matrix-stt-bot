import ffmpeg
import subprocess
from itertools import takewhile
import os

SAMPLE_RATE = 16000

def convert_audio(data: bytes) -> bytes:
  try:
    # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
    # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
    out, _ = (
      ffmpeg.input("pipe:", threads=0)
      .output("audio.wav", format="wav", acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
      .run(cmd="ffmpeg", capture_stdout=True, capture_stderr=True, input=data)
    )
  except ffmpeg.Error as e:
    raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

  return out

class ASR():
  def __init__(self, model = "tiny"):
    self.model = model

  def transcribe(self, audio: bytes) -> str:
    convert_audio(audio)
    stdout, stderr = subprocess.Popen(
        ["./main", "-m", f"models/ggml-{self.model}.bin", "-f", "audio.wav", "--no_timestamps"], 
        stdout=subprocess.PIPE
      ).communicate()

    os.remove("audio.wav")

    if stderr:
      print(stderr.decode())

    lines = stdout.decode().splitlines()[23:]
    print('\n'.join(lines))
    text = takewhile(lambda x: x, lines)
    return '\n'.join(text)