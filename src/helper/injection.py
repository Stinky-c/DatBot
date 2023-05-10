from typing import TypeAlias

import disnake
from disnake.ext import commands

from .models import Server

CmdInter: TypeAlias = disnake.ApplicationCommandInteraction


@commands.register_injection
async def get_server(inter: CmdInter) -> Server:
    s = await Server.find_one(inter.guild_id == Server.sid)
    if not s:
        return await Server.from_guild(inter.guild).create()
    return s
