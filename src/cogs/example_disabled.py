# ruff: noqa: F401
from typing import TypeAlias

import disnake
from disnake.ext import commands, plugins
from helper import CogMetaData, ConVar, DatBot, Settings

# Meta
metadata = CogMetaData(
    name="example",
    description="This is the base for creating a new cog",
    key=None,
    require_key=False,
)
plugin: plugins.Plugin[DatBot] = plugins.Plugin(
    name=metadata.name, logger=f"cog.{metadata.name}"
)

# Aliases
CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
GuildInter: TypeAlias = disnake.GuildCommandInteraction

# Context Vars
message: ConVar[str] = ConVar(f"{metadata.name}.message")


@plugin.load_hook()
async def cog_load():
    message.set("ABC")
    plugin.logger.debug(f"Hello from {metadata.name}!")


@plugin.unload_hook()
async def cog_unload():
    plugin.logger.debug(f"Goodbye from {metadata.name}!")


@plugin.slash_command(name=metadata.name)
async def cmd(inter: CmdInter):
    plugin.logger.debug(f"{inter.author.name} @ {inter.guild.name}")


@cmd.sub_command(name="ping")
async def ping(inter: CmdInter, abc: str):
    """Placeholder
    Parameters
    ----------
    abc: placeholder"""
    await inter.send(f"{message.get()}! {round(plugin.bot.latency * 1000)}ms")


setup, teardown = plugin.create_extension_handlers()
