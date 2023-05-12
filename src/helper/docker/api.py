from typing import TYPE_CHECKING

from .models import Image

if TYPE_CHECKING:
    from aiohttp import ClientSession


class BaseDocker:
    def __init__(self, docker: "Docker") -> None:
        self._docker = docker


class DockerImages(BaseDocker):
    # async def list(self, all: bool=False, limit: int):
    async def list(self) -> list[Image]:
        data = await self._docker._get("/images/json")
        return [Image.parse_obj(d) for d in data]


class DockerContainers(BaseDocker):
    ...


class Docker:
    """A simple docker api wrapper"""

    def __init__(self, client: "ClientSession") -> None:
        self._client = client

        self._images = DockerImages(self)
        self._containers = DockerContainers(self)

    @property
    def images(self) -> DockerImages:
        return self._images

    @property
    async def containers(self):
        return self._containers

    async def _get(self, url: str, params: dict = {}) -> dict:
        async with self._client.get(url, params=params) as req:
            req.raise_for_status()
            return await req.json()

    async def _post(self, url: str, data: dict):
        async with self._client.post(url, data=data) as req:
            req.raise_for_status()
            return await req.json()
