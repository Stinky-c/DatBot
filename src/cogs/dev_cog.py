import collections
import json
import platform as plat

import disnake
import psutil
from disnake.ext import commands
from helper import (
    UUID,
    DatBot,
    Emojis,
    LinkTuple,
    LinkView,
    Settings,
    gen_quote,
    jdumps,
    bytes2human,
)
from helper.models import Quote
from helper.views import CogSettingsView


class DevCog(commands.Cog):
    description = "This cog is filled with useful dev commands"
    CmdInter = disnake.ApplicationCommandInteraction
    name = "dev"

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def cog_load(self) -> None:
        self.httpclient = await self.bot.make_http(self.name)

    @commands.is_owner()
    @commands.slash_command(name="dev", guild_ids=Settings.bot.dev_guilds)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")

    @cmd.sub_command("close")
    async def stop_(self, inter: CmdInter):
        """Stops the bot"""
        await inter.send(await gen_quote())
        await self.bot.close()

    @cmd.sub_command("info")
    async def info_(self, inter: CmdInter):
        """Returns various system information"""

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

    @cmd.sub_command("cog")
    async def cSettings_(
        self, inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)
    ):
        """Returns a UI for changing cog settings"""
        await inter.response.defer()
        view = CogSettingsView(
            bot=self.bot, message=await inter.original_response(), cog=cog
        )
        await inter.send(f"Configure `{cog}`", view=view, ephemeral=True)

    @cmd.sub_command("unload")
    async def unload_(
        self, inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)
    ):
        """unloads a cog from the bot

        Parameters
        ----------
        cog: The cog path to unload
        """
        self.bot.unload_extension(cog)
        Settings.bot.cogs.remove(cog)
        await inter.send(f"`{cog}` has been unloaded {Emojis.thumbs_up}")

    @cmd.sub_command("load")
    async def load_(
        self, inter: CmdInter, cog: str = commands.Param(choices=Settings.bot.cogs)
    ):
        """loads a cog from the bot

        Parameters
        ----------
        cog: The cog path to unload
        """
        self.bot.load_extension(cog)
        await inter.send(f"`{cog}` has been loaded {Emojis.thumbs_up}")

    @cmd.sub_command("adddev")
    async def add_dev_(self, inter: CmdInter, id: disnake.Guild):
        """adds a new guild to the dev group"""
        if g := self.bot.get_guild(id):
            self.cmd.guild_ids.appened(id)
            await inter.send(f"Added '{g.name}' to the dev servers")
        else:
            await inter.send("Failed to add that server to my lists")

    @cmd.sub_command("embed")
    async def emebed_img_(
        self,
        inter: CmdInter,
        file: disnake.Attachment,
        url: str,
        message: str,
    ):
        """

        Parameters
        ----------
        file: An image to add
        url: A url to add
        message: The message to add
        """
        await inter.response.defer()
        link = LinkTuple("Click Here!", url)
        await inter.channel.send(
            message, file=await file.to_file(), view=LinkView(links=(link,))
        )
        await inter.send("Message Posted", ephemeral=True)

    @cmd.sub_command("save")
    async def save_config_(
        self, inter: CmdInter, path: str = commands.Param("config.toml")
    ):
        """Saves the config to path
        Parameters
        ----------
        path: the path to write to
        """
        Settings.save(path)
        await inter.send(f"Config saved {Emojis.thumbs_up}")

    @cmd.sub_command("settings")
    async def settings_(self, inter: CmdInter):
        await inter.send(jdumps(Settings.dict()), ephemeral=True)
        self.log.critical(
            "Settings has been dumped! Please ensure safety of keys and other valuable tokens"
        )

    @cmd.sub_command("iseven")
    async def iseven_(self, inter: CmdInter, number: commands.LargeInt):
        """Uses the Is Even api to test whether an number is even
        Parameters
        ----------
        number: A number to check if is even
        """
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

    @cmd.sub_command("gifiy")
    async def gifiy_(self, inter: CmdInter, file: disnake.Attachment):
        """Transforms an image to a gif using filenames

        Parameters
        ----------
        file: a png or jpeg to covert
        """
        await inter.response.defer()
        oldfn = file.filename.split(".")[:-1]
        fn = "".join([*oldfn, ".gif"])
        newf = await file.to_file(filename=fn)
        await inter.send("Transformed!", file=newf)

    @cmd.sub_command("cached")
    async def cached_(self, inter: CmdInter):
        """Returns all cached messages"""
        await inter.response.defer()
        count = collections.defaultdict(lambda: 0)
        for mess in self.bot.cached_messages:
            count[mess.author.id] += 1
        await inter.send(f"```json\n{json.dumps(count,indent=4)}```")

    @cmd.sub_command("status")
    async def status_(self, inter: CmdInter):
        """Checks discord status and returns the state"""
        # TODO: make it look nicer
        url = "https://discordstatus.com/api/v2/status.json"
        async with self.httpclient.get(url) as req:
            if req.status != 200:
                return await inter.send("Discord Status page returned a non 200")
            data: dict = await req.json()
            embed = {
                "title": "Discord Status",
                "description": data["status"]["description"],
                "color": 0x2ECC71
                if data["status"]["indicator"] == "none"
                else 0xE74C3C,
            }
            return await inter.send(embed=disnake.Embed.from_dict(embed))

    @cmd.sub_command_group("quote")
    async def quote_(self, inter: CmdInter):
        ...

    @quote_.sub_command("add")
    async def add_quote_(self, inter: CmdInter, quote: str):
        """Adds a new quote to the database
        Parameters
        ----------
        quote: a new qoute to add to the database
        """

        # TODO maybe add tags?
        q = await Quote(quote=quote).create()
        await inter.send(f"Quote created and Saved\n`{q.id}`")

    @quote_.sub_command("random")
    async def random_quote_(
        self,
        inter: CmdInter,
        count: int = commands.Param(1, description="A number then 7", gt=0, le=7),
    ):
        """Returns a random qoute from the database
        Parameters
        ----------
        count: a number of quotes between 0 and 7
        """
        await inter.send(await gen_quote())
        if count > 1:
            for _ in range(count - 1):
                await inter.channel.send(await gen_quote())

    @quote_.sub_command("remove")
    async def remove_quote_(self, inter: CmdInter, id: UUID):
        """Removes a quote from the database
        Parameters
        ----------
        id: A uuid for the quote
        """
        q = await Quote.find_one(Quote.id == id)
        if not q:
            await inter.send("Quote not found")
            return
        await q.delete()
        await inter.send(f"Quote `{q.id}` deleted")

    @quote_.sub_command("search")
    async def search_quote_(self, inter: CmdInter, id: UUID):
        """Finds a quote in the database
        Parameters
        ----------
        id: A uuid for the quote
        """
        q = await Quote.find_one(Quote.id == id)
        if not q:
            await inter.send("404 Quote not found")
            return
        await inter.send(q.quote)

    @quote_.sub_command("count")
    async def count_quotes_(self, inter: CmdInter):
        """Counts the amount of quotes in the database"""
        await inter.send(f"I have {await Quote.count()} quotes saved!")


def setup(bot: DatBot):
    bot.add_cog(DevCog(bot))
