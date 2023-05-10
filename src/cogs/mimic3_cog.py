from contextvars import ContextVar
from typing import TypeAlias

import disnake
from disnake.ext import commands, plugins
from helper import CogMetaData, DatBot, Settings, bytes2human
from helper.mimic3 import Mimic3Wrapper

# Meta
metadata = CogMetaData(
    name="mimic3",
    key="mimic3",
    require_key=True,
)
plugin: plugins.Plugin[DatBot] = plugins.Plugin(
    name=metadata.name, logger=f"cog.{metadata.name}"
)

# Aliases
CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
GuildInter: TypeAlias = disnake.GuildCommandInteraction

# Context Vars
m3api: ContextVar[Mimic3Wrapper] = ContextVar(metadata.name + "api")


@plugin.load_hook
async def cog_load():
    conf: dict = Settings.keys.get(metadata.key)
    wrapper = Mimic3Wrapper(
        await plugin.bot.make_http(metadata.name, base_url=conf["url"]),
        lang=conf.get("lang", "en_US"),
        model=conf.get("model", "vctk_low"),
        voice=conf.get("voice", "p376"),
    )
    m3api.set(wrapper)


@commands.slash_command(name=metadata.name)
async def cmd(inter: CmdInter):
    plugin.logger.debug(f"{inter.author.name} @ {inter.guild.name}")


@cmd.sub_command("speak")
async def ping(inter: CmdInter, text: str):
    """Generates a wav file using the selected voice
    Parameters
    ----------
    text: a body of text to generate"""
    await inter.response.defer()
    buf, blen = await m3api.get().speak(text)
    await inter.send(
        f"Size: '{bytes2human(blen)}'", file=disnake.File(buf, "output.wav")
    )


setup, teardown = plugin.create_extension_handlers()
