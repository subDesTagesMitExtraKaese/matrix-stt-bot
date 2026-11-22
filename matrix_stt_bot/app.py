import os
import traceback
import asyncio

import aiohttp
import nio
import simplematrixbotlib as botlib

from .asr import ASR
from .handler import is_media_event, transcribe_event


def create_bot():
    creds = botlib.Creds(
        homeserver=os.environ["HOMESERVER"],
        username=os.environ["USERNAME"],
        password=os.getenv("PASSWORD", None),
        login_token=os.getenv("LOGIN_TOKEN", None),
        access_token=os.getenv("ACCESS_TOKEN", None),
        session_stored_file="/data/session.txt",
    )

    config = botlib.Config()
    config.encryption_enabled = True
    config.emoji_verify = False
    config.ignore_unverified_devices = True
    config.store_path = "/data/crypto_store/"
    if "ALLOWLIST" in os.environ:
        config.allowlist = os.environ["ALLOWLIST"].split(",")

    bot = botlib.Bot(creds, config)
    asr = ASR(os.getenv("ASR_MODEL", "tiny"), os.getenv("ASR_LANGUAGE", "en"))

    @bot.listener.on_custom_event(nio.RoomMessage)
    async def on_message(room, event):
        if not is_media_event(event):
            return

        print(room.machine_name, event.sender, event.body, event.url)
        match = botlib.MessageMatch(room, event, bot)
        if not match.is_not_from_this_bot():
            return

        await bot.async_client.room_typing(room.machine_name, True, timeout=120000)
        reply = await transcribe_event(bot, event, asr)
        await bot.async_client.room_typing(room.machine_name, False)

        if not reply:
            return

        await bot.api._send_room(
            room_id=room.room_id,
            content={
                "msgtype": "m.notice",
                "body": reply,
                "m.relates_to": {"m.in_reply_to": {"event_id": event.event_id}},
            },
        )

    return bot, asr


async def main():
    bot, asr = create_bot()
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


def run():
    asyncio.run(main())
