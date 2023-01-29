# from __future__ import annotations
import disnake
from disnake import ui

# from disnake.ext import commands
from disnake import ButtonStyle

from .misc import variadic
from .ctypes import LinkTuple
from .cbot import DatBot
from .emojis import Emojis

from typing import Optional


Button = disnake.ui.Button
MesInter = disnake.MessageInteraction


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
                disnake.ui.Button(
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
    async def unload_(self, button: Button, message: MesInter):
        await message.response.defer()
        self.bot.unload_extension(self.cog)
        await message.send(f"`{self.cog}` unloaded", delete_after=4.0)

    @ui.button(style=ButtonStyle.green, label="Load Cog")
    async def load_(self, button: Button, message: MesInter):
        await message.response.defer()
        self.bot.load_extension(self.cog)
        await message.send(f"`{self.cog}` loaded", delete_after=4.0)

    @ui.button(style=ButtonStyle.red, label="Close", emoji=Emojis.cross.value)
    async def remove_(self, button: Button, message: MesInter):
        await self.message.delete()


# TODO test
"""
class PaginatorView(ui.View):
    def __init__(
        self, embeds: list[disnake.Embed], message: disnake.Message, inter, timeout=None
    ):
        super().__init__(timeout=timeout)
        if not isinstance(embeds, (list, tuple)) or len(embeds) <= 0:
            raise Exception("")
        self.embeds = embeds
        self.message = message
        self.inter = inter
        self.current_index = 0
        # self.refresh()

    def refresh(self):
        embed = self.embeds[self.current_index]
        for item in self.children:
            if isinstance(item, disnake.Embed):
                self.remove_item(item)
        self.message.edit(embed=embed)

    @ui.button(emoji="⬅️", style=ButtonStyle.blurple)
    async def previous(self, button: Button, inter: MesInter):
        if self.current_index == 0:
            self.current_index = len(self.embeds) - 1
        else:
            self.current_index -= 1
        self.refresh()
        await inter.response.edit_message(embed=self)

    @ui.button(emoji="➡️", style=ButtonStyle.blurple)
    async def next(self, button: Button, inter: MesInter):
        if self.current_index == len(self.embeds) - 1:
            self.current_index = 0
        else:
            self.current_index += 1
        self.refresh()
        await inter.response.edit_message(view=self)


"""
