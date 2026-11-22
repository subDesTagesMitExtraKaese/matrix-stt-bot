# Matrix Speech‑To‑Text Bot

## Introduction

The **Matrix Speech‑To‑Text Bot** is a powerful tool that transcribes audio messages using [OpenAI Whisper](https://github.com/openai/whisper).
It is built on top of [Simple‑Matrix‑Bot‑Lib](https://codeberg.org/imbev/simplematrixbotlib) and leverages the fast inference engine provided by [whisper.cpp](https://github.com/ggerganov/whisper.cpp).

---

## Key Features

- **Transcribes audio messages** from any Matrix room you invite the bot to.
- **Replies with the transcription** as a plain‑text Matrix message.
- Supports a wide range of Whisper models (`tiny`, `tiny.en`, `base`, `small`, `medium`, `large‑v3`, …) and languages.
- **Runs locally** – no third‑party cloud service is required.
- Optional **Vulkan** support for GPU‑accelerated inference.
- **Allowlist** support to restrict who can interact with the bot.

---
## Usage

The matrix bot is published as a ready‑to‑run Docker image on [DockerHub](https://hub.docker.com/r/ftcaplan/matrix-stt-bot) and [GHCR](https://github.com/subDesTagesMitExtraKaese/matrix-stt-bot/pkgs/container/matrix-stt-bot).

You can deploy it using `docker-compose`:

```yaml
services:
  matrix-stt-bot:
    image: ftcaplan/matrix-stt-bot
    restart: on-failure
    volumes:
      - ./data/:/data/
    environment:
      - "HOMESERVER=https://matrix.example.com"
      - "USERNAME=@stt-bot:example.com"
      - "PASSWORD=<password>"
      - "ASR_MODEL=tiny"
      - "ASR_LANGUAGE=en"
    
    # optional: pass rendering device to container to enable Vulkan support
    devices:
      - /dev/dri
```

## Development

The project is packaged with `pyproject.toml`. Install it in editable mode with the
development dependencies:

```sh
pip install -e '.[dev]'
```

This also installs the `matrix-stt-bot` entry point, so the bot can be started with
`matrix-stt-bot` or `python -m matrix_stt_bot`.

### Tests

The unit tests (message handling, model validation) need only the Python dependencies:

```sh
pytest -q
```

The integration smoke test checks the built image: whisper.cpp runs, all shared
libraries resolve, the Python modules import, and a WAV and an MP3 are transcribed
with the real `ASR` class. It runs inside the image, so no test dependencies are
baked into it:

```sh
docker build -t matrix-stt-bot:ci .
docker run --rm \
  -v "$PWD/tests:/tests:ro" \
  -v "$PWD/whisper.cpp/samples:/samples:ro" \
  matrix-stt-bot:ci python3 /tests/smoke_test.py
```

### CI

`.forgejo/workflows/ci.yml` runs the unit tests and builds the image, then runs the
smoke test against it. The `image` job needs a runner with access to the Docker
daemon; adjust `runs-on` to the label used by your Forgejo runner.

GitHub Actions (`.github/workflows/docker.yml`) is only used for publishing tagged
releases to DockerHub and GHCR.

## Configuration

### ASR Model

You can choose a model by setting it with `ASR_MODEL`. Available models include `tiny.en`, `tiny`, `base`, `small`, `medium`, and `large-v3`. The default is `ASR_MODEL=tiny`.

### Authentication

You can authenticate using tokens instead of a password: Set `LOGIN_TOKEN=<login-token>` or `ACCESS_TOKEN=<access-token>` instead of `PASSWORD=<password>`.

### Allowlist

To restrict commands to specific users, you can set up an allowlist using regular expressions of Matrix user IDs. This feature allows you to specify which users are allowed to send commands to the bot.

- If the `ALLOWLIST` environment variable is defined, the bot will parse it and use it as the allowlist.
- Example: `ALLOWLIST=^@user1:example.com$,^@user2:example.com$`
- If `ALLOWLIST` is not defined, the bot will only allow commands from users of the bot's homeserver.
