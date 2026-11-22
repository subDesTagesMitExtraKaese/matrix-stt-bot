import os
from pathlib import Path

import pytest

from matrix_stt_bot.asr import ASR

MODEL = os.getenv("TEST_MODEL", "tiny")


def test_invalid_model_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="Invalid model"):
        ASR("not-a-real-model", model_dir=str(tmp_path))


def test_model_directory_is_created(tmp_path):
    asr = ASR(MODEL, model_dir=str(tmp_path / "models"))

    assert Path(asr.file_path).parent.is_dir()
    assert asr.file_path == str(tmp_path / "models" / f"ggml-{MODEL}.bin")
