from .views import LinkView
from .misc import (
    gen_quote,
    build_path,
    bytes2human,
    format_time,
    variadic,
    escape_all,
    HTTP_STATUS,
    HTTP_CODES
)
from .cbot import DatBot
from .ctypes import LinkTuple, URL, UUID

# from .cache import MongoConnection
from .models import Server, User, Quote, init_models
from .settings import Settings
from .emojis import Emojis

# proxy
from motor.motor_asyncio import AsyncIOMotorClient
from disnake.utils import MISSING


class CogLoadingFailure(Exception):
    """For when you just refuse to load the cog"""


__all__ = ("DatBot",)
