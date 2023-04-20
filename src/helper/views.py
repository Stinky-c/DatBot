from typing import Optional, TypeAlias

import disnake

# from disnake.ext import commands
from disnake import ButtonStyle, ui

from .cbot import DatBot
from .ctypes import LinkTuple
from .emojis import Emojis
from .misc import variadic

MesInter: TypeAlias = disnake.MessageInteraction
CmdInter: TypeAlias = disnake.ApplicationCommandInteraction


class BaseView(ui.View):
    async def on_timeout(self) -> None:
        for child in self.children:
            child.disabled = True


class LinkView(ui.View):
    """
    Accpets `tuple[LinkTuple]`
    builds a link view
    """

    def __init__(self, *links: LinkTuple):
        super().__init__(timeout=0)
        links = variadic(links)
        for i in links:
            self.add_item(
                ui.Button(
                    label=i.label,
                    url=i.url,
                    emoji=i.emjoi,
                    style=ButtonStyle.link,
                )
            )


class CogSettingsView(BaseView):
    def __init__(
        self,
        *,
        message: disnake.InteractionMessage,
        cog: str,
        bot: DatBot,
        timeout: Optional[float] = 180,
    ):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.message = message
        self.cog = cog

    @property
    def get_cog(self):
        return self.bot.get_cog(self.cog)

    @ui.button(style=ButtonStyle.red, label="Unload Cog")
    async def unload_(self, button: ui.Button, message: MesInter):
        await message.response.defer()
        self.bot.unload_extension(self.cog)
        await message.send(f"`{self.cog}` unloaded", delete_after=4.0)

    @ui.button(style=ButtonStyle.green, label="Load Cog")
    async def load_(self, button: ui.Button, message: MesInter):
        await message.response.defer()
        self.bot.load_extension(self.cog)
        await message.send(f"`{self.cog}` loaded", delete_after=4.0)

    @ui.button(style=ButtonStyle.red, label="Close", emoji=Emojis.cross)
    async def remove_(self, button: ui.Button, message: MesInter):
        await self.message.delete()


class PaginatorView(BaseView):
    inter: TypeAlias = disnake.InteractionMessage

    def __init__(
        self,
        embeds: list[disnake.Embed],
        author: disnake.User | disnake.Member,
        message: str,
        vars: dict,
        timeout: int = 180,
    ):
        super().__init__(timeout=timeout)
        if not isinstance(embeds, (list, tuple)) or len(embeds) <= 0:
            raise Exception("Did not receive a list or tuple!")
        self.embeds = embeds
        self.current_index = 0
        self.author = author
        self.deletable = False  # ensures 2 clicks are required to delete
        self.message = message
        self.vars = vars

    async def update(self):
        embed = self.embeds[self.current_index]
        for item in self.children:
            if isinstance(item, disnake.Embed):
                self.remove_item(item)
        # update varibles for message
        self.vars.update(
            {
                "current_index": self.current_index,
                "offset_index": self.current_index + 1,
            }
        )

        await self.inter.edit(content=self.message.format(**self.vars), embed=embed)

    @ui.button(emoji=Emojis.arrow_left, style=ButtonStyle.blurple)
    async def previous(self, button: ui.Button, inter: MesInter):
        if inter.author != self.author:
            return await inter.send("You're not allowed to use this!", delete_after=5)

        if self.current_index == 0:
            self.current_index = len(self.embeds) - 1
        else:
            self.current_index -= 1

        await inter.send("Previous page", ephemeral=True, delete_after=1)
        await self.update()

    @ui.button(emoji=Emojis.x, style=ButtonStyle.danger)
    async def delete_embed(self, button: ui.Button, inter: MesInter):
        if inter.author != self.author:
            return await inter.send("You're not allowed to use this!", delete_after=5)

        if not self.deletable:
            await inter.send(
                "Click me again to delete!", ephemeral=True, delete_after=5
            )
            self.deletable = True
            return
        else:
            await inter.send("Deleting!", delete_after=5.0)
            await self.inter.delete(delay=5)

    @ui.button(emoji=Emojis.arrow_right, style=ButtonStyle.blurple)
    async def next(self, button: ui.Button, inter: MesInter):
        if inter.author != self.author:
            return await inter.send("You're not allowed to use this!", delete_after=5)

        if self.current_index == len(self.embeds) - 1:
            self.current_index = 0
        else:
            self.current_index += 1

        await inter.send("Next Page", ephemeral=True, delete_after=1)
        await self.update()

    @classmethod
    async def build(
        cls,
        inter: CmdInter,
        embeds: list[disnake.Embed],
        author: disnake.User | disnake.Member,
        vars: dict,
        message: str = "{offset_index}/{count}",
        timeout: int = 180,
    ):
        """
        Builds the view, running other required steps after creation
        Parameters
        ----------
        inter: Interaction
        embeds: A list of embeds to cycle through
        author: Author object to bind button clicks to
        message: The message to send with an embed
        vars: Varibles to add for message usage
        timeout: when view timesout
        """
        view = cls(
            embeds=embeds,
            author=author,
            message=message,
            vars=vars,
            timeout=timeout,
        )

        await inter.send(view=view)
        view.inter = await inter.original_response()
        await view.update()
        return view
