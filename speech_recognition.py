import whisper
import ffmpeg
import numpy as np

SAMPLE_RATE = 16000

def load_audio(data: bytes):
  try:
    # This launches a subprocess to decode audio while down-mixing and resampling as necessary.
    # Requires the ffmpeg CLI and `ffmpeg-python` package to be installed.
    out, _ = (
      ffmpeg.input("pipe:", threads=0)
      .output("-", format="s16le", acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
      .run(cmd="ffmpeg", capture_stdout=True, capture_stderr=True, input=data)
    )
  except ffmpeg.Error as e:
    raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

  return np.frombuffer(out, np.int16).flatten().astype(np.float32) / 32768.0

class ASR():
  def __init__(self, model = "tiny"):
    self.model = whisper.load_model(model)

  def transcribe(self, audio: bytes):
    audio = load_audio(audio)
    return self.model.transcribe(audio)