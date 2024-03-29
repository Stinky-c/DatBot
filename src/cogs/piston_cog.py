import re
from typing import TypeAlias

import disnake
from disnake.ext import commands
from helper import Cog, CogMetaData, DatBot, Settings
from helper.csettings import PistonConfig
from helper.models import PistonEvalResponse

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


class PistonCog(Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "piston"
    key_loc = "piston"
    key_enabled = True

    async def cog_load(self):
        self.conf: PistonConfig = Settings.keys.get(self.key_loc, PistonConfig)
        base_url = self.conf.url
        self.client = await self.bot.make_http(self.name, base_url=base_url)
        self.runtimes = await self.runtimes_piston()

    async def eval_piston(
        self,
        code: str,
        lang: str,
        version: str,
        compile_timeout: int = 10000,
        run_timeout: int = 5000,
    ) -> PistonEvalResponse:
        data = {
            "language": lang,
            "version": version,
            "files": [{"content": code}],
            "compile_timeout": compile_timeout,
            "run_timeout": run_timeout,
            # "compile_memory_limit": compile_memory_limit,
            # "run_memory_limit": run_memory_limit,
        }
        async with self.client.post("/api/v2/piston/execute", data=data) as res:
            d = await res.json()
            res.raise_for_status()
            return PistonEvalResponse.parse_obj(d)

    async def runtimes_piston(self) -> dict[str, tuple]:
        async with self.client.get("/api/v2/piston/runtimes") as res:
            res.raise_for_status()
            data: list[dict] = await res.json()
            runtimes = {
                i.get("language"): (i.get("language"), i.get("version")) for i in data
            }
            for i in data:
                for o in i.get("aliases"):
                    runtimes[o] = (i.get("language"), i.get("version"))
        return runtimes

    @commands.message_command(name="piston")
    async def eval_(self, inter: CmdInter, message: disnake.Message):
        for i in FORMATTED_CODE_REGEX.finditer(message.content):
            await inter.response.defer()
            lang, version = self.runtimes[i.group("lang")]
            code = i.group("code")
            evalJob = await self.eval_piston(code, lang, version)
            await inter.send(evalJob.compile.stdout)


def setup(bot: DatBot):
    bot.add_cog(PistonCog(bot))


metadata = CogMetaData(
    name=PistonCog.name,
    key=PistonCog.key_loc,
    require_key=PistonCog.key_enabled,
)
