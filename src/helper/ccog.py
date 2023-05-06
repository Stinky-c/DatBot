from logging import Logger
from typing import TYPE_CHECKING, TypeAlias

import disnake
from disnake.ext import commands

from .models import Server

if TYPE_CHECKING:
    from .cbot import DatBot


class Cog(commands.Cog):
    """A subclass of `disnake.ext.commands.cog` to provide injections and other shared code"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    log: Logger
    bot: "DatBot"
    name = "PLACEHOLDER"
    key_loc: str = None
    key_enabled: bool = False

    def __init__(self, bot: "DatBot") -> None:
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    @commands.register_injection
    async def get_server(self, inter: CmdInter) -> Server:
        s = await Server.find_one(inter.guild_id == Server.sid)
        if not s:
            return await Server.from_guild(inter.guild).create()
        return s
