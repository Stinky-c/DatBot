import re
from typing import TypeAlias

import disnake
from disnake.ext import commands
from helper import CogMetaData, DatBot, Settings
from helper.csettings import SnekboxConfig


class SnekBoxCog(commands.Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "snekbox"
    key_enabled = True
    key_loc = "snekbox"

    FORMATTED_CODE_REGEX = re.compile(
        # https://github.com/onerandomusername/monty-python/blob/94c303cc994976739de6bc5465eaacbfc5e7f86e/monty/exts/eval/__init__.py#L30
        r"(?P<delim>(?P<block>```)|``?)"
        r"(?(block)(?:(?P<lang>[a-z]+)\n)?)"
        r"(?:[ \t]*\n)*"
        r"(?P<code>.*?)"
        r"\s*"
        r"(?P=delim)",
        re.DOTALL | re.IGNORECASE,
    )

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def cog_load(self):
        snekconfig: SnekboxConfig = Settings.keys.get(self.key_loc, SnekboxConfig)

        snekbox_headers = {"User-Agent": "github.com/stinky-c"}
        if auth := snekconfig.auth:
            snekbox_headers["Authorization"] = auth

        self.client = await self.bot.make_http(
            self.name, base_url=snekconfig.url, headers=snekbox_headers
        )

    async def snek_eval(self, code: str) -> dict:
        async with self.client.post(
            "/eval", data={"input": code}, timeout=10, raise_for_status=True
        ) as res:
            return await res.json()

    @commands.message_command(name="Eval")
    async def eval_block(self, inter: CmdInter, message: disnake.Message):
        if code := self.prepare_input(message.content):
            await inter.response.defer()
            for i in code:
                fin = await self.snek_eval(i)
                await inter.send(self.prepare_response(fin))
        else:
            await inter.send("I don't understand that code")

    def prepare_input(
        self, message: str, *, require_fenced: bool = False
    ) -> list[str] | None:
        code = []
        for i in self.FORMATTED_CODE_REGEX.finditer(message):
            if i.group("lang") in ("py", "python"):
                code += [i.group("code")]
        return code if code else None

    def prepare_response(self, data: dict):
        returnCodes = {0: "Success", 1: "Failure"}
        status = returnCodes.get(data["returncode"], "Unknown")
        return f"Status: {status}\n```\n{data['stdout'][:1970]}\n```"


def setup(bot: DatBot):
    bot.add_cog(SnekBoxCog(bot))


metadata = CogMetaData(
    name=SnekBoxCog.name,
    key=SnekBoxCog.key_loc,
    require_key=SnekBoxCog.key_enabled,
)
