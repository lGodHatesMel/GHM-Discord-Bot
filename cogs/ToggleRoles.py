import discord
from discord.ext import commands
from utils.utils import custom_emojis
from config import CHANNELIDS
import random


class ToggleRoles(commands.Cog):
    hidden = True

    def __init__(self, bot):
        self.bot = bot
        self.RoleChannelID = CHANNELIDS.get('RoleChannel')

    async def ToggleRole(self, ctx, RoleName, emoji_name=None):
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send(f"You can only use this command in the <#{CHANNELIDS['RoleChannel']}> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role **{RoleName}** does not exist on this server.")
            return

        emoji = custom_emojis.get(emoji_name, ':question:')
        title = f"{emoji} {RoleName}"

        if role in ctx.author.roles:
            embed = discord.Embed(title=title, color=discord.Color.red())
            await ctx.author.remove_roles(role)
            embed.description = f"Alright {ctx.author.mention}, I've removed the **{RoleName}** role from you. If you need it back, just ask!"
        else:
            random_color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            while random_color == discord.Color.red():
                random_color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            embed = discord.Embed(title=title, color=random_color)
            await ctx.author.add_roles(role)
            embed.description = f"Congratulations {ctx.author.mention}! You've been given the **{RoleName}** role. Enjoy!"
        await ctx.message.reply(embed=embed)

    @commands.command(help="Toggle the 'Pokemon Scarlet Violet' role. Usage: !togglesv")
    async def togglesv(self, ctx):
        await self.ToggleRole(ctx, "Pokemon Scarlet Violet", "sv")

    @commands.command(help="Toggle the 'Pokemon BDSP' role. Usage: !togglebdsp")
    async def togglebdsp(self, ctx):
        await self.ToggleRole(ctx, "Pokemon BDSP", "bdsp")

    @commands.command(help="Toggle the 'Pokemon Legends Arceus' role. Usage: !togglepla")
    async def togglepla(self, ctx):
        await self.ToggleRole(ctx, "Pokemon Legends Arceus", "arceus")

    @commands.command(help="Toggle the 'Pokemon Sword Shield' role. Usage: !toggleswsh")
    async def toggleswsh(self, ctx):
        await self.ToggleRole(ctx, "Pokemon Sword Shield", "swsh")

    @commands.command(help="Toggle the 'Animal Crossing New Horizon' role. Usage: !toggleacnh")
    async def toggleacnh(self, ctx):
        await self.ToggleRole(ctx, "Animal Crossing New Horizon", "acnh")

    @commands.command(help="Toggle the 'Announcement Pings' role. Usage: !toggleannocements")
    async def toggleannocements(self, ctx):
        await self.ToggleRole(ctx, "Announcement Pings", "pinged")

    @commands.command(help="Toggle the 'PalWorld' role. Usage: !togglepalworld")
    async def togglepalworld(self, ctx):
        await self.ToggleRole(ctx, "PalWorld", "pw_grizzbolt")

    @commands.command(help="Toggle the 'PokeBotAnnouncements' role. Usage: !togglepokebots")
    async def togglepokebots(self, ctx):
        await self.ToggleRole(ctx, "Poke Bot Announcements", "ping")

def setup(bot):
    bot.add_cog(ToggleRoles(bot))