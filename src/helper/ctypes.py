from dataclasses import dataclass
from typing import Any, AsyncIterator, Dict, NamedTuple, Optional
from uuid import UUID as UUID_

import aiohttp
import disnake
from curse_api.abc import APIFactory
from disnake.ext import commands
from pydantic import HttpUrl

CmdInter = disnake.CommandInteraction


class LinkTuple(NamedTuple):
    """A helper class for Link View

    Args:
        label (str): Label to apply to button
        url (str): url to apply to button
        emoji (Emoji): accepts `disnake.Emoji` or str
    """

    label: str
    url: str
    emjoi: disnake.Emoji | disnake.PartialEmoji | str = "⛓️"

    def as_component(self):
        return disnake.ui.Button(label=self.label, url=self.url, emoji=self.emjoi)


class URL(HttpUrl):
    def __init__(self, *, url: str) -> None:
        super().__init__(url)

    @commands.converter_method
    def convert(cls, inter: CmdInter, url: str):
        return cls(url)


class UUID(UUID_):
    @commands.converter_method
    async def covert(cls, inter: CmdInter, arg: str):
        try:
            cls(arg)
        except ValueError as e:
            await inter.send("Invalid UUID")
            raise e


@dataclass
class CogMetaData:
    name: str
    description: str | None = None
    require_key: bool = False
    key: str | None = None


class AiohttpCurseClient(APIFactory):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._sess = session

    async def get(self, url: str, params: Optional[dict] = None) -> Dict[Any, Any]:
        res = await self._sess.get(url, params=params)
        res.raise_for_status()
        return await res.json()

    async def post(self, url: str, params: Optional[dict] = None) -> Dict[Any, Any]:
        res = await self._sess.post(url, json=params)
        res.raise_for_status()
        return await res.json()

    async def download(self, url: str, chunk_size: int) -> AsyncIterator[bytes]:
        res = await self._sess.get(url, allow_redirects=True)
        res.raise_for_status()
        return res.content.iter_chunked(chunk_size)

    async def close(self):
        await self._sess.close()
