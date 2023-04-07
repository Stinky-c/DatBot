from typing import TypeAlias

import disnake
from aiohttp import ClientResponseError
from curse_api import CurseAPI
from curse_api.models import Mod
from curse_api.enums import Games, SortOrder
from disnake.ext import commands
from disnake.utils import format_dt
from helper import Cog, CogLoadingFailure, DatBot, Settings
from helper.ctypes import AiohttpCurseClient
from helper.views import PaginatorView, LinkView, LinkTuple
from helper.emojis import CurseforgeEmojis as Emojis


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

        http = await self.bot.make_http(
            self.name,
            headers={
                "X-API-KEY": key,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "user-agent": "stinky-c/curse-api",
            },
            base_url=url or "https://api.curseforge.com",
        )
        s2 = AiohttpCurseClient(http)
        self.api = CurseAPI(s2)

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        self.log.debug(f"{inter.author.name} @ {inter.guild.name}")

    @classmethod
    def mod_page_url(cls, mod: Mod) -> str:
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
                description=f"{Emojis.download} {mod.downloadCount:,}\n{Emojis.created} {format_dt(mod.dateCreated)}\n{Emojis.updated} {format_dt(mod.dateModified)}\n{Emojis.uploaded} {format_dt(mod.dateReleased)}\n\n{mod.summary}",
                timestamp=disnake.utils.utcnow(),
                color=disnake.Color.random(seed=mod.slug),
            )
            .set_footer(text="Powered by CurseForge")
            .set_image(url=mod.logo.thumbnailUrl)
        )
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

        view = PaginatorView(
            [self.embed_from_mod(i) for i in mods],
            author=inter.author,
            message="I have found {count} mods to show you\n{current_index}/{count}",
            vars={"count": count - 1},
        )
        await inter.send(view=view)
        view.inter = await inter.original_response()
        await view.update()


def setup(bot: DatBot):
    conf: dict | None = Settings.keys.get(CurseForgeCog.key)
    if not conf:
        raise CogLoadingFailure(f"Missing '{CurseForgeCog.key}' key")
    if not conf.get("enabled"):
        return
    bot.add_cog(CurseForgeCog(bot))
