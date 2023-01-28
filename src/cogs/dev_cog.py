import disnake
from disnake.ext import commands
from helper import DatBot, Settings, LinkView, LinkTuple, Emojis, gen_quote, UUID
from helper.misc import bytes2human
from helper.views import CogSelectView
from helper.models import Quote
import psutil
import platform as plat


class DevCog(commands.Cog):
    description = "This cog is filled with useful dev commands"
    CmdInter = disnake.ApplicationCommandInteraction
    name = "dev"

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cogs.{self.name}")

    async def cog_load(self) -> None:
        # self.log.debug(f"{self.name} Loading")
        self.httpclient = self.bot.make_http(self.name)

    @commands.is_owner()
    @commands.slash_command(name="dev", guild_ids=Settings.bot.dev_guilds)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")

    @cmd.sub_command(name="close", description="Stops the bot")
    async def stop_(self, inter: CmdInter):
        await inter.send(await gen_quote())
        await self.bot.close()

    @cmd.sub_command(
        name="info",
        description="Returns various system information",
    )
    async def info_(self, inter: CmdInter):

        vmem = psutil.virtual_memory()
        duse = psutil.disk_usage("/")
        pexe = psutil.Process()
        embed_dict = {
            "color": disnake.Color(0x9B42F5),
            "timestamp": disnake.utils.utcnow().isoformat(),
            "author": {
                "name": "System Status",
                "icon_url": self.bot.user.display_avatar.url,
            },
            "fields": [
                {"name": "OS", "value": plat.system(), "inline": True},
                {
                    "name": "CPU Times",
                    "value": f"Current: {psutil.cpu_percent(0.1)}%",
                    "inline": True,
                },
                {
                    "name": "Memory Usage",
                    "value": f"{bytes2human(vmem.used)}MB/{bytes2human(vmem.available)}",
                    "inline": True,
                },
                {
                    "name": "Disk Usage",
                    "value": f"{bytes2human(duse.used)}MB/{bytes2human(duse.total)}",
                    "inline": True,
                },
                {
                    "name": "Bot Uptime",
                    "value": disnake.utils.format_dt(pexe.create_time(), "R"),
                    "inline": True,
                },
                {
                    "name": "Uptime",
                    "value": disnake.utils.format_dt(psutil.boot_time(), "R"),
                    "inline": True,
                },
            ],
        }
        await inter.send(embed=disnake.Embed.from_dict(embed_dict))

    @cmd.sub_command(name="cog", description="Returns a UI for changing cog settings")
    async def cSettings_(self, inter: CmdInter):
        # TODO: cog settings
        await inter.send(view=CogSelectView(), ephemeral=True)
        ...

    @cmd.sub_command(name="unload", description="unloads a cog from the bot")
    async def unload_(
        self, inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)
    ):
        self.bot.unload_extension(cog)
        Settings.bot.cogs.remove(cog)
        await inter.send(f"`{cog}` has been unloaded {Emojis.thumbs_up.value}")

    @cmd.sub_command(name="load", description="loads a cog from the bot")
    async def load_(
        self, inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)
    ):
        self.bot.load_extension(cog)
        await inter.send(f"`{cog}` has been loaded {Emojis.thumbs_up.value}")

    @cmd.sub_command(name="adddev")
    async def add_dev_(self, inter: CmdInter, id: disnake.Guild):
        if g := self.bot.get_guild(id):
            self.cmd.guild_ids.appened(id)
            await inter.send(f"Added '{g.name}' to the dev servers")
        else:
            await inter.send("Failed to add that server to my lists")

    @cmd.sub_command(name="toggle")
    async def toggle_(self, inter: CmdInter):
        self.bot.reload = not self.bot.reload
        await inter.send(f"Bot reload has been toggled\nStatus: `{self.bot.reload}`")

    @cmd.sub_command(name="embed")
    async def emebed_img_(
        self,
        inter: CmdInter,
        file: disnake.Attachment,
        url: str,
        message: str,
    ):
        await inter.response.defer()
        link = LinkTuple("Click Here!", url)
        await inter.channel.send(
            message, file=await file.to_file(), view=LinkView(links=(link,))
        )
        await inter.send("Message Posted", ephemeral=True)

    @cmd.sub_command(name="save")
    async def save_config_(
        self, inter: CmdInter, path: str = commands.Param("config.toml")
    ):
        Settings.save(path)
        await inter.send(f"Config saved {Emojis.thumbs_up.value}")

    @cmd.sub_command(
        name="iseven",
        description="Uses the Is Even api to test whether an number is even",
    )
    async def iseven_(self, inter: CmdInter, number: commands.LargeInt):
        url = f"https://api.isevenapi.xyz/api/iseven/{number}/"
        async with self.httpclient.get(url) as res:
            json: dict = await res.json()

        embed_dict = {
            "color": disnake.Color.random(),
            "timestamp": disnake.utils.utcnow().isoformat(),
            "author": {
                "name": inter.author.display_name,
                "icon_url": inter.author.avatar.url,
            },
            "title": f"Is {number} Even?",
            "fields": [
                {
                    "inline": False,
                    "name": "Advertisement",
                    "value": "HONDA CIVIC ...9-555-6289",
                },
                {
                    "inline": False,
                    "name": f"Is {number} Even?",
                    "value": json["iseven"],
                },
            ],
            "footer": {"text": url},
        }
        embed = disnake.Embed.from_dict(embed_dict)
        await inter.send(embed=embed)
        pass

    @cmd.sub_command(
        name="gifiy", description="Transforms an image to a gif using filenames"
    )
    async def gifiy_(self, inter: CmdInter, file: disnake.Attachment):
        await inter.response.defer()
        oldfn = file.filename.split(".")[:-1]
        fn = "".join([*oldfn, ".gif"])
        newf = await file.to_file(filename=fn)
        await inter.send("Transformed!", file=newf)
        ...

    @commands.is_owner()
    # @commands.message_command(name="get")
    async def get_message_(self, inter: CmdInter, message: disnake.Message):
        """find a way to get raw message content"""
        await inter.send(
            f"```{disnake.utils.escape_markdown(message.clean_content)}```"
        )

    @cmd.sub_command_group(name="quote")
    async def quote_(self, inter: CmdInter):
        ...

    @quote_.sub_command(name="add", description="Adds a new quote to the database")
    async def add_quote_(self, inter: CmdInter, quote: str):
        # TODO maybe add tags?
        q = await Quote(quote=quote).create()
        await inter.send(f"Quote created and Saved\n`{q.id}`")

    @quote_.sub_command(name="random", description="Returns a random quote")
    async def random_quote_(
        self,
        inter: CmdInter,
        count: int = commands.Param(1, description="A number then 7", gt=0, le=7),
    ):
        await inter.send(await gen_quote())
        if count > 1:
            for _ in range(count - 1):
                await inter.channel.send(await gen_quote())

    @quote_.sub_command(name="remove", description="Removes a quote. Requires the UUID")
    async def remove_quote_(self, inter: CmdInter, id: UUID):
        q = await Quote.find_one(Quote.id == id)
        if not q:
            await inter.send("Quote not found")
            return
        await q.delete()
        await inter.send(f"Quote `{q.id}` deleted")

    @quote_.sub_command(name="search", description="Finds a quote from a given UUID")
    async def search_quote_(self, inter: CmdInter, id: UUID):
        q = await Quote.find_one(Quote.id == id)
        if not q:
            await inter.send("404 Quote not found")
            return
        await inter.send(q.quote)

    @quote_.sub_command(name="count", description="Returns the amount of quotes")
    async def count_quotes_(self, inter: CmdInter):
        await inter.send(f"I have {await Quote.count()} quotes saved!")


def setup(bot: DatBot):
    bot.add_cog(DevCog(bot))
