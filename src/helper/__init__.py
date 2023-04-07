from functools import partial as _partial

from disnake.ext import tasks as _tasks

# proxy
from motor.motor_asyncio import AsyncIOMotorClient
from disnake.utils import MISSING


from .cbot import DatBot
from .ctypes import URL, UUID, LinkTuple
from .emojis import Emojis
from .errors import CogLoadingFailure
from .misc import (
    HTTP_CODES,
    HTTP_STATUS,
    build_path,
    bytes2human,
    cblock,
    escape_all,
    format_time,
    gen_quote,
    jdumps,
    uid,
    variadic,
)
from .models import Quote, Server, User, init_models
from .settings import Settings
from .views import LinkView
from .ccog import Cog

task = _partial(_tasks.loop, count=1)

__all__ = ("DatBot", "Cog", "Settings")
