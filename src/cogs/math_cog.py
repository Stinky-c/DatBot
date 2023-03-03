import ast
import math
import operator as op
import re
from typing import Callable, Literal, TypeAlias

import disnake
from disnake.ext import commands
from helper import DatBot
from helper.errors import InvalidStatment, MathError, NotAFunction
from data.math import help_message

math_op = {
    ast.USub: op.neg,
    # Basic math
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.FloorDiv: op.floordiv,
    ast.Mod: op.mod,
    # Functions
    ast.Call: {
        "log10": math.log10,
        "log": math.log,
        "ln": math.log,
        "sqrt": math.sqrt,
        "cos": math.cos,
        "sin": math.sin,
        "tan": math.tan,
        "rad": math.radians,
        "deg": math.degrees,
        "gcd": math.gcd,
        "lcm": math.lcm,
        "round": round,
    },
}

bit_op = {
    ast.USub: op.neg,
    # basic math
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.FloorDiv: op.floordiv,
    ast.Pow: op.pow,
    # bitwise
    ast.BitAnd: op.and_,
    ast.BitOr: op.or_,
    ast.BitXor: op.xor,
    ast.Invert: op.invert,  # https://docs.python.org/3/library/ast.html#ast.Invert
    ast.LShift: op.lshift,
    ast.RShift: op.rshift,
}

op_table = {
    "?": math_op,
    "b": bit_op,
    "m": math_op,
}


# TODO: support basic functions like
# log, abs, and sqrt
class MathCog(commands.Cog):
    """This is the base cog for creating a new cog"""

    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "math"
    key_enabled = False

    reg = re.compile(r"`(?P<statement>[^`]+)`\?(?P<key>[a-z\?])")

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def cog_load(self):
        self.log.debug(f"{self.name} Loading")

    def eval_expr(self, expr: str, op_map: dict = math_op):
        """Evals expr using the operation map"""
        return self.eval_(ast.parse(expr, mode="eval").body, op_map)

    def eval_(self, node, op_map: dict):
        if isinstance(node, ast.Num):  # <number>
            return node.n
        elif isinstance(node, ast.BinOp):  # <left> <operator> <right>
            return op_map[type(node.op)](
                self.eval_(node.left, op_map), self.eval_(node.right, op_map)
            )
        elif isinstance(node, ast.UnaryOp):  # <operator> <operand> e.g., -1
            return op_map[type(node.op)](self.eval_(node.operand, op_map))
        elif isinstance(node, ast.Call):
            a: Callable | None = op_map[type(node)].get(node.func.id)
            if a is None:
                raise NotAFunction
            return a(
                *[self.eval_(i, op_map) for i in node.args],
                **{o.arg: self.eval_(o, op_map) for o in node.keywords},
            )

        else:
            return "Invalid expression"

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        """Shows the help message"""  # TODO:
        embed_dict = {
            "title": "Math Help",
            "timestamp": disnake.utils.utcnow().isoformat(),
            "description": help_message,
            "color": disnake.Color.random(),
        }
        await inter.send(
            "To get started post a math equation in the form of `` `<math>`??`` to evaulate\n please note some major changes",
            embed=disnake.Embed.from_dict(embed_dict),
        )

    @commands.Cog.listener(disnake.Event.message)
    async def on_message(self, message: disnake.Message):
        content = message.content
        if message.author.bot:
            # I want to enable bots to use this
            # chat relays should be able to use this
            return

        if not self.reg.search(content):
            return

        for matched in self.reg.finditer(content):
            statement = matched.group("statement")

            # op_map = op_table[matched.group("key")]
            op_map = math_op
            try:
                solved = self.eval_expr(statement, op_map)
            except NotAFunction:
                return await message.reply("Unknown Functions", mention_author=False)
            except SyntaxError:
                return await message.reply("Failed to parse", mention_author=False)

            except MathError:
                return await message.reply(
                    "An unknown error occured", mention_author=False
                )
            else:
                await message.reply(
                    f"Statement evaluated: `{solved}`", mention_author=False
                )


def setup(bot: DatBot):
    bot.add_cog(MathCog(bot))
