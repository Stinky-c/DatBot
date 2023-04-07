import disnake
from disnake.ext import commands
from helper import CogLoadingFailure, DatBot, Settings, Cog
from typing import TypeAlias


class ExampleCog(Cog):
    """This is the base cog for creating a new cog"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "example"
    key_enabled = False

    async def cog_load(self):
        # async init logic here
        self.log.debug(f"{self.name} Loading")
        ...

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @cmd.sub_command(name="ping")
    async def ping(self, inter: CmdInter, abc: str):
        """Placeholder
        Parameters
        ----------
        abc: placeholder"""
        await inter.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms")


def setup(bot: DatBot):
    bot.add_cog(ExampleCog(bot))
