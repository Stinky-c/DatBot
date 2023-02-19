import asyncio

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from redis.asyncio import Redis

from .models import DocumentModels, Server, User


# FIXME Kinda pointless
class MongoConnection:
    def __init__(
        self,
        mongodb_uri: str = "mongodb://localhost:27017",
    ) -> None:
        # Mongo connection
        self.__mClient = AsyncIOMotorClient(mongodb_uri)
        asyncio.get_event_loop().run_until_complete(
            init_beanie(
                database=self.__mClient.discord,
                document_models=DocumentModels,
            )
        )

    @property
    def mongo_client(self):
        return self.__mClient

    async def get_or_fetch_user(self, user_id: str | int) -> User | None:
        """gets or fetches user object

        Args:
            guild_id (str | int): discord User id

        Returns:
            User | None: May return None
        """
        user = await User.find_one(User.uid == user_id)
        return user

    async def user_exsits(self, user_id: str | int) -> bool:
        """Attempts to chck if User exsits"""
        return bool(await User.find(User.uid == user_id).first_or_none())

    async def update_user(self, user: User, cache_time: int = 120):
        """Updates and caches the user object

        Args:
            user (User): Newly updated user object
            cache_time (int, optional): cache expiry time in seconds. Defaults to 120.

        """
        await user.save_changes()

    async def get_or_fetch_guild(self, guild_id: str | int) -> Server | None:
        """gets or fetches server object

        Args:
            guild_id (str | int): discord guild id

        Returns:
            Server | None: May return None
        """
        server = await Server.find_one(Server.sid == guild_id)
        return server

    async def guild_exsits(self, guild_id: str | int) -> bool:
        """Attempts to chck if Server exsits"""
        return bool(await Server.find(Server.sid == guild_id).first_or_none())

    async def update_server(self, server: Server, cache_time: int = 120):
        """Updates and caches the server object

        Args:
            server (Server): Newly updated server object
            cache_time (int, optional): cache expiry time in seconds. Defaults to 120.

        """
        await server.save_changes()


class MongoRedisConnection:
    def __init__(
        self,
        mongodb_uri: str = "mongodb://localhost:27017",
        redis_settings: dict = {"host": "localhost", "port": 6379, "db": 0},
    ) -> None:
        # Mongo connection
        self.__mClient = AsyncIOMotorClient(mongodb_uri)
        asyncio.get_event_loop().run_until_complete(
            init_beanie(
                database=self.__mClient.discord,
                document_models=DocumentModels,
            )
        )
        # redis caching
        self.__rClient = Redis(**redis_settings)

    @property
    def mongo_client(self):
        return self.__mClient

    @property
    def redis_client(self):
        return self.__rClient

    @property
    async def redis_ping(self):
        return await self.__rClient.ping()

    @staticmethod
    def user_redis_key(id: int | str):
        return f"user-discord-{id}"

    @staticmethod
    def server_redis_key(id: int | str):
        return f"server-discord-{id}"

    async def get_or_fetch_user(self, user_id: str | int) -> User | None:
        """gets or fetches user object

        Args:
            guild_id (str | int): discord User id

        Returns:
            User | None: May return None
        """
        if user := await self.redis_client.get(self.user_redis_key(user_id)):
            return user
        user = await User.find_one(User.uid == user_id)
        return user

    async def user_exsits(self, user_id: str | int) -> bool:
        """Attempts to chck if User exsits"""
        return bool(await User.find(User.uid == user_id).first_or_none())

    async def update_user(self, user: User, cache_time: int = 120):
        """Updates and caches the user object

        Args:
            user (User): Newly updated user object
            cache_time (int, optional): cache expiry time in seconds. Defaults to 120.

        """
        await user.save_changes()
        return await self.__rClient.set(
            self.user_redis_key(user.uid), user.json(), ex=cache_time
        )

    async def get_or_fetch_guild(self, guild_id: str | int) -> Server | None:
        """gets or fetches server object

        Args:
            guild_id (str | int): discord guild id

        Returns:
            Server | None: May return None
        """
        if server := await self.redis_client.get(self.server_redis_key(guild_id)):
            return server
        server = await Server.find_one(Server.sid == guild_id)
        return server

    async def guild_exsits(self, guild_id: str | int) -> bool:
        """Attempts to chck if Server exsits"""
        return bool(await Server.find(Server.sid == guild_id).first_or_none())

    async def update_server(self, server: Server, cache_time: int = 120):
        """Updates and caches the server object

        Args:
            server (Server): Newly updated server object
            cache_time (int, optional): cache expiry time in seconds. Defaults to 120.

        """
        await server.save_changes()
        return await self.__rClient.set(
            self.server_redis_key(server.uid), server.json(), ex=cache_time
        )
