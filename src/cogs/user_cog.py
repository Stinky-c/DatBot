from typing import TypeAlias

import disnake
from disnake.ext import commands
from helper import Cog, CogMetaData, DatBot, LinkTuple, LinkView


class UserCog(Cog):
    CmdInter: TypeAlias = disnake.ApplicationCommandInteraction
    GuildInter: TypeAlias = disnake.GuildCommandInteraction
    name = "user"

    @commands.user_command(name="View Song")
    async def spotifysong(self, inter: CmdInter, user: disnake.Member):
        if not any(isinstance(x, disnake.Spotify) for x in user.activities):
            await inter.send("That person is not listening to spotify", ephemeral=True)
            return

        spot = next(
            (x for x in list(user.activities) if isinstance(x, disnake.Spotify)), None
        )
        embed_dict = {
            "type": "image",
            "title": spot.title,
            "description": ", ".join(spot.artists),
            "color": spot.color.value,
            "image": {"url": spot.album_cover_url},
        }

        await inter.send(
            embed=disnake.Embed.from_dict(embed_dict),
            view=LinkView(LinkTuple("Track Link", spot.track_url)),
        )

    @commands.user_command(name="User Info")
    async def user_info_(self, inter: disnake.CmdInter, user: disnake.Member):
        user_roles = "\n".join([i.mention for i in user.roles[1:]])

        if user.premium_since:
            premium = disnake.utils.format_dt(user.premium_since, "F")
        else:
            premium = "Never"

        embed_dict = {
            "color": disnake.Color.dark_gray(),
            "timestamp": disnake.utils.utcnow().isoformat(),
            "author": {
                "name": user.display_name,
                "icon_url": user.display_avatar.url,
            },
            "fields": [
                {"name": "Name", "value": user.name, "inline": True},
                {
                    "name": "Roles",
                    "value": user_roles,
                    "inline": True,
                },
                {
                    "name": "Account creation date",
                    "value": disnake.utils.format_dt(user.created_at, "F"),
                    "inline": True,
                },
                {
                    "name": "Join Date",
                    "value": disnake.utils.format_dt(user.joined_at, "F"),
                    "inline": True,
                },
                {
                    "name": "Boosting since:",
                    "value": premium,
                    "inline": True,
                },
            ],
            "footer": {"text": f"ID: {inter.id}"},
        }

        await inter.send(embed=disnake.Embed.from_dict(embed_dict))


def setup(bot: DatBot):
    bot.add_cog(UserCog(bot))


metadata = CogMetaData(
    name=UserCog.name,
    key=UserCog.key_loc,
    require_key=UserCog.key_enabled,
)
