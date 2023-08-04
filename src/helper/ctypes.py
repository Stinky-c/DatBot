from collections import UserDict
from dataclasses import dataclass
from typing import Any, AsyncIterator, NamedTuple, Optional, TypeAlias, TypeVar
from uuid import UUID as UUID_

import aiohttp
import disnake
from curse_api.abc import APIFactory
from disnake.ext import commands
from pydantic import BaseModel, HttpUrl
from pydantic.error_wrappers import ValidationError

from helper.errors import ImproperConfiguration

CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
T = TypeVar("T", bound=BaseModel)


class _MissingType:
    def __eq__(self, other: Any) -> bool:
        return False

    def __bool__(self) -> bool:
        return False

    def __repr__(self) -> str:
        return "<MISSING>"


MISSING: Any = _MissingType()


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
    """
    name: Name of the plugin/cog to load
    description: A short description of the plugin/cog
    require_key: determines if a key field is needed
    key: the string name to the field object
    skip: skip loading the plugin/cog. Disables unfinished cogs
    """

    name: str
    description: str | None = None
    require_key: bool = False
    key: str | None = None
    skip: bool = False


class AiohttpCurseClient(APIFactory):
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self._sess = session

    async def get(self, url: str, params: Optional[dict] = None) -> dict[Any, Any]:
        res = await self._sess.get(url, params=params)
        res.raise_for_status()
        return await res.json()

    async def post(self, url: str, params: Optional[dict] = None) -> dict[Any, Any]:
        res = await self._sess.post(url, json=params)
        res.raise_for_status()
        return await res.json()

    async def download(self, url: str, chunk_size: int) -> AsyncIterator[bytes]:
        res = await self._sess.get(url, allow_redirects=True)
        res.raise_for_status()
        return res.conteniter_chunked(chunk_size)

    async def close(self):
        await self._sess.close()


class PydanticDict(UserDict):
    """Finds a key and attempts to return a populated pydantic model"""

    def get(self, key: Any, cls: T) -> T:
        return self.__getitem__(key, cls)

    def __getitem__(self, __key: Any, cls: T) -> T:
        v = super().__getitem__(__key)
        try:
            obj = cls.parse_obj(v)
            return obj
        except ValidationError as exc:
            raise ImproperConfiguration(f"'{__key}' is improperly configured.", exc)

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, dict):
            raise TypeError(f"Expected '{dict!r}' got '{v!r}'")
        return cls(v)
