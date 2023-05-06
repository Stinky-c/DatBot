import collections
from typing import Any
from uuid import uuid4

import orjson
from pydantic.json import pydantic_encoder

from .models import Quote


def variadic(x: Any, allowed_types=(str, bytes, dict)):
    """Converts item to a tuple if not iterable or not in allowed types"""
    return (
        x
        if isinstance(x, collections.abc.Iterable) and not isinstance(x, allowed_types)
        else (x,)
    )


def bytes2human(n: int) -> str:
    """Converts int to bytes size"""
    symbols = ("K", "M", "G", "T", "P", "E", "Z", "Y")
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = float(n) / prefix[s]
            return "%.1f%s" % (value, s)
    return "%sB" % n


async def gen_quote() -> str:
    """pulls a random quote from the database"""
    return (await Quote.aggregate([{"$sample": {"size": 1}}], Quote).to_list())[0].quote


def jdumps(obj: Any, size: int = 2000, json_encoder=pydantic_encoder) -> str:
    """Dumps object to a discord code block"""
    data = orjson.dumps(obj, default=json_encoder, option=orjson.OPT_INDENT_2).decode()
    dumped = f"```json\n{data}\n```"
    return dumped if len(dumped) <= size else "Payload too large"


def cblock(obj: Any, key: str = "", size: int = 2000):
    block = f"```{key}\n{obj}\n```"
    return block if len(block) <= size else "Payload too large"


def uid(length: int = 6):
    """Generates a short id based on uuid4"""
    return uuid4().hex[:length]
