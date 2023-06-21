from datetime import datetime
from typing import Optional
from uuid import uuid4

import aiohttp
import disnake
from beanie import Document, Indexed, init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field

from .ctypes import UUID


# Discord
class User(Document):
    id: UUID = Field(default_factory=uuid4)
    uid: Indexed(int)
    avatarUrl: str
    name: str
    notes: list[str] = []

    class Settings:
        use_cache = True

    @classmethod
    def from_user(cls, user: disnake.User | disnake.Member):
        return cls(
            uid=user.id,
            avatarUrl=user.display_avatar.url,
            name=user.name,
        )

    @property
    def mention(self):
        return f"<@{self.uid}>"


class SomeoneRoles(BaseModel):
    mention: int
    subscriber: int


class Server(Document):
    id: UUID = Field(default_factory=uuid4)
    sid: Indexed(int)
    ownId: Indexed(int)
    name: str
    checks: Optional[list[dict]]
    someone: Optional[SomeoneRoles]
    pinChannel: Optional[str]  # URL of webhook

    @classmethod
    def from_guild(cls, guild: disnake.Guild):
        return cls(  # type: ignore
            sid=guild.id,
            ownId=guild.owner_id,
            name=guild.name,
        )

    def pinChannel_webhook(self, session: aiohttp.ClientSession):
        return disnake.Webhook.from_url(self.pinChannel, session=session)

    class Settings:
        use_cache = True


class DiscordMessage(Document):
    message: str
    snowflake: int
    author: str
    author_id: int
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_message(cls, message: disnake.Message):
        return cls(
            message=message.content,
            author=message.author.name,
            author_id=message.author.id,
            snowflake=message.id,
        )


class CurseForgeMod(Document):
    # TODO: figure out how to do this
    # name: str
    hooks: Optional[list[str]]  # a list of webhook urls, use `webhooks`
    projectId: int
    previous: int | None  # Compare to previous `mod.latestFilesIndexes[0].fileId`

    def webhooks(self, session: aiohttp.ClientSession, token: str = None):
        for hook in self.hooks:
            yield disnake.Webhook.from_url(hook, session=session, bot_token=token)


# Piston
class PistonFile(BaseModel):
    name: Optional[str]
    content: str
    encoding: str = "utf-8"


class PistonEvalJob(BaseModel):
    language: str
    version: str
    files: list[PistonFile]
    stdin: str
    args: list[str]
    compile_timeout: int = 10000
    run_timeout: int = 5000
    compile_memory_limit: int = -1
    run_memory_limit: int = -1


class PistonRunObject(BaseModel):
    """Either a run or compile stage of a response"""

    stdout: Optional[str]
    stderr: Optional[str]
    output: str
    code: int
    signal: Optional[str]


class PistonEvalResponse(BaseModel):
    language: str
    version: str
    compile: Optional[PistonRunObject]
    run: PistonRunObject


class SomeoneRole(BaseModel):
    ...


# data
class Quote(Document):
    id: UUID = Field(default_factory=uuid4)
    quote: str

    class Settings:
        name = "quotes"


class Location(BaseModel):
    name: str
    local_names: Optional[dict]
    lat: float
    lon: float
    country: str
    state: str

    def __str__(self) -> str:
        return f"{self.name}: {self.lat}, {self.lon}"


# Minecraft container management
class MinecraftContainer(Document):
    name: str
    containerid: str | None = None
    image: str
    authorid: int
    # config: CreateContainerConfig
    uid: str


DocumentModels_discord = [User, Server, DiscordMessage]
DocumentModels_data = [Quote, CurseForgeMod, MinecraftContainer]


async def init_models(db: AsyncIOMotorClient):
    await init_beanie(db.discord, document_models=DocumentModels_discord)
    await init_beanie(db.data, document_models=DocumentModels_data)
