import disnake
from disnake.ext import commands
import random

from helper import DatBot
from helper.models import Server, SomeoneRoles
from functools import partial


# not very happy about this
# wanna move it to helper views
class RoleButtonSomeoneView(disnake.ui.View):
    Button = disnake.ui.Button
    MesInter = disnake.MessageInteraction
    message: disnake.Message
    role_name = "someone-list"

    @staticmethod
    def fetch_someone(role_list: list[disnake.Role], name: str = role_name):
        """Fetches a role with a name"""
        return [x for x in role_list if x.name == name][0]
        # fix edge case where role doesnt exist

    @disnake.ui.button(label="Join mentions", style=disnake.ButtonStyle.green)
    async def grant_role(self, button: Button, inter: MesInter):
        role = self.fetch_someone(inter.guild.roles)
        if role in inter.author.roles:
            await inter.send("You have already joined the mention list", ephemeral=True)
            return
        await inter.author.add_roles(role, reason="Joined `@someone` mention list")
        await inter.send(
            f"{inter.author.display_name} has subscribed to the `@someone` mention list"
        )

    async def on_timeout(self) -> None:
        self.grant_role.disabled = True
        await self.message.edit(
            f"This button has expired. Use my `/{SomeoneCog.name} add` to join the mention list",
            view=self,
        )


class SomeoneCog(commands.Cog):
    CmdInter = disnake.ApplicationCommandInteraction
    name = "someone"
    role_name = "someone-list"
    max_lru_size = 10

    def __init__(self, bot: DatBot):
        self.bot = bot

    async def cog_load(self):
        ...

    async def fetch_role(self, guild_id: int, role_id: int) -> disnake.Role:
        g = await self.bot.fetch_guild(guild_id)
        return g.get_role(role_id)

    @commands.register_injection
    async def get_server(self, inter: CmdInter) -> Server:
        s = await Server.find_one(inter.guild_id == Server.sid)
        if not s:
            return await Server.from_guild(inter.guild).create()
        return s

    @commands.register_injection
    async def get_someone(self, inter: CmdInter, s: Server) -> SomeoneRoles:
        return s.someone

    @commands.slash_command(name=name)
    async def cmd(self, inter: CmdInter):
        ...

    @cmd.sub_command("setup")
    async def setup_roles_(
        self,
        inter: CmdInter,
        subscribe_role: disnake.Role,
        listen_role: disnake.Role,
        s: Server,
    ):
        """Sets up the guilds someone subscriber list

        Parameters
        ----------
        subscribe_role: a role to pick from when listen role is pinged
        listen_role: a role to listen
        """
        someone = SomeoneRoles(mention=listen_role.id, subscriber=subscribe_role.id)
        s.someone = someone
        await inter.response.defer()
        await s.save()
        return await inter.send(
            f"Setup complete\nListen role: {someone.mention}\nSubscriber Role: {someone.subscriber}"
        )

    @cmd.sub_command("add")
    async def join_(self, inter: CmdInter, s: SomeoneRoles):
        """Joins the guilds someone subscriber list"""
        role = inter.guild.get_role(s.subscriber)

        await inter.author.add_roles(
            role, reason=f"User joined the `{role.name}` mention list"
        )
        await inter.response.send_message(
            f"You subscribed to the `{role.name}` mention list"
        )

    @cmd.sub_command("leave")
    async def leave_(self, inter: CmdInter, s: SomeoneRoles):
        """Leaves the guilds Someone subscriber list"""
        role = inter.guild.get_role(s.subscriber)

        await inter.author.remove_roles(
            role, reason=f"User left the `{role.name}` mention list"
        )
        await inter.response.send_message(
            f"You have unsubscribed to the `{role.name}` mention list"
        )

    @staticmethod
    def _predicate(member: disnake.Member, role: disnake.Role, author_id: int):
        return (
            False
            if member.id == author_id
            else any(
                [
                    o
                    for o in member.roles
                    if o.id == role.id and not member.id == author_id
                ]
            )
        )

    @commands.Cog.listener("on_message")
    async def someone_(self, message: disnake.Message):
        gid = message.guild.id
        s = await Server.find_one(Server.sid == gid)

        if len(message.role_mentions) <= 0 and s is None:
            return

        someone = s.someone
        if any([i for i in message.role_mentions if someone.mention == i.id]):
            a = await self.fetch_role(gid, someone.subscriber)
            b = (
                await message.guild.fetch_members()
                .filter(partial(self._predicate, role=a, author_id=message.author.id))
                .flatten()
            )
            await message.channel.send(random.choice(b).mention)


def setup(bot: DatBot):
    bot.add_cog(SomeoneCog(bot))
