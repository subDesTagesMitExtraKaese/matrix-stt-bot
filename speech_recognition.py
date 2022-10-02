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

MODELS = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large"]

class ASR():
  def __init__(self, model = "tiny"):
    if model not in MODELS:
      raise ValueError(f"Invalid model: {model}. Must be one of {MODELS}")
    self.model = model
    os.mkdir("/data/models")
    self.model_path = f"/data/models/ggml-{model}.bin"
    self.model_url = f"https://ggml.ggerganov.com/ggml-model-whisper-{self.model}.bin"

  def load_model(self):
    if not os.path.exists(self.model_path):
      print("Downloading model...")
      subprocess.run(["wget", self.model_url, "-O", self.model_path], check=True)
      print("Done.")

  def transcribe(self, audio: bytes) -> str:
    convert_audio(audio)
    stdout, stderr = subprocess.Popen(
        ["./main", "-m", self.model_path, "-f", "audio.wav", "--no_timestamps"], 
        stdout=subprocess.PIPE
      ).communicate()

    os.remove("audio.wav")

    if stderr:
      print(stderr.decode())

    lines = stdout.decode().splitlines()[23:]
    print('\n'.join(lines))
    text = takewhile(lambda x: x, lines)
    return '\n'.join(text)