#!/usr/bin/env python3
import tempfile
from urllib.parse import urlparse
import os

import simplematrixbotlib as botlib
import nio

import whisper

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

model = whisper.load_model(os.getenv('ASR_MODEL', 'tiny'))

@bot.listener.on_custom_event(nio.RoomMessage)
async def on_message(room, event):
  if not isinstance(event, (nio.RoomMessageAudio,
                            nio.RoomEncryptedAudio,
                            nio.RoomMessageVideo,
                            nio.RoomEncryptedVideo)):
    return

  encrypted = isinstance(event, (nio.RoomEncryptedAudio, nio.RoomEncryptedVideo))

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

    with tempfile.NamedTemporaryFile("w+b") as file:
      file.write(data)
      file.flush()
      print(file.name)
      result = model.transcribe(file.name)['text']
    await bot.async_client.room_typing(room.machine_name, False)

    if not result:
      print("No result")
      return

    filename = response.filename or event.body
    if filename:
      reply = f"Transcription of {filename}: {result}"
    else:
      reply = f"Transcription: {result}"

    await bot.api._send_room(
      room_id=room.room_id,
      content={
        "msgtype": "m.notice",
        "body": reply,
        "m.relates_to": {
          "m.in_reply_to": {
            "event_id": event.event_id
          }
        }
      })

if __name__ == "__main__":
  bot.run()
