import disnake
from disnake.ext import commands
from helper import DatBot, Server, Cog
from typing import TypeAlias


class ModerationCog(Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    MsgInter: TypeAlias = disnake.MessageCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "mod"

    async def cog_load(self):
        self.webhook_http = await self.bot.make_http("mod.webhook")

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        ...

    @cmd.sub_command("ban")
    @commands.has_permissions(ban_members=True)
    async def ban_(
        self,
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

    @commands.message_command(name="Pin Message")
    @commands.guild_only()
    async def pin_message_(
        self,
        inter: MsgInter,
        message: disnake.Message,
    ):
        server = await self.get_server(inter)  # fix injection code

        if not server.pinChannel:
            await inter.send("Server is not properly configured")
            return

        hook = server.pinChannel_webhook(self.webhook_http)
        await hook.send(
            message.content,
            username=message.author.display_name,
            avatar_url=message.author.avatar.url,
        )
        await inter.send("Posted!", ephemeral=True)

    @cmd.sub_command("webhook")
    async def configure_pin_webhook(
        self,
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
                await server.pinChannel_webhook(self.webhook_http).delete(
                    reason="Pin Channel webhook has been moved"
                )
            except disnake.errors.NotFound:  # TODO: find if there are more errors possible
                await inter.send("Preconfigured webhook missing, skipping")
            except Exception:
                await inter.send("Unknown error removing old webhook, skipping")

        hook = await channel.create_webhook(name="Pin Channel Webhook")
        server.pinChannel = hook.url
        await server.save()
        await inter.send(f"A webhook has been configured on {channel.mention}")


def setup(bot: DatBot):
    bot.add_cog(ModerationCog(bot))
