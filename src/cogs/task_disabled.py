import disnake
from disnake.ext import commands
from helper import DatBot, Settings, task
from typing import TypeAlias


class ExampleCog(commands.Cog):
    """This is an example cog powered by a partial decorator `task`"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "task"
    key_enabled = False

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def cog_load(self):
        ...

    @task()
    async def test(self, inter: CmdInter):
        await inter.send("Hello, World!")
        ...

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @cmd.sub_command(name="task")
    async def ping(self, inter: CmdInter):
        """A basic task example"""
        abc = await self.test.start(inter=inter)
        self.log.info(abc)


def setup(bot: DatBot):
    bot.add_cog(ExampleCog(bot))
