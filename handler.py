from urllib.parse import urlparse
import os
import tempfile

import nio

MEDIA_TYPES = (
    nio.RoomMessageAudio,
    nio.RoomEncryptedAudio,
    nio.RoomMessageVideo,
    nio.RoomEncryptedVideo,
)

ENCRYPTED_TYPES = (nio.RoomEncryptedAudio, nio.RoomEncryptedVideo)


def is_media_event(event) -> bool:
    return isinstance(event, MEDIA_TYPES)


def file_suffix(filename) -> str:
    if not filename:
        return ""
    basename = os.path.basename(urlparse(filename).path)
    return os.path.splitext(basename)[1]


async def transcribe_event(bot, event, asr):
    """Transcribe a media event and return the reply body, or None if there is nothing to send."""
    response = await bot.async_client.download(mxc=event.url)
    if isinstance(response, nio.responses.DownloadError):
        print(response)
        return None

    if isinstance(event, ENCRYPTED_TYPES):
        print("decrypting...")
        file_info = event.source["content"]["file"]
        data = nio.crypto.attachments.decrypt_attachment(
            response.body,
            file_info["key"]["k"],
            file_info["hashes"]["sha256"],
            file_info["iv"],
        )
    else:
        data = response.body

    if not data:
        return None

    filename = response.filename or event.body

    with tempfile.NamedTemporaryFile("w+b", suffix=file_suffix(filename)) as file:
        file.write(data)
        file.flush()
        result = await asr.transcribe(file.name)

    if not result:
        print("No result")
        return None

    if filename:
        return f"Transcription of {filename}: {result}"
    return f"Transcription: {result}"
