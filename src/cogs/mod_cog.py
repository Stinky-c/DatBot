from contextvars import ContextVar
from typing import TypeAlias

import disnake
from disnake.ext import commands, plugins
from helper import CogMetaData, DatBot, LinkTuple, Server, get_server

# Meta
metadata = CogMetaData(
    name="moderation",
    key=None,
    require_key=False,
)
plugin: plugins.Plugin[DatBot] = plugins.Plugin(
    name=metadata.name, logger=f"cog.{metadata.name}"
)


# Aliases
CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
MsgInter: TypeAlias = disnake.MessageCommandInteraction
GuildInter: TypeAlias = disnake.GuildCommandInteraction

# Context Vars
webhookhttp: ContextVar[str] = ContextVar(metadata.name + "message", default="Pong")


@plugin.load_hook()
async def cog_load():
    webhookhttp.set(await plugin.bot.make_http("mod.webhook"))


@plugin.slash_command(name=metadata.name)
async def cmd(inter: CmdInter):
    plugin.logger.debug(f"{inter.author.name} @ {inter.guild.name}")


@cmd.sub_command("ban")
@commands.has_permissions(ban_members=True)
async def ban_(
    inter: CmdInter,
    user: disnake.Member,
    reason: str = "You have been banned.",
    clean_duration: int = 604800,
    ephemeral: bool = False,
):
    """Bans a user
    Parameters
    ----------
    user: a user to ban
    reason: A custom message
    clean_duration: amount of time to clean messages
    ephemeral: hide the response message
    """
    await user.ban(reason, clean_history_duration=clean_duration)
    await inter.send(
        f"'{user.name}' has been banned for '{reason}'", ephemeral=ephemeral
    )


@plugin.message_command(name="Pin Message")
@commands.guild_only()
async def pin_message_(
    inter: MsgInter,
    message: disnake.Message,
):
    server = await get_server(inter)  # fix injection code

    if not server.pinChannel:
        await inter.send("Server is not properly configured")
        return

    hook = server.pinChannel_webhook(webhookhttp.get())
    await hook.send(
        message.content,
        username=message.author.display_name,
        avatar_url=message.author.avatar.url,
        components=(LinkTuple("Source", message.jump_url).as_component(),),
    )
    await inter.send("Posted!", ephemeral=True)


@cmd.sub_command("webhook")
async def configure_pin_webhook(
    inter: CmdInter,
    channel: disnake.TextChannel,
    server: Server,
):
    """
    Configures the servers pin channel using a webhook
    Parameters
    ----------
    channel: The channel messages show be sent to
    """
    if not isinstance(channel, disnake.TextChannel):
        await inter.send("Not a text channel!")
        return

    if server.pinChannel:
        try:
            await server.pinChannel_webhook(webhookhttp.get()).delete(
                reason="Pin Channel webhook has been moved"
            )
        except disnake.errors.NotFound:
            await inter.send("Preconfigured webhook missing, skipping")
        except Exception:
            await inter.send("Unknown error while removing old webhook, skipping")

    hook = await channel.create_webhook(name="Pin Channel Webhook")
    server.pinChannel = hook.url
    await server.save()
    await inter.send(f"A webhook has been configured on {channel.mention}")


setup, teardown = plugin.create_extension_handlers()
