#!/usr/bin/env python3
from urllib.parse import urlparse
import tempfile
import os

import whisper
import simplematrixbotlib as botlib
import nio

model = whisper.load_model("tiny")

creds = botlib.Creds(
  homeserver=os.environ['HOMESERVER'],
  username=os.environ['USERNAME'],
  password=os.getenv('PASSWORD', None),
  login_token=os.getenv('LOGIN_TOKEN', None),
  access_token=os.getenv('ACCESS_TOKEN', None),
  session_stored_file="/data/session.txt"
)

config = botlib.Config()
config.encryption_enabled = True
config.emoji_verify = True
config.ignore_unverified_devices = True
config.store_path = '/data/crypto_store/'
bot = botlib.Bot(creds, config)

@bot.listener.on_custom_event(nio.RoomMessageAudio)
async def on_audio_message(room, event):
  print(event.sender, event.body, event.url)
  match = botlib.MessageMatch(room, event, bot)
  if match.is_not_from_this_bot():
    bot.async_client.room_typing(room, )
    url = urlparse(event.url)
    response = await bot.async_client.download(server_name=url.netloc, media_id=url.path[1:])
    print(response)
    with tempfile.NamedTemporaryFile("w+b") as file:
      file.write(response.body)
      file.flush()
      print(file.name)
      result = model.transcribe(file.name)

    await bot.api.send_text_message(
      room_id=room.room_id,
      message=f"Transcription of {response.filename}: {result['text']}",
      msgtype="m.notice")

bot.run()