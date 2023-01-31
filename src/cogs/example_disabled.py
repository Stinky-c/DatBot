import disnake
from disnake.ext import commands
from helper import DatBot, CogLoadingFailure, Settings


class ExampleCog(commands.Cog):
    """This is the base cog for creating a new cog"""
    CmdInter = disnake.ApplicationCommandInteraction
    name = "example"
    key_enabled = False

    def __init__(self, bot: DatBot):
        # init logic here
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def cog_load(self):
        # async init logic here
        self.log.debug(f"{self.name} Loading")
        ...

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @cmd.sub_command(name="ping")
    async def ping(self, inter: CmdInter,abc:str):
        """ Placeholder
        Parameters
        ----------
        abc: placeholder
"""
        await inter.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms")


def setup(bot: DatBot):
    if ExampleCog.key_enabled or not Settings.keys.get(ExampleCog.key_loc):
        raise CogLoadingFailure(
            f"Missing `{ExampleCog.key_loc}` api key. Disable or provide key"
        )
    bot.add_cog(ExampleCog(bot))
