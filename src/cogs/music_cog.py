import asyncio
from typing import Any, Dict, Optional

import disnake
import yt_dlp as youtube_dl  # type: ignore
from disnake.ext import commands
from helper import DatBot, build_path, Settings

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
    "paths": {
        "home": build_path(Settings.dir.get("music").path),
        "temp": build_path(Settings.dir.get("temp").path),
    },
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(disnake.PCMVolumeTransformer):
    def __init__(
        self, source: disnake.AudioSource, *, data: Dict[str, Any], volume: float = 0.5
    ):
        super().__init__(source, volume)

        self.title = data.get("title")

    @classmethod
    async def from_url(
        cls,
        url,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        stream: bool = False,
    ):
        loop = loop or asyncio.get_event_loop()
        data: Any = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)

        return cls(disnake.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Music(commands.Cog):
    CmdInter = disnake.ApplicationCommandInteraction

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.slash_command(name="music")
    async def music_(self, inter: CmdInter):
        pass

    @music_.sub_command()
    async def join(self, inter: CmdInter, *, channel: disnake.VoiceChannel):
        """Joins a voice channel"""

        if inter.guild.voice_client is not None:
            await inter.guild.voice_client.move_to(channel)
        else:
            await channel.connect()
        await inter.send("connected")

    @music_.sub_command()
    async def play(self, inter: CmdInter, *, query: str):
        """Plays a file from the local filesystem"""
        await self.ensure_voice(inter)
        source = disnake.PCMVolumeTransformer(disnake.FFmpegPCMAudio(query))
        inter.guild.voice_client.play(
            source, after=lambda e: print(f"Player error: {e}") if e else None
        )

        await inter.send(f"Now playing: {query}")

    @music_.sub_command()
    async def yt(self, inter: CmdInter, *, url: str):
        """Plays from a url (almost anything youtube_dl supports)"""
        await self._play_url(inter, url=url, stream=False)

    @music_.sub_command()
    async def stream(self, inter: CmdInter, *, url: str):
        """Streams from a url (same as yt, but doesn't predownload)"""
        await self._play_url(inter, url=url, stream=True)

    async def _play_url(self, inter: CmdInter, *, url: str, stream: bool):
        await self.ensure_voice(inter)
        await inter.response.defer()
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=stream)
        inter.guild.voice_client.play(
            player, after=lambda e: print(f"Player error: {e}") if e else None
        )

        await inter.send(f"Now playing: {player.title}")

    @music_.sub_command()
    async def volume(self, inter: CmdInter, volume: int):
        """Changes the player's volume"""

        if inter.guild.voice_client is None:
            return await inter.send("Not connected to a voice channel.")

        inter.guild.voice_client.source.volume = volume / 100
        await inter.send(f"Changed volume to {volume}%")

    @music_.sub_command()
    async def stop(self, inter: CmdInter):
        """Stops and disconnects the bot from voice"""
        await inter.guild.voice_client.disconnect()
        await inter.send("Goodbye")

    async def ensure_voice(self, inter: CmdInter):
        if inter.guild.voice_client is None:
            if inter.author.voice:
                await inter.author.voice.channel.connect()
            else:
                await inter.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif inter.guild.voice_client.is_playing():
            inter.guild.voice_client.stop()


def setup(bot: DatBot):
    bot.add_cog(Music(bot))
