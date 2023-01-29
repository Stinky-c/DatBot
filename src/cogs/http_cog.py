import disnake
from disnake.ext import commands
from helper import DatBot
from helper import HTTP_CODES, URL
from urllib.parse import unquote


class HTTPCog(commands.Cog):
    CmdInter = disnake.ApplicationCommandInteraction
    name = "http"

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def cog_load(self):
        self.log.debug(f"{self.name} Loading")
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

        if code in HTTP_CODES:
            await inter.send(f"https://http.cat/{code}.jpg")
        else:
            await inter.send("https://http.cat/404.jpg")

    @cmd.sub_command("dog")
    async def dog_(self, inter: CmdInter, code: int):
        """Sends a cog from an HTTP status code
        Parameters
        ----------
        code: an HTTP code
        """

        if code in HTTP_CODES:
            await inter.send(f"https://http.dog/{code}.jpg")
        else:
            await inter.send("https://http.dog/404.jpg")

    @commands.is_owner()
    @cmd.sub_command(name="get")
    async def get_(self, inter: CmdInter, url: URL):
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
