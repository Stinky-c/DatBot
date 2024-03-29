"""Contains all code accustom to various functionality of the bot"""
import importlib
import logging
import signal
import sys
import traceback
from asyncio import AbstractEventLoop
from types import MappingProxyType, SimpleNamespace
from typing import Coroutine, Mapping, Optional, Sequence

import aiohttp
import disnake
from disnake.ext import commands
from disnake.ext.commands import errors as derrors
from mafic import Player, Track
from motor.motor_asyncio import AsyncIOMotorClient

from . import errors
from .ctypes import CogMetaData
from .misc import cblock, dumpbs
from .models import init_models
from .settings import BotSettings, LoggingLevels, Settings

MISSING = disnake.utils.MISSING


class DatBot(commands.InteractionBot):
    _db_conn: AsyncIOMotorClient
    log: logging.Logger
    clog: logging.Logger
    closeList: list[tuple[str, Coroutine]]
    _echannel: disnake.TextChannel = None
    __extensions_meta: dict[str, CogMetaData] = {}
    httpclient: aiohttp.ClientSession  # Useful for one off http requests

    def __init__(
        self,
        *,
        owner_id: Optional[int] = None,
        owner_ids: Optional[set[int]] = None,
        reload: bool = False,
        command_sync_flags: commands.CommandSyncFlags = commands.CommandSyncFlags.default(),
        test_guilds: Optional[Sequence[int]] = None,
        asyncio_debug: bool = False,
        loop: Optional[AbstractEventLoop] = None,
        shard_id: Optional[int] = None,
        shard_count: Optional[int] = None,
        enable_debug_events: bool = False,
        enable_gateway_error_handler: bool = True,
        gateway_params: Optional[disnake.GatewayParams] = None,
        connector: Optional[aiohttp.BaseConnector] = None,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        assume_unsync_clock: bool = True,
        max_messages: Optional[int] = 1000,
        application_id: Optional[int] = None,
        heartbeat_timeout: float = 60,
        guild_ready_timeout: float = 2,
        allowed_mentions: Optional[disnake.AllowedMentions] = None,
        activity: Optional[disnake.BaseActivity] = None,
        status: Optional[disnake.Status | str] = None,
        intents: Optional[disnake.Intents] = None,
        chunk_guilds_at_startup: Optional[bool] = None,
        member_cache_flags: Optional[disnake.MemberCacheFlags] = None,
        localization_provider: Optional[disnake.LocalizationProtocol] = None,
        strict_localization: bool = False,
        bot_config: BotSettings = Settings,
    ):
        super().__init__(
            owner_id=owner_id,
            owner_ids=owner_ids,
            reload=reload,
            command_sync_flags=command_sync_flags,
            test_guilds=test_guilds,
            asyncio_debug=asyncio_debug,
            loop=loop,
            shard_id=shard_id,
            shard_count=shard_count,
            enable_debug_events=enable_debug_events,
            enable_gateway_error_handler=enable_gateway_error_handler,
            gateway_params=gateway_params,
            connector=connector,
            proxy=proxy,
            proxy_auth=proxy_auth,
            assume_unsync_clock=assume_unsync_clock,
            max_messages=max_messages,
            application_id=application_id,
            heartbeat_timeout=heartbeat_timeout,
            guild_ready_timeout=guild_ready_timeout,
            allowed_mentions=allowed_mentions,
            activity=activity,
            status=status,
            intents=intents,
            chunk_guilds_at_startup=chunk_guilds_at_startup,
            member_cache_flags=member_cache_flags,
            localization_provider=localization_provider,
            strict_localization=strict_localization,
        )
        # set up logging
        for k, v in bot_config.logging:
            if v is None:
                continue
            if not v.logfile:
                self.configure_logger(
                    name=k,
                    level=v.level,
                    format=v.format,
                    handler=logging.StreamHandler(sys.stdout),
                )
            else:
                self.configure_logger(
                    name=k,
                    level=v.level,
                    format=v.format,
                    handler=logging.FileHandler(
                        filename=v.logfile, encoding=v.encoding, mode=v.mode
                    ),
                )

        self.log = self.get_logger("bot")
        self.clog = self.get_logger("cog")

        # configure extras
        self.closeList = []
        self.config = bot_config
        self._db_conn = AsyncIOMotorClient(self.config.connections.mongo)
        self.started = False

    @classmethod
    def from_settings(cls, settings: BotSettings = Settings):
        return cls(
            owner_ids=settings.bot.owner_ids,
            test_guilds=settings.bot.test_guilds,
            intents=disnake.Intents(settings.bot.intents_flag),
            reload=settings.bot.reload_flag,
            activity=disnake.Activity(
                name=settings.bot.activity_str,
                type=disnake.ActivityType(settings.bot.activity_type),
            ),
            status=disnake.Status.online,
            command_sync_flags=commands.CommandSyncFlags._from_value(
                settings.bot.command_flag
            ),
            bot_config=settings,
        )

    def configure_logger(
        self,
        name: str,
        format: str,
        handler: logging.Handler,
        level: LoggingLevels = LoggingLevels.ERROR,
    ):
        logger = self.get_logger(name)
        logger.setLevel(level)
        handler.setFormatter(logging.Formatter(format, style="{"))
        logger.addHandler(handler)
        return logger

    async def start(
        self,
        token: str,
        *,
        reconnect: bool = True,
        ignore_session_start_limit: bool = False,
    ) -> None:
        # Setup one of attrs
        self.httpclient = await self.make_http("internal")

        # register close task for signal interupts
        try:

            def close():
                self.loop.create_task(self.close())

            self.loop.add_signal_handler(signal.SIGINT, close)
            self.loop.add_signal_handler(signal.SIGTERM, close)
        except NotImplementedError:
            pass

        return await super().start(
            token=token,
            reconnect=reconnect,
            ignore_session_start_limit=ignore_session_start_limit,
        )

    async def make_http(self, name: str, *args, **kwargs) -> aiohttp.ClientSession:
        """Make a aiohttp session and register the closing functions
        logger name: `cog.{name}.http`
        """
        logger = self.get_logger(f"cog.{name}.http")

        async def on_request_end(
            sess: aiohttp.ClientSession,
            ctx: SimpleNamespace,
            end: aiohttp.TraceRequestEndParams,
        ):
            """aiohttp client logging"""
            res = end.response
            logger.debug(
                f"[{res.status!s} {res.reason!s}] {res.method.upper()!s} {end.url!s} ({res.content_type!s})"
            )

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_end.append(on_request_end)

        connector = kwargs.pop(
            "connector", aiohttp.TCPConnector(resolver=aiohttp.AsyncResolver())
        )
        json_serialize = kwargs.pop("json_serialize", dumpbs)

        # ClientSession perfers to be created in an async context?
        sess = aiohttp.ClientSession(
            connector=connector,
            trace_configs=[trace_config],
            json_serialize=json_serialize,
            *args,
            **kwargs,
        )

        self.register_aclose(name, sess.close())
        return sess

    def register_aclose(self, name: str, func: Coroutine):
        """Appends a close method the close list"""
        if not isinstance(func, Coroutine):
            raise TypeError("Not coroutine")
        self.closeList.append(("cog." + name, func))

    def get_logger(self, name: str):
        """Returns a configured logger"""
        return logging.getLogger(name)

    async def send_exception(self, exception: Exception):
        """Sends error to channel, defaults to logging if unset"""

        if Settings.bot.error_channel or self._echannel:
            c = Settings.bot.error_channel
            self.log.info(f"Configuring error channel to {c}")
            self._echannel = await self.fetch_channel(c)

        error = "".join(traceback.format_exception(exception))
        self.log.error(repr(self._echannel))
        if self._echannel:
            c = self._echannel
            embed = disnake.Embed(
                title="Unhandled Exception",
                timestamp=disnake.utils.utcnow(),
                description=cblock(error, size=4096),
                color=disnake.Color.red(),
            )
            await c.send(embed=embed)
        else:
            self.log.exception("An error occured")
        return error

    async def on_connect(self):
        self.log.info("Connecting...")

    async def on_ready(self):
        if not self.started:
            self.log.debug("Loading beanie models")
            await init_models(self._db_conn)
        self.log.info(f"{self.user.name} is ready!")

    async def close(self) -> None:
        self.log.info("Shutting down bot!")
        for name, close in self.closeList:
            self.log.info(f"running '{name}' Close coroutine")
            await close
        await super().close()

    def _load_meta_from_module_spec(
        self, spec: importlib.machinery.ModuleSpec, key: str
    ) -> None:
        """Extend `bot.load_extension` for metadata about cog"""
        lib = importlib.util.module_from_spec(spec)
        sys.modules[key] = lib
        try:
            spec.loader.exec_module(lib)  # type: ignore
        except Exception as e:
            del sys.modules[key]
            raise derrors.ExtensionFailed(key, e) from e

        try:
            meta = lib.metadata
        except AttributeError:
            del sys.modules[key]
            raise errors.MissingCogMeta(key)
        else:
            return meta

    def load_extension_meta(self, name: str) -> CogMetaData:
        """Loads extension meta data, similar to `CommonBotBase.load_extension`"""

        self.extensions
        spec = importlib.util.find_spec(name)
        if spec is None:
            raise derrors.ExtensionNotFound(name)
        return self._load_meta_from_module_spec(spec, name)

    @property
    def extensions_meta(self) -> Mapping[str, CogMetaData]:
        """A read-only mapping of extension name to extension metadata."""
        return MappingProxyType(self.__extensions_meta)


class LavaPlayer(Player[DatBot]):
    managed: disnake.TextChannel
    queue: list[Track]

    def __init__(self, client: DatBot, channel: disnake.abc.Connectable) -> None:
        super().__init__(client, channel)
        self.queue: list[Track] = []
        self.managed: disnake.TextChannel = None
        self._paused: bool = False
