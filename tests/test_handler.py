from types import SimpleNamespace

import nio
import pytest

from handler import file_suffix, is_media_event, transcribe_event


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response
        self.downloads = []

    async def download(self, mxc):
        self.downloads.append(mxc)
        return self.response


class FakeBot:
    def __init__(self, response):
        self.async_client = FakeAsyncClient(response)


class FakeASR:
    def __init__(self, output="hello world"):
        self.output = output
        self.calls = []

    async def transcribe(self, path):
        with open(path, "rb") as file:
            self.calls.append((path, file.read()))
        return self.output


def make_event(cls=nio.RoomMessageAudio, body="voice message", url="mxc://example/abc"):
    event = cls.__new__(cls)
    event.body = body
    event.url = url
    event.source = {"content": {}}
    return event


def download_response(body=b"audio-bytes", filename="voice-message.ogg"):
    return SimpleNamespace(body=body, filename=filename)


@pytest.mark.parametrize(
    "filename, expected",
    [
        ("voice-message.ogg", ".ogg"),
        ("clip.webm", ".webm"),
        ("https://matrix.example/_matrix/media/v3/download/abc.ogg", ".ogg"),
        ("https://matrix.example/file.mp3?download=true", ".mp3"),
        ("no-extension", ""),
        ("", ""),
        (None, ""),
    ],
)
def test_file_suffix(filename, expected):
    assert file_suffix(filename) == expected


def test_media_event_detection():
    assert is_media_event(make_event(nio.RoomMessageAudio))
    assert is_media_event(make_event(nio.RoomMessageVideo))
    assert is_media_event(make_event(nio.RoomEncryptedAudio))
    assert is_media_event(make_event(nio.RoomEncryptedVideo))
    assert not is_media_event(make_event(nio.RoomMessageText))


async def test_transcribes_audio_and_formats_reply():
    bot = FakeBot(download_response(body=b"audio-bytes"))
    asr = FakeASR(output="hello world")
    event = make_event()

    reply = await transcribe_event(bot, event, asr)

    assert reply == "Transcription of voice-message.ogg: hello world"
    assert bot.async_client.downloads == ["mxc://example/abc"]
    path, content = asr.calls[0]
    assert path.endswith(".ogg")
    assert content == b"audio-bytes"


async def test_falls_back_to_event_body_for_filename():
    bot = FakeBot(download_response(filename=None))
    asr = FakeASR()
    event = make_event(body="clip.webm")

    reply = await transcribe_event(bot, event, asr)

    assert reply == "Transcription of clip.webm: hello world"
    assert asr.calls[0][0].endswith(".webm")


async def test_reply_without_filename():
    bot = FakeBot(download_response(filename=None))
    asr = FakeASR()
    event = make_event(body="")

    reply = await transcribe_event(bot, event, asr)

    assert reply == "Transcription: hello world"


async def test_download_error_is_handled():
    bot = FakeBot(nio.responses.DownloadError("not found"))
    asr = FakeASR()

    assert await transcribe_event(bot, make_event(), asr) is None
    assert asr.calls == []


async def test_empty_download_is_handled():
    bot = FakeBot(download_response(body=b""))
    asr = FakeASR()

    assert await transcribe_event(bot, make_event(), asr) is None
    assert asr.calls == []


async def test_empty_transcription_is_handled():
    bot = FakeBot(download_response())
    asr = FakeASR(output="")

    assert await transcribe_event(bot, make_event(), asr) is None


async def test_encrypted_attachment_is_decrypted(monkeypatch):
    decrypted = b"decrypted-audio"
    seen = {}

    def fake_decrypt(body, key, sha256, iv):
        seen.update(body=body, key=key, sha256=sha256, iv=iv)
        return decrypted

    monkeypatch.setattr(nio.crypto.attachments, "decrypt_attachment", fake_decrypt)

    bot = FakeBot(download_response(body=b"ciphertext"))
    asr = FakeASR()
    event = make_event(nio.RoomEncryptedAudio)
    event.source = {
        "content": {
            "file": {
                "key": {"k": "the-key"},
                "hashes": {"sha256": "the-hash"},
                "iv": "the-iv",
            }
        }
    }

    reply = await transcribe_event(bot, event, asr)

    assert reply == "Transcription of voice-message.ogg: hello world"
    assert seen == {
        "body": b"ciphertext",
        "key": "the-key",
        "sha256": "the-hash",
        "iv": "the-iv",
    }
    assert asr.calls[0][1] == decrypted
