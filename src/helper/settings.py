import json
import os
from enum import IntEnum
from glob import glob
from os import environ
from pathlib import Path
from typing import Any, DefaultDict, List, Optional

import disnake
import toml
from pydantic import (
    BaseModel,
    BaseSettings,
    Extra,
    Field,
    MongoDsn,
    SecretStr,
)
from pydantic.json import pydantic_encoder


class LoggingLevels(IntEnum):
    """Logging levels for the `logging` module"""

    CRITICAL = 50
    ERROR = 40
    WARNING = 30
    INFO = 20
    DEBUG = 10
    NOTSET = 0

    WARN = WARNING
    FATAL = CRITICAL


def toml_source(settings: BaseSettings) -> dict[str, Any]:
    encoding = settings.__config__.env_file_encoding
    env = "DATBOT_CONFIG"
    fp = Path(environ.get(env, "config.toml"))
    if not fp.exists():
        raise Exception(f"Missing config file, please set '{env}' to the file path")

    return toml.loads(fp.read_text(encoding))


class LoggerConfig(BaseModel):
    stdout: bool = True
    logfile: Path | None = None
    format: str = "{asctime:20} | {levelname:^7} | {name:15} | {message}"
    level: LoggingLevels = LoggingLevels.INFO
    encoding: str = "utf-8"


class LoggingConfig(BaseModel):
    disnake: LoggerConfig
    cog: LoggerConfig
    bot: LoggerConfig


class Connections(BaseModel):
    mongo: MongoDsn


def cogs_factory(pattern: str = "*_cog.py"):
    # I don't know how I feel about this
    return [
        i.replace("\\", ".").replace("/", ".").strip(".py")
        for i in [
            y for x in os.walk("cogs") for y in glob(os.path.join(x[0], "*_cog.py"))
        ]
    ]


class BotConfig(BaseModel):
    reload_flag: bool = False
    command_flag: int = 31
    intents_flag: int = 3276799
    activity_str: str = "The fucks"
    activity_type: int = disnake.ActivityType.watching.value
    owner_ids: Optional[set[int]]
    test_guilds: Optional[List[int]]
    dev_guilds: Optional[List[int]]
    cogs: List[str] = Field(  # TODO find way to exlclude from schema
        default_factory=lambda: cogs_factory("*_cog.py"),
        exclude=True,
    )
    disabled_cogs: List[str] = Field(  # TODO find way to exlclude from schema
        default_factory=lambda: cogs_factory("*_disabled.py"),
        exclude=True,
    )


class DevConfig(BaseModel):
    # TODO maybe?
    ...


# TODO make api string class
# hidden when logging but not when dumping config
class Key(str):
    ...


class Directory(BaseModel):
    name: str
    path: Path
    data: Optional[dict[str, str]]


class Patches(BaseModel):
    wavelink: bool = False


class BotSettings(BaseSettings):
    """All bot settings"""

    # Connections
    connections: Connections

    # Bot
    token: SecretStr = Field(..., env="DISCORD_TOKEN", exclude=True)
    bot: BotConfig

    # Logging
    logging: LoggingConfig

    # API keys
    keys: DefaultDict[str, Any]

    # directories
    dir: DefaultDict[str, Directory]

    # toggle patches
    patches: Patches = Patches()

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = Extra.ignore

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                toml_source,
                env_settings,
                file_secret_settings,
            )

    def save(self, path: os.PathLike[str] = "config.toml"):  # type: ignore
        with open(path, "w") as f:
            toml.dump(json.loads(self.json()), f)

    def save_json(self, path: os.PathLike[str] = "config.toml"):  # type: ignore
        with open(path, "w") as f:
            json.dump(self.dict(), f, default=pydantic_encoder)


Settings = BotSettings()  # type: ignore


def schema_json():
    return Settings.schema_json()
