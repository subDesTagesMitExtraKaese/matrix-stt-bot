import ffmpeg
import subprocess
import tempfile

SAMPLE_RATE = 16000

def convert_audio(data: bytes) -> bytes:
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

  return out

class ASR():
  def __init__(self, model = "tiny"):
    self.model = model

  def transcribe(self, audio: bytes) -> str:
    audio = convert_audio(audio)
    with tempfile.NamedTemporaryFile("w+b") as file:
      file.write(audio)
      file.flush()
      stdout, stderr = subprocess.Popen(
          ["./main", "-m", f"models/ggml-{self.model}.bin", "-f", file.name], 
          stdout=subprocess.PIPE
        ).communicate()
      if stderr:
        print(stderr.decode())
    return stdout.decode()