from typing import TypeAlias
from urllib.parse import unquote

import disnake
from disnake.ext import commands
from helper import Cog, CogMetaData, DatBot


class HTTPCog(Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "http"

    async def cog_load(self):
        self.client = await self.bot.make_http(self.name)

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @cmd.sub_command("cat")
    async def cat_(self, inter: CmdInter, code: int):
        """Sends a cat from an HTTP status code
        Parameters
        ----------
        code: an HTTP code
        """

        await inter.send(f"https://http.cat/{code}.jpg")

    @cmd.sub_command("dog")
    async def dog_(self, inter: CmdInter, code: int):
        """Sends a cog from an HTTP status code
        Parameters
        ----------
        code: an HTTP code
        """

        await inter.send(f"https://http.dog/{code}.jpg")

    @commands.is_owner()
    @cmd.sub_command(name="get")
    async def get_(self, inter: CmdInter, url: str):
        """using a client, GET's a url
        Parameters
        ----------
        url: a fully qualified URL"""
        async with self.client.get(str(url)) as req:
            await inter.send(req.status)

    @commands.is_owner()
    @cmd.sub_command(name="decode", description="URL decodes a given string")
    async def decode_(self, inter: CmdInter, content: str):
        """url decodes a string
        Parameters
        ----------
        content: a urlencoded string
        """
        await inter.send(unquote(content))


def setup(bot: DatBot):
    bot.add_cog(HTTPCog(bot))


metadata = CogMetaData(
    name=HTTPCog.name,
    key=HTTPCog.key_loc,
    require_key=HTTPCog.key_enabled,
)
