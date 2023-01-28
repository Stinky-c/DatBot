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
        self.client = self.bot.make_http(self.name)

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @cmd.sub_command(
        name="cat", description="Sends a cat based on a given HTTP status code"
    )
    async def cat_(self, inter: CmdInter, code: int):
        if code in HTTP_CODES:
            await inter.send(f"https://http.cat/{code}.jpg")
        else:
            await inter.send("https://http.cat/404.jpg")

    @cmd.sub_command(
        name="dog", description="Sends a dog based on a given HTTP status code"
    )
    async def dog_(self, inter: CmdInter, code: int):
        if code in HTTP_CODES:
            await inter.send(f"https://http.dog/{code}.jpg")
        else:
            await inter.send("https://http.dog/404.jpg")

    @commands.is_owner()
    @cmd.sub_command(name="get")
    async def get_(self, inter: CmdInter, url: URL):
        async with self.client.get(str(url)) as req:
            await inter.send(req.status)

    @commands.is_owner()
    @cmd.sub_command(name="decode", description="URL decodes a given string")
    async def decode_(
        self,
        inter: CmdInter,
        content: str,
    ):
        await inter.send(unquote(content))


def setup(bot: DatBot):
    bot.add_cog(HTTPCog(bot))
