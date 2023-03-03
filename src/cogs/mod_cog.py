import disnake
from disnake.ext import commands
from helper import DatBot
from typing import TypeAlias


class ModerationCog(commands.Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "mod"

    def __init__(self, bot: DatBot):
        self.bot = bot

    async def cog_load(self):
        ...

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

    async def vote_kick_(self, inter: CmdInter, user: disnake.Member):
        # A vote kick
        ...


def setup(bot: DatBot):
    bot.add_cog(ModerationCog(bot))
