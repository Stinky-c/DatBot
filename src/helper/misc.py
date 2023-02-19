import collections
import json
import os
from enum import EnumMeta, IntEnum
from glob import glob
from pathlib import Path
from typing import Any
from uuid import uuid4

import disnake
from pydantic.json import pydantic_encoder

from .models import Quote


def cogs_status() -> list[dict[str, Path | str | bool]]:
    """returns all information regarding cog files"""
    cog_contents = [
        y for x in os.walk("cogs") for y in glob(os.path.join(x[0], "*.py"))
    ]
    tmp = []
    for i in cog_contents:
        a = {
            "path": Path(i),
            "logic_name": i.replace("\\", ".").strip(".py"),
            "status": True if "_cog" in i else False,
        }
        c = ("_cog.py", "_disabled.py") if a["status"] else ("_disabled.py", "_cog.py")
        a["toggle"] = lambda: os.rename(str(a["path"]), str(a["path"]).replace(*c))
        tmp.append(a)

    return tmp


def variadic(x: Any, allowed_types=(str, bytes, dict)):
    """Converts item to a tuple if not iterable or not in allowed types"""
    return (
        x
        if isinstance(x, collections.abc.Iterable) and not isinstance(x, allowed_types)
        else (x,)
    )


def build_path(*path: str, t: bool = False) -> str | Path:
    """builds a path from given strings
    Creates parent dirs if missing and is directory

    Args:
        t (bool, optional): Transfrom to string. Defaults to False.

    Returns:
        str | Path: path to dir or file
    """
    p = Path(*path).absolute()
    if p.is_dir():
        p.mkdir(parents=True, exist_ok=True)
    return str(p) if not t else p


def format_time(time: int | float) -> str:
    """Formats a time, uses '%Y-%m-%d %H:%M:%S'"""
    return disnake.utils.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def bytes2human(n):
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


def escape_all(input: str) -> str:
    """Escapes mentiosn and removes markdown"""
    s1 = disnake.utils.resolve_template(input)
    s2 = disnake.utils.remove_markdown(s1)
    return s2


def jdumps(obj: Any,size:int=2000) -> str:
    """Dumps object to a discord code block"""
    dumped = f"```json\n{json.dumps(obj, indent=4, default=pydantic_encoder)}\n```"
    return dumped if len(dumped) <= size else "Payload too large"


def cblock(obj: Any, key: str = "", size: int = 2000):
    block = f"```{key}\n{obj}\n```"
    return block if len(block) <= size else "Payload too large"


def uid(length: int = 6):
    """Generates a short id based on uuid4"""
    return uuid4().hex[:length]


class ContainsEnumMeta(EnumMeta):
    def __contains__(cls, item):
        return item in [v.value for v in cls.values()]


class HTTP_STATUS(IntEnum, metaclass=ContainsEnumMeta):
    continue_ = 100
    switching_protocols = 101
    processing = 102
    early_hints = 103

    OK = 200
    created = 201
    accepted = 202
    non_authoritative_information = 203
    no_content = 204
    reset_content = 205
    partial_content = 206
    multi_status = 207
    already_reported = 208
    im_used = 226

    multiple_choices = 300
    moved_permanently = 301
    found = 302
    see_other = 303
    not_modified = 304
    use_proxy = 305
    temporary_redirect = 307
    permanent_redirect = 308
    bad_request = 400
    unauthorized = 401
    payment_Required = 402
    forbidden = 403
    not_found = 404
    method_not_allowed = 405
    not_acceptable = 406
    proxy_authentication_required = 407
    request_timeout = 408
    conflict = 409
    gone = 410
    length_required = 411
    precondition_failed = 412
    payload_too_large = 413
    uri_too_long = 414
    unsupported_media_type = 415
    range_not_satisfiable = 416
    expectation_failed = 417
    im_a_teapot = 418
    misdirected_request = 421
    unprocessable_entity = 422
    locked = 423
    failed_dependency = 424
    too_early = 425
    upgrade_required = 426
    precondition_required = 428
    too_many_requests = 429
    request_header_fields_too_large = 431
    unavailable_for_legal_reasons = 451

    internal_server_error = 500
    not_implemented = 501
    bad_gateway = 502
    service_unavailable = 503
    gateway_timeout = 504
    http_version_not_supported = 505
    variant_also_negotiates = 506
    insufficient_storage = 507
    loop_detected = 508
    not_extended = 510
    network_authentication_required = 511
    web_server_is_down = 521
    connection_timed_out = 522
    origin_is_unreachable = 523
    ssl_handshake_failed = 525
    network_connect_timeout_error = 599


HTTP_CODES = list(HTTP_STATUS._value2member_map_.keys())
