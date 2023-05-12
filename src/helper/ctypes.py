import typing as t
from dataclasses import dataclass
from uuid import UUID as UUID_

import aiohttp
import disnake
from curse_api.abc import APIFactory
from disnake.ext import commands
from pydantic import HttpUrl

CmdInter = disnake.CommandInteraction


class LinkTuple(t.NamedTuple):
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
    skip: bool = False


class AiohttpCurseClient(APIFactory):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._sess = session

    async def get(
        self, url: str, params: t.Optional[dict] = None
    ) -> dict[t.Any, t.Any]:
        res = await self._sess.get(url, params=params)
        res.raise_for_status()
        return await res.json()

    async def post(
        self, url: str, params: t.Optional[dict] = None
    ) -> dict[t.Any, t.Any]:
        res = await self._sess.post(url, json=params)
        res.raise_for_status()
        return await res.json()

    async def download(self, url: str, chunk_size: int) -> t.AsyncIterator[bytes]:
        res = await self._sess.get(url, allow_redirects=True)
        res.raise_for_status()
        return res.content.iter_chunked(chunk_size)

    async def close(self):
        await self._sess.close()


T = t.TypeVar("T")


class ConVar(t.Generic[T]):
    """ContextVars were giving me a headache, so I made a workaround with a similar api"""

    """
    TODO: add default
    TODO: some global mapping dict
    """

    def __init__(self, name: str) -> None:
        # if _mapping.get(name):
        #     raise KeyError("Key already exists")
        # _mapping[name] = self

        self.__name = name
        self.__value = None

    @property
    def name(self):
        return self.__name

    def set(self, value: T) -> T:
        old, self.__value = self.__value, value
        return old

    def get(self, default: T = None):
        if self.__value is None and default is not None:
            raise LookupError("ABC")
        return self.__value or default

    def reset(self):
        self.__value = None

    def __repr__(self) -> str:
        return f"<name={type(self).__name__} value={type(self.__value)}>"
