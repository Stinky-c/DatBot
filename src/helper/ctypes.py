from typing import NamedTuple
from pydantic import HttpUrl
import disnake
from disnake.ext import commands
from uuid import UUID as UUID_

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


class URL(HttpUrl):
    def __init__(self, *, url: str) -> None:
        super().__init__(url)

    @commands.converter_method
    def test(cls, inter: CmdInter, url: str):
        return cls(url)


class UUID(UUID_):
    @commands.converter_method
    async def covert(cls, inter: CmdInter, arg: str):
        try:
            cls(arg)
        except ValueError as e:
            await inter.send("Invalid UUID")
            raise e
