# Matrix Speech-To-Text Bot

Transcribes audio messages using [OpenAI Whisper](https://github.com/openai/whisper).

This bot is based on [Simple-Matrix-Bot-Lib](https://github.com/i10b/simplematrixbotlib) and [whisper.cpp](https://github.com/ggerganov/whisper.cpp). It downloads audio messages from your homeserver, transcribes them locally and responds with the result as a text message.

## Usage

The bot is available as an image on [DockerHub](https://hub.docker.com/r/ftcaplan/matrix-stt-bot).
You can deploy it using `docker-compose`:

```yaml
version: "3.7"

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
```

## Configuration
The bot will download the model file on first run to reduce image size. Available models are `tiny.en`, `tiny`, `base.en`, `base`, `small.en`, `small`, `medium.en`, `medium`, and `large`. The default is `ASR_MODEL=tiny`.

You can authenticate using tokens instead of a password by setting `LOGIN_TOKEN=<login-token>` or `ACCESS_TOKEN=<access-token>` instead of `PASSWORD=<password>`.

- **ASR_MODEL**: You can choose a docker tag with the corresponding model pre downloaded or set it with `ASR_MODEL`. Available models are `tiny.en`, `tiny`, `base.en`, `base`, `small.en`, `small`, `medium.en`, `medium`, and `large`. The default is `ASR_MODEL=tiny`.

- **Authentication**:
  - You can authenticate using tokens instead of a password:
    - Set `LOGIN_TOKEN=<login-token>` or `ACCESS_TOKEN=<access-token>` instead of `PASSWORD=<password>`.

- **Allowlist**:
  - To restrict commands to specific users, you can set up an allowlist using regular expressions of Matrix user IDs. This feature allows you to specify which users are allowed to send commands to the bot.
    - If the `ALLOWLIST` environment variable is defined, the bot will parse it and use it as the allowlist.
    - Example: `ALLOWLIST=^@user1:example.com$,^@user2:example.com$`
    - If `ALLOWLIST` is not defined, the bot will only allow commands from users of the bot's homeserver.
