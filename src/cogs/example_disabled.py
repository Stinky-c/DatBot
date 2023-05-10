from typing import TypeAlias

import disnake
from disnake.ext import commands
from helper import Cog, CogMetaData, DatBot


class ExampleCog(Cog):
    """This is the base cog for creating a new cog"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "example"
    key_loc = None
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
        await inter.send(f"Pong! {round(self.bot.latency * 1000)}ms")


def setup(bot: DatBot):
    bot.add_cog(ExampleCog(bot))


metadata = CogMetaData(
    name=ExampleCog.name,
    key=ExampleCog.key_loc,
    require_key=ExampleCog.key_enabled,
)
