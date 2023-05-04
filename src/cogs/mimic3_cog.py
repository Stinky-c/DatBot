import disnake
from disnake.ext import commands
from helper import CogLoadingFailure, DatBot, Settings, Cog
from typing import TypeAlias
from helper.mimic3 import Mimic3Wrapper
from helper import bytes2human


class Mimic3Cog(Cog):
    """This is the base cog for creating a new cog"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "mimic3"
    key_loc = "mimic3"

    async def cog_load(self):
        self.log.debug(f"{self.name} Loading")
        conf: dict = Settings.keys.get(self.key_loc)
        self.api = Mimic3Wrapper(
            await self.bot.make_http(self.name, base_url=conf["url"]),
            lang=conf.get("lang", "en_US"),
            model=conf.get("model", "vctk_low"),
            voice=conf.get("voice", "p376"),
        )

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @cmd.sub_command("speak")
    async def ping(self, inter: CmdInter, text: str):
        """Generates a wav file using the selected voice
        Parameters
        ----------
        text: a body of text to generate"""
        await inter.response.defer()
        buf, blen = await self.api.speak(text)
        await inter.send(
            f"Size: '{bytes2human(blen)}'", file=disnake.File(buf, "output.wav")
        )


def setup(bot: DatBot):
    if not Settings.keys.get(Mimic3Cog.key_loc):
        raise CogLoadingFailure(f"Missing {Mimic3Cog.key_loc} key")

    bot.add_cog(Mimic3Cog(bot))
