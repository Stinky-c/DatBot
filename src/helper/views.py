# from __future__ import annotations
import disnake
from disnake import ui

# from disnake.ext import commands
from disnake import ButtonStyle

from helper.misc import variadic, cogs_status
from helper.ctypes import LinkTuple

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


class CogSettingsView(ui.View):
    def __init__(self, data: str, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.name_, self.status_, self.path_ = data.split(":")

    @ui.button(style=ButtonStyle.red, label="Unload Cog")
    async def unload_(self, button: Button, message: MesInter):
        # TODO
        ...

    @ui.button(style=ButtonStyle.green, label="Load Cog")
    async def load_(self, button: Button, message: MesInter):
        # TODO
        ...


class CogSelectView(ui.View):
    """Lists out all cogs for selection"""

    def __init__(self, *, timeout: Optional[float] = 180):
        super().__init__(timeout=timeout)
        self.cogs = cogs_status()
        for cog in self.cogs:
            self.pick_cog.add_option(
                label=f"{cog['logic_name']}:{cog['status']}",
                value=f"{cog['logic_name']}:{cog['status']}:{cog['path']}",
            )

    @ui.string_select()
    async def pick_cog(self, string_inter: ui.StringSelect, message: MesInter):
        name, status, path = string_inter.values[0].split(":")

        embed_dict = {
            "fields": [
                {"name": "Logic Name", "value": name},
                {"name": "Path", "value": path},
                {
                    "name": "Status",
                    "value": "Enabled" if status == "True" else "Disabled",
                },
            ]
        }
        await message.send(
            embed=disnake.Embed.from_dict(embed_dict),
            ephemeral=True,
            view=CogSettingsView(data=string_inter.values[0]),
        )


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
