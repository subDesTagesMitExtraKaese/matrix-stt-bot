import asyncio
import subprocess
import os

MODELS = [
  "tiny",
  "tiny.en",
  "tiny-q5_1",
  "tiny.en-q5_1",
  "tiny-q8_0",
  "base",
  "base.en",
  "base-q5_1",
  "base.en-q5_1",
  "base-q8_0",
  "small",
  "small.en",
  "small.en-tdrz",
  "small-q5_1",
  "small.en-q5_1",
  "small-q8_0",
  "medium",
  "medium.en",
  "medium-q5_0",
  "medium.en-q5_0",
  "medium-q8_0",
  "large-v1",
  "large-v2",
  "large-v2-q5_0",
  "large-v2-q8_0",
  "large-v3",
  "large-v3-q5_0",
  "large-v3-turbo",
  "large-v3-turbo-q5_0",
  "large-v3-turbo-q8_0",
]

class ASR():
  def __init__(self, model = "tiny", language = "en"):
    if os.path.exists(f"/app/ggml-{model}.bin"):
      self.model_path = f"/app"
    else:
      self.model_path = f"/data/models"
      if not os.path.exists(self.model_path):
        os.mkdir(self.model_path)

    file_path = f"{self.model_path}/ggml-{model}.bin"
    if not os.path.exists(file_path) and model not in MODELS:
      raise ValueError(f"Invalid model: {model}. Must be one of {MODELS}")

    self.model = model
    self.language = language
    self.file_path = file_path
    self.lock = asyncio.Lock()

  def load_model(self):
    if not os.path.exists(self.file_path) or os.path.getsize(self.file_path) == 0:
      print("Downloading model...")
      subprocess.run(["./download-ggml-model.sh", self.model, self.model_path], check=True)
      print("Done.")

  async def transcribe(self, file: str) -> str:
    async with self.lock:
      print(f"transcriibing {file}...")
      proc = await asyncio.create_subprocess_exec(
          "./whisper-cli",
          "-m", f"{self.model_path}/ggml-{self.model}.bin",
          "-l", self.language,
          "-f", file,
          "-nt",
          stdout=asyncio.subprocess.PIPE,
          stderr=asyncio.subprocess.PIPE
        )
      stdout, stderr = await proc.communicate()

    if stderr:
      print(stderr.decode())
      
    text = stdout.decode().strip()
    print(text)

    return text