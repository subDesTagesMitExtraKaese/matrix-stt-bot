#!/usr/bin/env python3
from urllib.parse import urlparse
import os
import time
import traceback
import tempfile
import asyncio
import aiohttp

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
if 'ALLOWLIST' in os.environ:
  config.allowlist = os.environ['ALLOWLIST'].split(',')

bot = botlib.Bot(creds, config)

asr = ASR(os.getenv('ASR_MODEL', 'tiny'), os.getenv('ASR_LANGUAGE', 'en'))

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
    response = await bot.async_client.download(mxc=event.url)
    if isinstance(response, nio.responses.DownloadError):
      print(response)
      data = None
    elif encrypted:
      print("decrypting...")
      data = nio.crypto.attachments.decrypt_attachment(
        response.body,
        event.source["content"]["file"]["key"]["k"],
        event.source["content"]["file"]["hashes"]["sha256"],
        event.source["content"]["file"]["iv"],
      )
    else:
      data = response.body

    filename = response.filename or event.body
    if data:
      with tempfile.NamedTemporaryFile("w+b", suffix=filename) as file:
        file.write(data)
        file.flush()
        result = await asr.transcribe(file.name)
    else:
      result = None
    
    await bot.async_client.room_typing(room.machine_name, False)

    if not result:
      print("No result")
      return

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

async def main():
    asr.load_model()
    while True:
        try:
            await bot.main()
        except (asyncio.exceptions.TimeoutError, aiohttp.ClientError) as e:
            print(f"Network issue: {e}")
            traceback.print_exc()
            print("Network issue, restarting...")
            await asyncio.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}")
            traceback.print_exc()
            print("Unexpected error, restarting...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

