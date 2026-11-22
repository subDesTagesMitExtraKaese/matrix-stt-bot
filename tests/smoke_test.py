"""Integration smoke test, runs inside the built image:

    docker run --rm \
        -v "$PWD/tests:/tests:ro" \
        -v "$PWD/whisper.cpp/samples:/samples:ro" \
        matrix-stt-bot:ci python3 /tests/smoke_test.py
"""

import asyncio
import glob
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

APP = Path("/app")
SAMPLES = Path(os.environ.get("SMOKE_SAMPLES", "/samples"))
MODEL = os.environ.get("SMOKE_MODEL", "tiny")
MODEL_DIR = os.environ.get("SMOKE_MODEL_DIR", "/tmp/models")


def check(condition, message):
    if not condition:
        sys.exit(f"FAIL: {message}")


def run(*args, **kwargs):
    return subprocess.run(args, capture_output=True, text=True, timeout=300, **kwargs)


def normalize(text):
    return " ".join(re.findall(r"[a-z0-9']+", text.lower()))


def check_binary():
    result = run("./whisper-cli", "--help", cwd=APP)
    check(result.returncode == 0, f"whisper-cli --help failed: {result.stderr}")

    for pattern in ("whisper-cli", "libwhisper.so*", "libggml*.so*", "libparakeet.so*"):
        libraries = glob.glob(str(APP / pattern))
        check(libraries, f"no file matching {pattern}")
        for library in libraries:
            ldd = run("ldd", library)
            check("not found" not in ldd.stdout, f"missing shared library for {library}")

    check((APP / "download-ggml-model.sh").is_file(), "model download script missing")


def check_python_imports():
    result = run(sys.executable, "-c", "import aiohttp, nio, simplematrixbotlib", cwd=APP)
    check(result.returncode == 0, f"python imports failed: {result.stderr}")

    check(shutil.which("matrix-stt-bot"), "matrix-stt-bot entry point missing")

    env = {
        **os.environ,
        "HOMESERVER": "https://matrix.invalid",
        "USERNAME": "@stt-bot:matrix.invalid",
        "PASSWORD": "unused",
        "ASR_MODEL": MODEL,
        "ASR_LANGUAGE": "en",
    }
    result = run(
        sys.executable,
        "-c",
        "from matrix_stt_bot.app import create_bot; create_bot()",
        cwd=APP,
        env=env,
    )
    check(result.returncode == 0, f"creating the bot failed: {result.stderr}")


def check_transcription():
    from matrix_stt_bot.asr import ASR

    asr = ASR(MODEL, "en", MODEL_DIR)
    asr.load_model()

    for sample in ("jfk.wav", "jfk.mp3"):
        text = normalize(asyncio.run(asr.transcribe(str(SAMPLES / sample))))
        check("fellow americans" in text, f"unexpected {sample} transcription: {text}")
        check("country" in text, f"unexpected {sample} transcription: {text}")


def main():
    check_binary()
    check_python_imports()
    check_transcription()
    print("smoke test OK")


if __name__ == "__main__":
    main()
