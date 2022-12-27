import tempfile
import ffmpeg
import asyncio
import subprocess
import os

SAMPLE_RATE = 16000

def convert_audio(data: bytes, out_filename: str):
  try:
    with tempfile.NamedTemporaryFile("w+b") as file:
      file.write(data)
      file.flush()
      print(f"Converting media {file.name} to {out_filename}")

      out, err = (
        ffmpeg.input(file.name, threads=0)
        .output(out_filename, format="wav", acodec="pcm_s16le", ac=1, ar=SAMPLE_RATE)
        .overwrite_output()
        .run(cmd="ffmpeg", capture_stdout=True, capture_stderr=True, input=data)
      )
    if os.path.getsize(out_filename) == 0:
      print(str(err, "utf-8"))
      raise Exception("Converted file is empty")
  except ffmpeg.Error as e:
    raise RuntimeError(f"Failed to load audio: {e.stderr.decode()}") from e

  return out

MODELS = ["tiny.en", "tiny", "base.en", "base", "small.en", "small", "medium.en", "medium", "large"]

class ASR():
  def __init__(self, model = "tiny", language = "en"):
    if model not in MODELS:
      raise ValueError(f"Invalid model: {model}. Must be one of {MODELS}")
    self.model = model
    self.language = language

    if os.path.exists(f"/app/ggml-model-whisper-{model}.bin"):
      self.model_path = f"/app/ggml-model-whisper-{model}.bin"
    else:
      self.model_path = f"/data/models/ggml-{model}.bin"
      if not os.path.exists("/data/models"):
        os.mkdir("/data/models")
        
    self.model_url = f"https://huggingface.co/datasets/ggerganov/whisper.cpp/resolve/main/ggml-{self.model}.bin"
    self.lock = asyncio.Lock()

  def load_model(self):
    if not os.path.exists(self.model_path) or os.path.getsize(self.model_path) == 0:
      print("Downloading model...")
      subprocess.run(["wget", self.model_url, "-O", self.model_path], check=True)
      print("Done.")

  async def transcribe(self, audio: bytes) -> str:
    filename = tempfile.mktemp(suffix=".wav")
    convert_audio(audio, filename)
    async with self.lock:
      proc = await asyncio.create_subprocess_exec(
          "./main",
          "-m", self.model_path,
          "-l", self.language,
          "-f", filename,
          "--no_timestamps", 
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
      stdout, stderr = await proc.communicate()

      os.remove(filename)

    if stderr:
      print(stderr.decode())
      
    text = stdout.decode().strip()
    print(text)

    return text