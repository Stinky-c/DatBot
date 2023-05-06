from typing import TypeAlias

import disnake
import mafic
from disnake.ext import commands
from helper import (
    Cog,
    CogLoadingFailure,
    CogMetaData,
    DatBot,
    Emojis,
    Settings,
    cblock,
    jdumps,
    uid,
)
from helper.cbot import LavaPlayer

# TODO: update to use REST based API
# TODO: add playlist
# TODO: add timeout feature
# TODO: add looping; enum for playlist loop & song loop
# TODO: add url to embed


class LavaLinkCog(Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "music"
    key_enabled = True
    key_loc = "music"

    def __init__(self, bot: DatBot):
        super().__init__(bot)
        self.nodes = mafic.NodePool(bot)

    async def connect_node(self):
        """Connect to our Lavalink nodes."""
        await self.bot.wait_until_ready()

        if len(self.nodes.nodes) > 0:
            self.log.info("Nodes already loaded")
            return False

        conf = Settings.keys.get(self.key_loc)
        if isinstance(conf, list):
            for i in conf:
                await self.nodes.create_node(
                    host=i["host"],
                    port=i["port"],
                    password=i["password"],
                    label=i.get("label"),
                )
        else:
            await self.nodes.create_node(
                host=conf["host"],
                port=conf["port"],
                password=conf["password"],
                label=conf.get("label", uid()),
            )
        return True

    async def cog_load(self):
        await self.connect_node()

    def is_connected():
        async def predicate(inter: disnake.CmdInter):
            connected = bool(inter.author.voice)
            if not connected:
                await inter.send(
                    "You must be connected to a voice channel to use this command"
                )
            return connected

        return commands.check(predicate)

    def bot_connected():
        async def predicate(inter: disnake.CmdInter):
            connected = bool(inter.guild.voice_client)
            if not connected:
                await inter.send(
                    "Bot must be connected to a voice channel to use this command"
                )
            return connected

        return commands.check(predicate)

    @staticmethod
    def embed_factory(track: mafic.Track) -> dict:
        thumbnail_urls = {
            "youtube": "https://img.youtube.com/vi/{track_id}/maxresdefault.jpg"
        }
        image_url = thumbnail_urls.get(track.source, "").format(
            track_id=track.identifier
        )

        return {
            "type": "image",
            "title": track.title,
            "description": track.author or "unknown",
            "color": disnake.Color.random(seed=track.identifier),
            "image": {"url": image_url},
            "timestamp": disnake.utils.utcnow().isoformat(),
        }

    @commands.register_injection
    async def get_player(self, inter: CmdInter) -> LavaPlayer:
        vc: LavaPlayer
        if not inter.guild.voice_client:
            vc = await inter.author.voice.channel.connect(cls=LavaPlayer)
            self.log.info(f"Creating voice connection: '{inter.guild!s}'")
        else:
            vc = inter.guild.voice_client
        vc.managed = inter.channel
        return vc

    @commands.Cog.listener("on_track_end")
    async def on_track_end(self, event: mafic.TrackEndEvent):
        player: LavaPlayer = event.player
        self.log.debug(f"Track ended in '{player.guild.id}': {event.reason}")
        if len(player.queue) <= 0:
            return
        to_play = player.queue.pop(0)
        await player.play(to_play)
        embed = self.embed_factory(to_play)
        await player.managed.send(
            f"Now playing '{to_play.title}'", embed=disnake.Embed.from_dict(embed)
        )

    @commands.Cog.listener("on_track_exception")
    async def on_track_exception(self, *args, **kwargs):  # TODO
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
        self, inter: CmdInter, vc: LavaPlayer, search: str, replace: bool = False
    ):
        """Play a song from youtube with the given search query or a url.

        Parameters
        ----------
        search: a youtube search term or youtube URL
        replace: Replaces the current song instead of queuing
        """

        await inter.response.defer()
        to_play = await vc.fetch_tracks(search, search_type=mafic.SearchType.YOUTUBE)

        if to_play is None:
            return await inter.send("Unable to find a song")
        elif isinstance(to_play, list):
            next_play = to_play[0]
        elif isinstance(to_play, mafic.Playlist):
            next_play = to_play.tracks.pop(to_play.selected_track)
            vc.queue.extend(to_play.tracks)
        elif isinstance(to_play, mafic.Track):
            next_play = to_play
        else:
            self.log.error("Something went really wrong")
            return await inter.send("How")

        if vc.current is None or replace:
            await vc.play(next_play)
            message = f"Now playing '{next_play.title}'"
        else:
            vc.queue.append(next_play)
            message = f"Now queuing '{next_play.title}'"

        embed = self.embed_factory(next_play)
        await inter.send(message, embed=disnake.Embed.from_dict(embed))
        self.log.debug(message + f" in '{inter.guild!s}'")

    @cmd.sub_command("playing")
    @bot_connected()
    async def playing_(self, inter: CmdInter, vc: LavaPlayer):
        """Displays the current playing song"""
        current = vc.current
        if current is None:
            return await inter.send("The bot is not currently playing")
        embed = self.embed_factory(current)
        await inter.send(embed=disnake.Embed.from_dict(embed))

    @cmd.sub_command("skip")
    @bot_connected()
    async def skip_(self, inter: CmdInter, vc: LavaPlayer):
        """Skips the current song"""
        # TODO: add skip to queue index
        if not vc.current:
            return await inter.send("Not currently playing!")
        await vc.seek(vc.current.length * 1000)
        # source length is in seconds and seek uses milliseconds
        await inter.send("Skipping!")

    @cmd.sub_command("quit")
    @bot_connected()
    async def quit_(self, inter: CmdInter, vc: LavaPlayer):
        """Disconnects bot from voice channel"""
        await vc.destroy()
        await inter.send(f"Goodbye {Emojis.wave}")

    @cmd.sub_command("queue")
    @bot_connected()
    async def queue_(self, inter: CmdInter, vc: LavaPlayer):
        """List all items in the queue"""
        if len(vc.queue) <= 0:
            return await inter.send("The queue is empty")
        base = "\n".join([i.title for i in vc.queue])
        await inter.send(
            f"There are {len(vc.queue)} items in the queue.\n" + cblock(base)
        )
        self.log.debug(base)

    @cmd.sub_command("pause")
    async def pause_(self, inter: CmdInter, vc: LavaPlayer):
        """Toggle pausing"""
        state = vc.paused
        await vc.pause(not state)
        await inter.send(f"player is now {'un'*state}paused", delete_after=3)

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
        if len(self.nodes.nodes) <= 0:
            return await inter.send("I have zero connected nodes")
        nodes = "\n".join([repr(i) for i in self.nodes.nodes])
        await inter.send(
            f"I have {len(self.nodes.nodes)} connected nodes\n```{nodes}```"
        )

    @commands.is_owner()
    @cmd.sub_command_group("dev", guild_ids=Settings.bot.dev_guilds)
    async def dev_(self, inter: CmdInter):
        """Allows for viewing & manipulation of internal data"""
        self.log.debug(f"{inter.author} @ {inter.guild.name}: {inter.id}")

    @dev_.sub_command("players")
    async def players_(self, inter: CmdInter):
        """Returns a list of vc which players are connected to"""
        tmp = []
        for node in self.nodes.nodes:
            for player in node.players:
                tmp.append(player.guild.id)
        await inter.send(jdumps(tmp))

    @dev_.sub_command("current")
    async def current_(self, inter: CmdInter, vc: LavaPlayer):
        """Returns info about the guild player."""
        embed = (
            disnake.Embed(
                title=f"'{vc.guild!s}' Statistics",
                timestamp=disnake.utils.utcnow().isoformat(),
                color=disnake.Color.random(seed=vc.current.id),
            )
            .add_field("Node", vc.node.label)
            .add_field("Ping", vc.ping)
            .add_field("Queue length", len(vc.queue))
            .add_field("Last update", vc._last_update)
            .add_field("Playing?", bool(vc.current))
            .add_field(
                "Track Position",
                f"{round(vc.position/1000/60,2)}/{round(vc.current.length/1000/60,2)}",
            )
        )

        await inter.send(embed=embed)

    @cmd.error
    async def on_error(
        self, inter: CmdInter, exception: commands.CommandInvokeError, *args, **kwargs
    ):  # TODO find better type hint for exception
        # TODO find the best error handling method
        # exceptions are still printed on error even after handling
        if isinstance(exception, commands.CheckFailure):
            self.log.debug(f"'{inter.author!s}' was not connected in '{inter.guild!s}'")
            return
        elif isinstance(
            exception.original, mafic.errors.TrackLoadException
        ):  # Might not be `CommandInvokeError`
            self.log.error("Song failed loading")
            return await inter.send("There was an issue loading the next song.")
        elif isinstance(exception.original, mafic.errors.MaficException):
            self.log.error("Unknown lavalink exception")
            return await inter.send("Unknown player error")
        else:
            self.log.error(repr(inter))
            await self.bot.send_exception(exception)


def setup(bot: DatBot):
    if not Settings.keys.get(LavaLinkCog.key_loc):
        raise CogLoadingFailure(f"Missing `{LavaLinkCog.name}` configuration.")
    bot.add_cog(LavaLinkCog(bot))


def metadata(bot: DatBot) -> CogMetaData:
    return CogMetaData(
        name=LavaLinkCog.name,
        key=LavaLinkCog.key_loc,
        require_key=LavaLinkCog.key_enabled,
    )
