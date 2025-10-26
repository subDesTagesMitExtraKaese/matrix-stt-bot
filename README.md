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

The matrix bot is published as a ready‑to‑run Docker image on [DockerHub](https://hub.docker.com/r/ftcaplan/matrix-stt-bot).

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
