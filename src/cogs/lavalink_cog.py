import disnake
from disnake.ext import commands
import wavelink
from wavelink.utils import MISSING
from wavelink import Player
from helper import DatBot, CogLoadingFailure, Settings
from helper.patch import patch_wavelink_loggers


class LavaLinkCog(commands.Cog):
    CmdInter = disnake.ApplicationCommandInteraction
    name = "wavelink"
    key_enabled = True
    key_loc = "wavelink"

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")
        if Settings.patches.wavelink:
            patch_wavelink_loggers(bot.get_logger, f"cog.{self.name}.wavelink.")

        self.nodes = wavelink.NodePool()

    async def connect_node(self):
        """Connect to our Lavalink nodes."""

        conf = Settings.keys.get(self.key_loc)
        if isinstance(conf, list):
            for i in conf:
                await self.nodes.create_node(
                    bot=self.bot,
                    host=i["host"],
                    port=i["port"],
                    password=i["password"],
                    identifier=i.get("identifier", MISSING),
                )
        else:
            await self.nodes.create_node(
                bot=self.bot,
                host=conf["host"],
                port=conf["port"],
                password=conf["password"],
                identifier=conf.get("identifier", MISSING),
            )

    async def cog_load(self):
        await self.bot.wait_until_ready()
        self.bot.loop.create_task(self.connect_node())

    @commands.register_injection
    async def get_player(self, inter: CmdInter) -> Player:
        vc: Player
        if not inter.guild.voice_client:
            vc = await inter.author.voice.channel.connect(cls=Player)
            self.log.info(f"creating voice connection: {inter.guild_id}")
        else:
            vc = inter.guild.voice_client
        return vc

    @commands.Cog.listener("on_wavelink_node_ready")
    async def on_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        self.log.info(f"Node: <{node.identifier}> is ready!")
        self.bot.register_aclose(self.name, node.disconnect(force=True))

    @commands.slash_command(name=name)
    @commands.guild_only()
    async def cmd(self, inter: CmdInter):
        ...

    @cmd.sub_command()
    async def play(self, inter: CmdInter, vc: Player, search: str):
        """Play a song with the given search query.

        Parameters
        ----------
        search: a youtube search term
        """
        await inter.response.defer()
        toplay = await wavelink.YouTubeTrack.search(search, return_first=True)

        await vc.play(toplay)
        embed_dict = {
            "type": "image",
            "title": toplay.title,
            "description": toplay.author,
            "color": disnake.Color.random(),
            "image": {"url": toplay.thumbnail},
            "timestamp": disnake.utils.utcnow().isoformat(),
        }
        await inter.send(embed=disnake.Embed.from_dict(embed_dict))

    @commands.is_owner()
    @cmd.sub_command_group("nodes", "Commands for node handling and configuration")
    async def nodes_(self, inter: CmdInter):
        self.log.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")

    @nodes_.sub_command("reconnect", "Attempts to reconnect with the node")
    async def reconnect_(self, inter: CmdInter):
        await inter.send("Attempting reconnect")
        await self.connect_node()

    @nodes_.sub_command("disconnect", "Attempts to reconnect with the node")
    async def disconnect_node_(
        self, inter: CmdInter, node_id: str, force: bool = False
    ):
        await inter.response.defer()
        node: wavelink.Node = self.nodes.get_node(identifier=node_id)
        await node.disconnect(force=force)
        await inter.send("Node disconnected!")

    @nodes_.sub_command("shutdown", "disconnects from all nodes")
    async def shutdown_nodes_(self, inter: CmdInter):
        await inter.send("Closing all node connections")
        async for node in self.nodes.nodes.values():
            node.disconnect()

    @nodes_.sub_command("list", "Lists all connected nods")
    async def list_nodes_(self, inter: CmdInter):
        nodes = "\n".join([repr(i) for i in self.nodes.nodes])
        await inter.send(
            f"I have {len(self.nodes.nodes)} connected nodes\n```{nodes}```"
        )


def setup(bot: DatBot):
    if not Settings.keys.get(LavaLinkCog.key_loc):
        raise CogLoadingFailure(f"Missing `{LavaLinkCog.name}` configuration.")
    bot.add_cog(LavaLinkCog(bot))
