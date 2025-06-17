import tempfile
import asyncio
import time
import os

from pywhispercpp.model import Model

class ASR():
  def __init__(self, model_name = "tiny", language = None):
    self.models_dir = f"/data/models"
    if not os.path.exists(self.models_dir):
      os.mkdir(self.models_dir)

    self.model = None
    self.model_name = model_name
    self.language = language
    self.lock = asyncio.Lock()

  def load_model(self):
    if not os.path.exists(f"{self.models_dir}/ggml-{self.model_name}.bin"):
      print(f"Downloading Model {self.model_name} ...")
    self.model = Model(self.model_name, models_dir=self.models_dir, language=self.language, print_progress=False)

  async def transcribe(self, data: bytes) -> str:
    async with self.lock:
      with tempfile.NamedTemporaryFile("w+b") as file:
        file.write(data)
        file.flush()
        start = time.perf_counter()
        segments = await asyncio.to_thread(self.model.transcribe, file.name, new_segment_callback=print)
        end = time.perf_counter()
        print(f"Transcribed media in {end - start:.3f}s")
        return " ".join([s.text for s in segments])