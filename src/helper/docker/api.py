import aiodocker.containers

from helper.models import MinecraftContainer

from .models import CreateContainerConfig, Image

# TODO: An api that does what i fucking want
# better typing and interface


class DockerWrapper:
    def __init__(self, docker: aiodocker.Docker) -> None:
        self.docker = docker

    async def ping(self) -> str:
        """
        !Ping

        Pong!
        """
        return (await self.docker.version())["Version"]

    async def get_container(
        self, id: str
    ) -> tuple[aiodocker.containers.DockerContainer, MinecraftContainer]:
        """Gets container by id"""
        mccontainer = await MinecraftContainer.find_one(
            MinecraftContainer.containerid == id
        )
        container = await self.docker.containers.get(id)
        return container, mccontainer

    async def stop_container(self, id: str):
        """Stops a docker container"""
        container = await self.docker.containers.get(id)
        await container.stop()

    async def create_container(
        self,
        image: str,
        network: str,
        env: dict[str, str],
        server_id: str,
        author_id: int,
        start: bool = True,
    ):
        """Creates a containers from the given config"""
        await self.ensure_image(image)

        # Docker config
        containerconf = CreateContainerConfig(
            Env=[f"{k}={v}" for k, v in env.items()],
            Image=image,
            HostConfig={
                "NetworkMode": network,
            },
            NetworkingConfig={"EndpointsConfig": {network: {"Aliases": [server_id]}}},
        )

        # Mongo thingy
        server = MinecraftContainer(
            name=f"mcserver-{server_id}",
            uid=server_id,
            # config=containerconf,
            image=image,
            authorid=author_id,
        )
        # Create container in docker and update database entry
        container = await self.docker.containers.create(
            config=containerconf, name=server.name
        )
        server.containerid = container.id
        if start:
            await container.start()
        return await server.create()

    async def list_images(self) -> list[Image]:
        """Lists all docker images"""
        return [Image.parse_obj(x) for x in await self.docker.images.list()]

    async def ensure_image(self, image: str):
        """Ensures the image is present"""
