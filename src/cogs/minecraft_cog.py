from typing import TYPE_CHECKING, TypeAlias

import aiohttp
import disnake
from aiodocker import Docker, DockerError
from data.mcserver import ServerTags
from disnake.ext import plugins
from helper import CogMetaData, ConVar, DatBot, Settings, uid
from helper.csettings import MCServerConfig
from helper.docker import DockerWrapper
from helper.models import MinecraftContainer
from thefuzz import process

if TYPE_CHECKING:
    from helper.docker import Image

# Meta
metadata = CogMetaData(
    name="mcserver",
    description="Create a minecraft server using docker containers",
    key="mcserver",
    require_key=True,
    skip=True,
)
plugin: plugins.Plugin[DatBot] = plugins.Plugin(
    name=metadata.name, logger=f"cog.{metadata.name}"
)

# Aliases
CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
GuildInter: TypeAlias = disnake.GuildCommandInteraction

# Context Vars
dockerw: ConVar[DockerWrapper] = ConVar(f"{metadata.name}.dockerc")

# Ideas
"""
Working
TODO: container manager

Less important
TODO: finish Docker api
TODO: version parsing
TODO: version & tag comparison
TODO: discord intergation
TODO: whitelist
TODO: clean up code


IMPORTANT
TODO: change router verbosity
TODO: curseforge support
TODO: limit servers per person & total
TODO: limit docker resource usage
TODO: friendly name; name collison somehow
TODO: version check

"""

# Overview
"""
a system for creating and managing docker instances of minecraft
"""

# Consts
LOGGER = plugin.logger
SETTINGS: MCServerConfig = Settings.keys.get(metadata.key, MCServerConfig)
SERVER_ENV = {
    "EULA": True,
    "USE_MODPACK_START_SCRIPT": False,
    "ENABLE_AUTOPAUSE": True,
    "MAX_PLAYERS": 5,
    "USE_AIKAR_FLAGS": True,
    "CF_API_KEY": SETTINGS.cfapikey,
}
HEADERS = {"Content-Type": "application/json", "Accept": "application/json"}


# Hooks
@plugin.load_hook()
async def docker_create():
    http = await plugin.bot.make_http(
        name=metadata.name,
        connector=aiohttp.UnixConnector(SETTINGS.dockerSocket),
    )
    docker = DockerWrapper(Docker(session=http))
    dockerw.set(docker)
    await docker.ping()


@plugin.load_hook(post=True)
async def router_load():
    # TODO: register all servers and their routes on boot, or find a method to persist
    async with plugin.bot.httpclient.get(
        SETTINGS.routerUrl + "/routes", headers=HEADERS
    ) as res:
        res.raise_for_status()


@plugin.load_hook(post=True)
async def container_load():
    # TODO: turn on all containers again
    ...


@plugin.load_hook()
async def misc_load():
    if new := SETTINGS.get("extraEnv", None):
        SERVER_ENV.update(new)


@plugin.unload_hook(post=True)
async def docker_teardown():
    docker = dockerw.get()
    #
    async for container in MinecraftContainer.all():
        try:
            d, _ = await docker.get_container(container.containerid)
        except DockerError:
            LOGGER.debug("Container not found, Skipping")
        else:
            LOGGER.debug(f"Stopping '{container.id}'")
            await d.stop()


# Checks
def check_label(images: "list[Image]", label: str) -> bool:
    return any([label in x.Labels.values() for x in images])


def check_tag(images: "list[Image]", tag: str):
    return any([i for i in images if tag in i.RepoTags])


# Erm?
def gen_fqdn(name: str):
    return SETTINGS.hostUrl.format(name=name)


async def register_route(host: str, port: int, name: str):
    # TODO: friendly names?
    client = plugin.bot.httpclient
    fqdn = gen_fqdn(name)
    data = {
        "serverAddress": fqdn,
        "backend": f"{host}:{port}",
    }
    async with client.post(
        SETTINGS.routerUrl + "/routes",
        json=data,
        headers=HEADERS,
    ) as res:
        res.raise_for_status()
    return fqdn


# Commands
@plugin.slash_command(name=metadata.name)
async def cmd(inter: CmdInter):
    LOGGER.debug(f"{inter.author.name} @ {inter.guild.name}")


@cmd.sub_command(name="create")
async def create_server(
    inter: CmdInter,
    tag: ServerTags = ServerTags.latest,
    # version: MinecraftVersions = MinecraftVersions.v_1_19_3, # TODO
):
    """Creates a docker container using selected versions and tags
    Parameters
    ----------
    tag: an optional jvm implementation and version picker
    """
    # TODO: replace
    docker = dockerw.get()
    env = SERVER_ENV.copy()
    server = await docker.create_container(
        image=f"itzg/minecraft-server:{tag}",
        network=SETTINGS.dockerNetwork,
        env=env,
        server_id=uid(),
        author_id=inter.author.id,
    )
    fqdn = await register_route(host=server.uid, port=25565, name=server.uid)
    embed = disnake.Embed(
        title="Creation Successful", description="The server has been created!"
    ).add_field(name="Join Here", value=fqdn)
    await inter.send(embed=embed)


@cmd.sub_command(name="delete")
async def delete_server(inter: CmdInter, server: str):
    await inter.response.defer()

    docker = None
    container = await MinecraftContainer.find_one(
        MinecraftContainer.containerid == server
    )
    if container is None:
        return await inter.send("Something went wrong")
    fucking = await docker.containers.get(server)
    fucking.delete()
    await container.delete()


@cmd.sub_command_group(name="dev")
async def dev(inter: CmdInter):
    "Funny seeing you here"


@dev.sub_command(name="list")
async def start(inter: CmdInter):
    docker = None
    rawimages = await docker.containers.list(filter="ancestor=")
    images = [Image.parse_obj(x) for x in rawimages]
    await inter.send(check_label(images, "docker-minecraft-server"))


@dev.sub_command(name="fqdn")
async def create_fqdn(inter: CmdInter, name: str, host: str):
    fqdn = await register_route(host, "25565", name)
    await inter.send(fqdn)


# Autocompleters
@delete_server.autocomplete("server")
async def autocomplete(inter: CmdInter, input: str):  # TODO rename
    containers = await MinecraftContainer.find(
        MinecraftContainer.authorid == inter.author.id
    ).to_list()

    if input == "":
        return [x.uid for x in containers][:24]

    best = process.extractBests(input, [x.uid for x in containers], limit=25)
    return [x[0] for x in best]


setup, teardown = plugin.create_extension_handlers()
