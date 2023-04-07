"""Contains all code accustom to various functionality of the bot"""
import logging
import signal
import sys
from asyncio import AbstractEventLoop
from types import SimpleNamespace
from typing import Coroutine, Optional, Sequence

import aiohttp
import disnake
from disnake.ext import commands
from mafic import Player, Track
from motor.motor_asyncio import AsyncIOMotorClient
import traceback

from .models import init_models
from .settings import BotSettings, LoggingLevels, Settings
from .misc import cblock

MISSING = disnake.utils.MISSING


class DatBot(commands.InteractionBot):
    _db_conn: AsyncIOMotorClient
    log: logging.Logger
    clog: logging.Logger
    closeList: list[tuple[str, Coroutine]]
    _echannel: disnake.TextChannel = None

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
        # TODO add options to configure other handlers
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
        if self.reload:
            self.log.info("Reload enabled")
            self.loop.create_task(self._watchdog())

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
        """Make a aiohttp session and register the closing functions"""
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

        sess = aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(resolver=aiohttp.AsyncResolver()),
            trace_configs=[trace_config],
            *args,
            **kwargs,
        )

        self.closeList.append(("cog." + name, sess.close()))
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


class LavaPlayer(Player[DatBot]):  # TODO: new name
    managed: disnake.TextChannel
    queue: list[Track]

    def __init__(self, client: DatBot, channel: disnake.abc.Connectable) -> None:
        super().__init__(client, channel)
        self.queue: list[Track] = []
        self.managed: disnake.TextChannel = None
        self._paused: bool = False
