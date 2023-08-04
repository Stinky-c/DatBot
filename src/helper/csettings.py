"""
A collection of sub settings for all modules
"""
from typing import Any

from pydantic import BaseModel, BaseSettings


# Base
class BasePluginConfig(BaseSettings):
    enabled: bool


# Minecraft
class MCServerConfig(BasePluginConfig):
    cfapikey: str  # Curseforge api key
    routerUrl: str  # Url to mc-router
    hostUrl: str  # Base url for mcservers
    dockerSocket: str  = "/var/run/docker.sock" # a docker socket. defaults to `/var/run/docker.sock`
    dockerNetwork: str  # Name identifter for docker network
    extraEnv: dict[str, Any] = {}


# Piston
class PistonConfig(BasePluginConfig):
    url: str = "https://emkc.org/"


# Music
class MusicNodeModel(BaseModel):
    host: str
    port: str
    password: str
    label: str | None


class MusicConfig(BasePluginConfig):
    nodes: list[MusicNodeModel]


# Curseforge
class CurseForgeConfig(BasePluginConfig):
    key: str
    url: str = "https://api.curseforge.com"


# Snekbox
class SnekboxConfig(BasePluginConfig):
    url: str = "http://snekbox:8060"
    auth: str | None = None
