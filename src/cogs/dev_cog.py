import collections
import json
import platform as plat
from datetime import datetime
from typing import TypeAlias

import disnake
import psutil
from disnake.ext import commands, plugins
from helper import (
    UUID,
    CogMetaData,
    DatBot,
    Emojis,
    LinkTuple,
    LinkView,
    Settings,
    bytes2human,
    gen_quote,
    jdumps,
)
from helper.models import Quote

# Meta
metadata = CogMetaData(
    name="dev",
    description="This cog is filled with useful dev commands",
    key="dev",
    require_key=False,
)

plugin: "plugins.Plugin[DatBot]" = plugins.Plugin(
    name=metadata.name,
    logger=f"cog.{metadata.name}",
)

# Aliases
CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
GuildInter: TypeAlias = disnake.GuildCommandInteraction

# ContextVars


@commands.is_owner()
@plugin.slash_command(name="dev", guild_ids=Settings.bot.dev_guilds)
async def cmd(inter: CmdInter):
    plugin.logger.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")


@cmd.sub_command("close")
async def stop_(inter: CmdInter):
    """Stops the bot"""
    await inter.send(await gen_quote())
    await plugin.bot.close()


@cmd.sub_command("echo")
async def echo_(inter: CmdInter, message: str):
    await inter.send("Done!", ephemeral=True)
    await inter.channel.send(message)


@cmd.sub_command("info")
async def info_(inter: CmdInter):
    """Returns various system information"""

    vmem = psutil.virtual_memory()
    duse = psutil.disk_usage("/")
    pexe = psutil.Process()
    embed = (
        disnake.Embed(
            color=disnake.Color(0x9B42F5),
            timestamp=disnake.utils.utcnow(),
            title="System Usage",
        )
        .set_author(name="System Status", icon_url=plugin.bot.user.display_avatar.url)
        .add_field("OS", plat.system())
        .add_field("CPU Times", f"Current: {psutil.cpu_percent(0.1)}%")
        .add_field(
            "Memory Usage",
            f"{bytes2human(vmem.used)}/{bytes2human(vmem.available)}",
        )
        .add_field("Disk Usage", f"{bytes2human(duse.used)}/{bytes2human(duse.total)}")
        .add_field("Bot Uptime", disnake.utils.format_dt(pexe.create_time(), "R"))
        .add_field("Uptime", disnake.utils.format_dt(psutil.boot_time(), "R"))
    )
    await inter.send(embed=embed)


@cmd.sub_command("unload")
async def unload_(
    inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)
):
    """unloads a cog from the bot

    Parameters
    ----------
    cog: The cog path to unload
    """
    plugin.bot.unload_extension(cog)
    Settings.bot.cogs.remove(cog)
    await inter.send(f"`{cog}` has been unloaded {Emojis.thumbs_up}")


@cmd.sub_command("load")
async def load_(inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)):
    """loads a cog from the bot

    Parameters
    ----------
    cog: The cog path to unload
    """
    plugin.bot.load_extension(cog)
    await inter.send(f"`{cog}` has been loaded {Emojis.thumbs_up}")


@cmd.sub_command("embed")
async def emebed_img_(
    inter: CmdInter,
    file: disnake.Attachment,
    url: str,
    message: str,
):
    """

    Parameters
    ----------
    file: An image to add
    url: A url to add
    message: The message to add
    """
    await inter.response.defer()
    link = LinkTuple("Click Here!", url)
    await inter.channel.send(
        message, file=await file.to_file(), view=LinkView(links=(link,))
    )
    await inter.send("Message Posted", ephemeral=True)


@cmd.sub_command("save")
async def save_config_(inter: CmdInter, path: str = commands.Param("config.toml")):
    """Saves the config to path
    Parameters
    ----------
    path: the path to write to
    """
    Settings.save(path)
    await inter.send(f"Config saved {Emojis.thumbs_up}")


@cmd.sub_command("settings")
async def settings_(inter: CmdInter):
    """Dumps the bot settings"""
    embed = disnake.Embed(
        title="Settings", description=jdumps(Settings.dict(), size=4096)
    )
    await inter.send(embed=embed, ephemeral=True)
    plugin.logger.critical(
        "Settings has been dumped! Please ensure safety of keys and other valuable tokens"
    )


@cmd.sub_command("gifiy")
async def gifiy_(inter: CmdInter, file: disnake.Attachment):
    """Transforms an image to a gif using filenames

    Parameters
    ----------
    file: a png or jpeg to covert
    """
    await inter.response.defer()
    oldfn = file.filename.split(".")[:-1]
    fn = "".join([*oldfn, ".gif"])
    newf = await file.to_file(filename=fn)
    await inter.send("Transformed!", file=newf)


@cmd.sub_command("cached")
async def cached_(inter: CmdInter):
    """Returns all cached messages"""
    await inter.response.defer()
    count = collections.defaultdict(lambda: 0)
    for mess in plugin.bot.cached_messages:
        count[mess.author.id] += 1
    await inter.send(f"```json\n{json.dumps(count,indent=4)}```")


@cmd.sub_command("oauth")
async def oauth_(inter: CmdInter, client_id: str):
    url = disnake.utils.oauth_url(
        client_id=client_id, permissions=disnake.Permissions.all()
    )
    plugin.logger.info(f"oauth url generated for {client_id}; '{url}'")
    await inter.send(url, ephemeral=True)


@cmd.sub_command("timestamp")
async def timestamp_(
    inter: CmdInter,
    timestamp: int,
    format: disnake.utils.TimestampStyle = "f",
):
    """
    Given a unix timestamp, attempts to return a parsed time
    Parameters
    ----------
    timestamp: A unix timestamp
    format: A discord timestamp style
    """
    dt = datetime.fromtimestamp(timestamp)
    await inter.send(disnake.utils.format_dt(dt, style=format))


@cmd.sub_command_group("quote")
async def quote_(inter: CmdInter):
    ...


@quote_.sub_command("add")
async def add_quote_(inter: CmdInter, quote: str):
    """Adds a new quote to the database
    Parameters
    ----------
    quote: a new qoute to add to the database
    """

    q = await Quote(quote=quote).create()
    await inter.send(f"Quote created and Saved\n`{q.id}`")


@quote_.sub_command("random")
async def random_quote_(
    inter: CmdInter,
    count: int = commands.Param(1, description="A number then 7", gt=0, le=7),
):
    """Returns a random qoute from the database
    Parameters
    ----------
    count: a number of quotes between 0 and 7
    """
    await inter.send(await gen_quote())
    if count > 1:
        for _ in range(count - 1):
            await inter.channel.send(await gen_quote())


@quote_.sub_command("remove")
async def remove_quote_(inter: CmdInter, id: UUID):
    """Removes a quote from the database
    Parameters
    ----------
    id: A uuid for the quote
    """
    q = await Quote.find_one(Quote.id == id)
    if not q:
        await inter.send("Quote not found")
        return
    await q.delete()
    await inter.send(f"Quote `{q.id}` deleted")


@quote_.sub_command("search")
async def search_quote_(inter: CmdInter, id: UUID):
    """Finds a quote in the database
    Parameters
    ----------
    id: A uuid for the quote
    """
    q = await Quote.find_one(Quote.id == id)
    if not q:
        await inter.send("404 Quote not found")
        return
    await inter.send(q.quote)


@quote_.sub_command("count")
async def count_quotes_(inter: CmdInter):
    """Counts the amount of quotes in the database"""
    await inter.send(f"I have {await Quote.count()} quotes saved!")


setup, teardown = plugin.create_extension_handlers()
