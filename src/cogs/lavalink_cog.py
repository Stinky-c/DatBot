import disnake
import wavelink
from disnake.ext import commands
from helper import CogLoadingFailure, DatBot, Emojis, Settings, jdumps, cblock
from helper.patch import patch_wavelink_loggers
from wavelink import Player
from wavelink.utils import MISSING


# TODO: update to use REST based API
# TODO: add playlist
# TODO: add timeout feature
# TODO: add a youtube only queue
class LavaLinkCog(commands.Cog):
    CmdInter = disnake.ApplicationCommandInteraction
    name = "wavelink"
    key_enabled = True
    key_loc = "wavelink"
    nodes = wavelink.NodePool
    _player_channels: dict[int, int]

    def __init__(self, bot: DatBot):
        self.bot = bot
        self.log = bot.get_logger(f"cog.{self.name}")
        self._player_channels = {}
        if Settings.patches.wavelink:
            patch_wavelink_loggers(bot.get_logger, f"cog.{self.name}.wavelink.")

    async def connect_node(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        if len(self.nodes._nodes) > 0:
            self.log.info("Nodes already loaded")
            return False

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
        return True

    async def cog_load(self):
        await self.connect_node()

    def is_connected():
        async def predicate(inter: disnake.CmdInter, *_):
            return inter.author.voice is not None

        return commands.check(predicate)

    @staticmethod
    def embed_factory(toplay: wavelink.YouTubeTrack) -> dict:
        return {
            "type": "image",
            "title": toplay.title,
            "description": toplay.author or "unknown",
            "color": disnake.Color.random(),
            "image": {"url": toplay.__getattribute__("thumbnail") or ""},
            "timestamp": disnake.utils.utcnow().isoformat(),
        }

    async def get_player_channel(self, guild_id: int) -> disnake.TextChannel:
        channel_id = self._player_channels.get(guild_id, None)
        if not channel_id:
            raise Exception("Player not bound")
        return await self.bot.fetch_channel(channel_id)

    async def get_play(self, vc: Player, **kwargs) -> wavelink.abc.Playable:
        """Gets the next item in queue and plays it"""
        to_play = await vc.queue.get_wait()
        await vc.play(to_play, **kwargs)
        return to_play

    @commands.register_injection
    async def get_player(self, inter: CmdInter) -> Player:
        vc: Player
        if not inter.guild.voice_client:
            vc = await inter.author.voice.channel.connect(cls=Player)
            self.log.info(f"Creating voice connection: '{inter.guild!s}'")
        else:
            vc = inter.guild.voice_client
        self._player_channels[inter.guild.id] = inter.channel_id
        return vc

    @commands.Cog.listener("on_wavelink_node_ready")
    async def on_node_ready(self, node: wavelink.Node):
        """Event fired when a node has finished connecting."""
        self.log.info(f"Node: <{node.identifier}> is ready!")
        self.bot.register_aclose(self.name, node.disconnect(force=True))

    @commands.Cog.listener("on_wavelink_track_end")
    async def on_track_end(self, player: Player, track: wavelink.Track, reason: str):
        self.log.debug(f"track ended: {reason}")
        to_play: wavelink.YouTubeTrack = player.queue.get()
        channel = await self.get_player_channel(player.guild.id)
        await player.play(to_play)
        embed = self.embed_factory(to_play)
        await channel.send(
            f"Now playing '{to_play.title}'", embed=disnake.Embed.from_dict(embed)
        )

    @commands.Cog.listener("on_wavelink_track_exception")
    async def on_track_exception(self, *args, **kwargs):
        self.log.error(args)
        self.log.error(kwargs)

    @commands.slash_command(name=name)
    @commands.guild_only()
    @is_connected()
    @commands.cooldown(1, 1, commands.BucketType.member)  # once a second
    async def cmd(self, inter: CmdInter):
        ...

    @cmd.sub_command("play")
    async def play_(
        self, inter: CmdInter, vc: Player, search: str, replace: bool = False
    ):
        """Play a song from youtube with the given search query.

        Parameters
        ----------
        search: a youtube search term
        """

        await inter.response.defer()
        toplay = await wavelink.YouTubeTrack.search(search, return_first=True)
        if not vc.is_playing() or replace:
            # raise wavelink.LoadTrackError({"exception": {"message": "Testing"}})
            # why is this not handling correctly
            await vc.play(toplay)
            message = f"Now playing '{toplay.title}'"
        else:
            vc.queue.put(toplay)
            message = f"Now queuing '{toplay.title}'"

        embed = self.embed_factory(toplay)
        await inter.send(message, embed=disnake.Embed.from_dict(embed))
        self.log.debug(message + f" in '{inter.guild!s}'")

    @cmd.sub_command("skip")
    async def skip_(self, inter: CmdInter, vc: Player):
        """Skips the current song"""
        # TODO: add skip to queue index
        if not vc.is_playing():
            await vc.resume()
        await vc.seek(vc.source.length * 1000)
        # source length is in seconds and seek uses milliseconds
        await inter.send("Skipping!")

    @cmd.sub_command("quit")
    async def quit_(self, inter: CmdInter, vc: Player):
        """Disconnects bot from voice channel"""
        await vc.disconnect()
        del self._player_channels[inter.guild_id]
        await inter.send(f"Goodbye {Emojis.wave}")

    @cmd.sub_command("queue")
    async def queue_(self, inter: CmdInter, vc: Player):
        if len(vc.queue) <= 0:
            return await inter.send("The queue is empty")
        base = "\n".join([i.title for i in vc.queue])
        await inter.send(
            f"There are {len(vc.queue)} items in the queue.\n" + cblock(base)
        )

    @commands.is_owner()
    @cmd.sub_command_group("nodes")
    async def nodes_(self, inter: CmdInter):
        """Commands for node handling and configuration"""
        self.log.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")

    @nodes_.sub_command("reconnect")
    async def reconnect_(self, inter: CmdInter):
        """Attempts to reconnect with the node"""
        await inter.send("Attempting reconnect")
        await self.connect_node()

    @nodes_.sub_command("disconnect")
    async def disconnect_node_(
        self, inter: CmdInter, node_id: str, force: bool = False
    ):
        """Attempts to disconnect from the node"""
        await inter.response.defer()
        node = self.nodes.get_node(identifier=node_id)
        await node.disconnect(force=force)
        await inter.send("Node disconnected!")

    @nodes_.sub_command("shutdown")
    async def shutdown_nodes_(self, inter: CmdInter):
        """disconnects from all nodes"""
        await inter.send("Not yet implemented")

    @nodes_.sub_command("list")
    async def list_nodes_(self, inter: CmdInter):
        """Lists all connected nods"""
        if len(self.nodes._nodes) <= 0:
            return await inter.send("I have zero connected nodes")
        nodes = "\n".join([repr(i) for i in self.nodes._nodes])
        await inter.send(
            f"I have {len(self.nodes._nodes)} connected nodes\n```{nodes}```"
        )

    @commands.is_owner()
    @cmd.sub_command_group("dev")
    async def dev_(self, inter: CmdInter):
        """Allows for viewing & manipulation of internal data"""
        self.log.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")

    @dev_.sub_command("players")
    async def players_(self, inter: CmdInter):
        """Returns the channels players are bound to"""
        await inter.send(jdumps(self._player_channels))

    @dev_.sub_command("current")
    async def current_(self, inter: CmdInter, vc: Player):
        """Returns info about the guild player."""
        embed_dict = {
            "title": f"'{vc.guild!s}' statistics",
            "fields": [
                {
                    "name": "Node",
                    "value": vc.node.identifier,
                },
                {
                    "name": "Last update",
                    "value": disnake.utils.format_dt(vc.last_update),
                },
                {"name": "Last position", "value": str(vc.last_position)},
                {"name": "Playing?", "value": vc.is_playing()},
                {"name": "Volume", "value": vc.volume},
                {"name": "Queue length", "value": len(vc.queue)},
            ],
            "timestamp": disnake.utils.utcnow().isoformat(),
        }

        await inter.send(embed=disnake.Embed.from_dict(embed_dict))

    @dev_.sub_command("eval")
    async def eval_(self, inter: CmdInter, vc: Player, source: str):
        """Takes a one line statment and evals it in the current scope
        Parameters
        ----------
        source: a string to eval
        """
        evaled = eval(source, locals())
        await inter.send(cblock(evaled))

    @cmd.error
    async def on_error(
        self, inter: CmdInter, exception: commands.CommandError, *args, **kwargs
    ):  # TODO find better type hint for exception
        # TODO find the best error handling method
        # exceptions are still printed on error even after handling
        if isinstance(exception, commands.CheckFailure):
            await inter.send("You must be connected to a visible voice channel.")
            self.log.debug(f"'{inter.author!s}' was not connected in '{inter.guild!s}'")
        elif isinstance(
            exception, wavelink.errors.LoadTrackError
        ):  # Might not be `CommandInvokeError`
            await inter.send("There was an issue loading the next song.")
            self.log.error("Song failed loading")
        else:
            await inter.send("An unkown error occured")
            self.log.error(repr(inter))
            self.log.exception(exception)


def setup(bot: DatBot):
    if not Settings.keys.get(LavaLinkCog.key_loc):
        raise CogLoadingFailure(f"Missing `{LavaLinkCog.name}` configuration.")
    bot.add_cog(LavaLinkCog(bot))
