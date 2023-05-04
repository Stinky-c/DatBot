from aiohttp import ClientSession
from io import BytesIO


class Mimic3Wrapper:
    def __init__(
        self,
        client: ClientSession,
        lang: str = "en_US",
        model: str = "vctk_low",
        voice: str = "p376",
    ) -> None:
        self._client = client
        self._lang = lang
        self._model = model
        self._voice = voice

    @property
    def voice_key(self):
        return f"{self._lang}/{self._model}#{self._voice}"

    @voice_key.setter
    def voice_key(self, lang: str | None, model: str | None, voice: str | None):
        self._lang = lang or self._lang
        self._model = model or self._model
        self._voice = voice or self._voice

    async def speak(self, text: str) -> BytesIO:
        buf = BytesIO()
        async with self._client.get(
            "/api/tts",
            params={"text": text, "voice": self.voice_key},
            headers={"content-type": "text/plain"},
        ) as req:
            req.raise_for_status()
            buf.write(await req.content.read())
        blen = buf.tell()
        buf.seek(0)
        return buf, blen

    async def voices(self) -> dict:
        async with self._client.get("/api/voices") as req:
            req.raise_for_status()
            return await req.json()
