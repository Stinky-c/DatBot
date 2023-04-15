from typing import TypeAlias
import orjson

import disnake
from aiohttp import ClientResponseError
from curse_api import CurseAPI
from curse_api.enums import Games, SortOrder
from curse_api.models import Mod, File
from curse_api.ext import ManifestParser
from disnake.ext import commands, tasks
from disnake.utils import format_dt
from helper import Cog, CogLoadingFailure, DatBot, Settings
from helper.ctypes import AiohttpCurseClient
from helper.emojis import CurseforgeEmojis as Emojis
from helper.models import CurseForgeMod
from helper.views import LinkTuple, LinkView, PaginatorView


class CurseForgeCog(Cog):
    """This is the base cog for creating a new cog"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "curseforge"
    key = "cfcore"

    async def cog_load(self):
        self.log.debug(f"{self.name} Loading")
        conf: dict[str, str] = Settings.keys.get(self.key)
        key = conf.get("key")
        url = conf.get("url")
        # Curse api - API wrapper is a consumer of a client
        http = await self.bot.make_http(
            self.name + "_api",
            headers={
                "X-API-KEY": key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "user-agent": "stinky-c/curse-api",
            },
            base_url=url or "https://api.curseforge.com",
        )
        c2 = AiohttpCurseClient(http)
        self.api = CurseAPI(c2)
        self.parser = ManifestParser(self.api)

        self.http = await self.bot.make_http(self.name + "_webhook")

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @classmethod
    def mod_page_url(cls, mod: Mod) -> str:
        # TODO: add to curse-api
        return (
            f"https://www.curseforge.com/{mod.gameId.name.replace('_','-')}/{mod.category.name.replace('_','-')}/{mod.slug}"
            if mod.category
            else None
        )

    @classmethod
    def embed_from_mod(cls, mod: Mod) -> disnake.Embed:
        embed = (
            disnake.Embed(
                title=mod.name,
                url=cls.mod_page_url(mod),
                description=f"""
                {Emojis.download} {mod.downloadCount:,}
                {Emojis.created} {format_dt(mod.dateCreated)}
                {Emojis.updated} {format_dt(mod.dateModified)}
                {Emojis.uploaded} {format_dt(mod.dateReleased)}

                {mod.summary}""".lstrip(),
                timestamp=disnake.utils.utcnow(),
                color=disnake.Color.random(seed=mod.slug),
            )
            .set_footer(text="Powered by CurseForge")
            .set_image(url=mod.logo.thumbnailUrl)
        )
        return embed

    @classmethod
    def embed_from_file(cls, file: File) -> disnake.Embed:
        # TODO: fix
        embed = disnake.Embed(
            title=file.displayName,
            color=disnake.Color.random(seed=file.id),
            timestamp=disnake.utils.utcnow(),
        ).add_field("API Status", "Available" if file.isAvailable else "Unavailable")
        if f := file.downloadUrl:
            embed.url = f
        return embed

    @classmethod
    def LinkTuples_from_mod(cls, mod: Mod) -> list[LinkTuple]:
        # TODO: add iter method to `BaseCurseModel`
        linkTup = []
        links = mod.links

        if i := links.issuesUrl:
            linkTup.append(LinkTuple("Issues", i))
        if i := links.sourceUrl:
            linkTup.append(LinkTuple("Source", i))
        if i := links.websiteUrl:
            linkTup.append(LinkTuple("Website", i))
        if i := links.wikiUrl:
            linkTup.append(LinkTuple("Wiki", i))

        return linkTup

    @cmd.sub_command("mid")
    async def from_mid(self, inter: CmdInter, mid: str):
        """Fetches a Curse mod/addon from project id

        Parameters
        ----------
        mid: The Id belonging to the mod
        """
        await inter.response.defer()

        try:
            mod = await self.api.get_mod(mid)
        except ClientResponseError as e:
            await self.bot.send_exception(e)
            return await inter.send("An error occured!")
        links = self.LinkTuples_from_mod(mod)
        links.insert(0, LinkTuple("Files", self.mod_page_url(mod) + "/files"))

        await inter.send(
            embed=self.embed_from_mod(mod), view=LinkView(*links)
        )  # `LinkView` should take both iterable and non-iterable

    @cmd.sub_command("search")
    async def from_search(
        self,
        inter: CmdInter,
        slug: str = None,
        search: str = None,
        gameid: int = Games.minecraft.value,
        index: int = 0,
        pagesize: int = 50,
        sortorder: SortOrder = SortOrder.Descending.value
        # game: Games = Games.minecraft,
    ):
        """
        Searches for a mod on curseforge

        Parameters
        ----------
        search: The text filter to search for
        gameid: gameid to filter by
        index: index to start searching at
        pagesize: max page size
        """
        # TODO:
        # add game autocomplete?
        # add index & page
        game = Games(gameid)
        await inter.response.defer()
        try:
            mods, page = await self.api.search_mods(
                game,
                searchFilter=search,
                slug=slug,
                index=index,
                pageSize=pagesize,
                sortOrder=sortorder,
            )
        except ClientResponseError as e:
            await self.bot.send_exception(e)
            return await inter.send("An error occured!")
        count = len(mods)
        if count <= 0:  # ensure mods are found
            return await inter.send("No mods were found")

        view = await PaginatorView.build(
            inter=inter,
            embeds=[self.embed_from_mod(i) for i in mods],
            author=inter.author,
            message="I have found {count} mods to show you\n{current_index}/{count}",
            vars={"count": count - 1},
        )

    @cmd.sub_command("manifest")
    async def from_manifest_(self, inter: CmdInter, manifest: disnake.Attachment):
        data = orjson.loads(await manifest.read())
        try:
            mods = await self.parser.load_mods(data)
        except Exception as e:
            await self.bot.send_exception(e)
            return await inter.send("Invalid manifest")

        count = len(mods)
        if count <= 0:  # ensure mods are found
            return await inter.send("No mods were found")

        view = await PaginatorView.build(
            inter=inter,
            embeds=[self.embed_from_mod(mod) for mod in mods],
            author=inter.author,
            message="{count} files found!\n{current_index}/{count}",
            vars={"count": count - 1},
        )

    # Curseforge Update notifier
    # @cmd.sub_command("create")
    @commands.bot_has_permissions(manage_webhooks=True)
    async def create_(self, inter: CmdInter, channel: disnake.TextChannel, pid: int):
        try:
            mod = await self.api.get_mod(pid)
        except ClientResponseError as e:
            await self.bot.send_exception(e)
            return await inter.send("An error occured!")

        hook = await channel.create_webhook(name="CurseForge Checker")
        fIndex = mod.latestFilesIndexes
        fileId = fIndex[0].fileId if len(fIndex) > 0 else None
        # return await inter.send("No previous files have been uploaded")
        g = await CurseForgeMod(
            hooks=[hook.url], projectId=pid, previous=fileId
        ).create()
        await inter.send(g.id)
        # PID: 520914
        # FID: 4461163

    # @cmd.sub_command("test")
    async def test_(self, inter: CmdInter):
        self.poll_.start()
        await inter.send("Started!")

    # @cmd.sub_command("next")
    async def next_(self, inter: CmdInter):
        if not self.poll_.time:
            return await inter.send("No avaible run times")
        times = "\n".join([disnake.utils.format_dt(i) for i in self.poll_.time])
        await inter.send(times)

    # @tasks.loop(hours=1)
    async def poll_(self):
        data = {i.projectId: i.previous async for i in CurseForgeMod.find_all()}
        self.log.debug(list(data.keys()))
        mods = await self.api.get_mods(list(data.keys()))

        for i in mods:
            if i.latestFilesIndexes[0].fileId != data[i.id]:
                continue
            t = await CurseForgeMod.find_one(CurseForgeMod.projectId == i.id)
            for hook in t.webhooks(self.http):
                embed = self.embed_from_mod(i)
                await hook.send("A new file has been uploaded!", embed=embed)


def setup(bot: DatBot):
    conf: dict | None = Settings.keys.get(CurseForgeCog.key)
    if not conf:
        raise CogLoadingFailure(f"Missing '{CurseForgeCog.key}' key")
    if not conf.get("enabled"):
        return
    bot.add_cog(CurseForgeCog(bot))