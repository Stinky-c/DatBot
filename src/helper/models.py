from uuid import uuid4
from .ctypes import UUID
from beanie import Document, Indexed, init_beanie
from pydantic import BaseModel, Field
from typing import Optional
import disnake
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime

# Discord
class User(Document):
    id: UUID = Field(default_factory=uuid4)
    uid: Indexed(int)
    avatarUrl: str
    name: str
    discriminator: str
    notes: list[str] = []

    class Settings:
        use_cache = True

    @classmethod
    def from_user(cls, user: disnake.User | disnake.Member):
        return cls(
            uid=user.id,
            avatarUrl=user.display_avatar.url,
            name=user.name,
            discriminator=user.discriminator,
        )

    @property
    def full(self):
        return f"{self.name}#{self.discriminator}"

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

    @classmethod
    def from_guild(cls, guild: disnake.Guild):
        return cls(  # type: ignore
            sid=guild.id,
            ownId=guild.owner_id,
            name=guild.name,
        )

    class Settings:
        use_cache = True


class DiscordMessage(Document):
    message: str
    author: str
    author_id: int
    timestamp: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_message(cls, message: disnake.Message):
        return cls(
            message=message.content,
            author=message.author.name,
            author_id=message.author.id,
        )


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

    stdout: str | None
    stderr: str | None
    output: str
    code: int
    signal: str | None


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


DocumentModels_discord = [User, Server, DiscordMessage]
DocumentModels_data = [Quote]


async def init_models(db: AsyncIOMotorClient):
    await init_beanie(db.discord, document_models=DocumentModels_discord)
    await init_beanie(db.data, document_models=DocumentModels_data)
