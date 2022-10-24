#!/usr/bin/env python3
from urllib.parse import urlparse
import os

import simplematrixbotlib as botlib
import nio

from speech_recognition import ASR

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
config.emoji_verify = False
config.ignore_unverified_devices = True
config.store_path = '/data/crypto_store/'
bot = botlib.Bot(creds, config)

asr = ASR(os.getenv('ASR_MODEL', 'tiny'))

@bot.listener.on_custom_event(nio.RoomMessageAudio)
async def on_message_audio(room, event):
  await on_audio(room, event, False)

@bot.listener.on_custom_event(nio.RoomEncryptedAudio)
async def on_encrypted_audio(room, event):
  await on_audio(room, event, True)

async def on_audio(room, event, encrypted):
  print(room.machine_name, event.sender, event.body, event.url)
  match = botlib.MessageMatch(room, event, bot)
  if match.is_not_from_this_bot():
    await bot.async_client.room_typing(room.machine_name, True, timeout=120000)
    url = urlparse(event.url)
    response = await bot.async_client.download(server_name=url.netloc, media_id=url.path[1:])
    if encrypted:
      print("decrypting...")
      data = nio.crypto.attachments.decrypt_attachment(
        response.body,
        event.source["content"]["file"]["key"]["k"],
        event.source["content"]["file"]["hashes"]["sha256"],
        event.source["content"]["file"]["iv"],
      )
    else:
      data = response.body
    print(response)
    result = await asr.transcribe(data)

    await bot.async_client.room_typing(room.machine_name, False)
    if response.filename:
      await bot.api.send_text_message(
        room_id=room.room_id,
        message=f"Transcription of {response.filename}: {result}",
        msgtype="m.notice")
    else:
      await bot.api.send_text_message(
        room_id=room.room_id,
        message=f"Transcription: {result}",
        msgtype="m.notice")

if __name__ == "__main__":
  asr.load_model()
  bot.run()
