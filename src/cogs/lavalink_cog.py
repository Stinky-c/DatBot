import disnake
from disnake.ext import commands
import wavelink
from helper import DatBot, CogLoadingFailure


class LavaLinkCog(commands.Cog):
    CmdInter = disnake.ApplicationCommandInteraction
    Player = wavelink.Player
    name = "wavelink"
    key_enabled = True
    key_loc = "wavelink"

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")

    async def connect_node(self):
        """Connect to our Lavalink nodes."""

        conf = self.bot.config.keys.get(self.key_loc)
        await wavelink.NodePool.create_node(
            bot=self.bot,
            host=conf["host"],
            port=conf["port"],
            password=conf["password"],
        )

    async def cog_load(self):
        await self.bot.wait_until_ready()
        self.bot.loop.create_task(self.connect_node())

    @commands.register_injection
    async def get_player(self, inter: CmdInter) -> wavelink.Player:
        vc: wavelink.Player
        if not inter.guild.voice_client:
            vc = await inter.author.voice.channel.connect(cls=wavelink.Player)
        else:
            vc = inter.guild.voice_client
        return vc

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        ...

    @cmd.sub_command(name="ping")
    async def ping(self, inter: CmdInter):
        await inter.response.send_message(f"Pong! {round(self.bot.latency * 1000)}ms")

    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        self.log.info(f"Node: <{node.identifier}> is ready!")
        self.bot.register_aclose(self.name, node.disconnect())

    class OtherCustomClass:
        def __init__(self, username: str, discriminator: str) -> None:
            self.username = username
            self.discriminator = discriminator

        @commands.converter_method
        async def convert(cls, inter: disnake.CommandInteraction, user: disnake.User):
            return cls(user.name, user.discriminator)

    @cmd.sub_command()
    async def play(self, inter: CmdInter, vc: Player, search: str):
        """Play a song with the given search query.

        If not connected, connect to our voice channel.
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
            "timestamp": disnake.utils.utcnow(),
        }
        await inter.send(embed=disnake.Embed.from_dict(embed_dict))

    @commands.is_owner()
    @cmd.sub_command(
        name="reconnect", description="Attempts to reconnect with the node"
    )
    async def reconnect_(self, inter: CmdInter):
        await inter.send("Attempting reconnect")
        await self.connect_node()

    @commands.is_owner()
    @cmd.sub_command(
        name="disconnect", description="Attempts to reconnect with the node"
    )
    async def disconnect_(self, inter: CmdInter):
        ...


def setup(bot: DatBot):
    if LavaLinkCog.key_enabled and not bot.config.keys.get(LavaLinkCog.key_loc):
        raise CogLoadingFailure(
            f"Missing `{LavaLinkCog.key_loc}` api key. Disable or provide key"
        )
    bot.add_cog(LavaLinkCog(bot))
