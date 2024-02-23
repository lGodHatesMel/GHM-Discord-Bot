import discord
from discord.ext import commands
import json
import random

class ToggleRoles(commands.Cog):
    hidden = True

    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.RoleChannelID = self.config['channel_ids'].get('RoleChannel')

    def load_config(self):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

    async def ToggleRole(self, ctx, RoleName):
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role **{RoleName}** does not exist on this server.")
            return

        if role in ctx.author.roles:
            embed = discord.Embed(title=RoleName, color=discord.Color.red())
            await ctx.author.remove_roles(role)
            embed.description = f"Removed the **{RoleName}** role from {ctx.author.mention}."
        else:
            random_color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            while random_color == discord.Color.red():
                random_color = discord.Color.from_rgb(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            embed = discord.Embed(title=RoleName, color=random_color)
            await ctx.author.add_roles(role)
            embed.description = f"Gave the '{RoleName}' role to {ctx.author.mention}."

        await ctx.send(embed=embed)

    @commands.command(help="Toggle the 'Pokemon Scarlet Violet' role. Usage: !togglesv")
    async def togglesv(self, ctx):
        await self.ToggleRole(ctx, "Pokemon Scarlet Violet")

    @commands.command(help="Toggle the 'Pokemon BDSP' role. Usage: !togglebdsp")
    async def togglebdsp(self, ctx):
        await self.ToggleRole(ctx, "Pokemon BDSP")

    @commands.command(help="Toggle the 'Pokemon Legends Arceus' role. Usage: !togglepla")
    async def togglepla(self, ctx):
        await self.ToggleRole(ctx, "Pokemon Legends Arceus")

    @commands.command(help="Toggle the 'Pokemon Sword Shield' role. Usage: !toggleswsh")
    async def toggleswsh(self, ctx):
        await self.ToggleRole(ctx, "Pokemon Sword Shield")

    @commands.command(help="Toggle the 'Animal Crossing New Horizon' role. Usage: !toggleacnh")
    async def toggleacnh(self, ctx):
        await self.ToggleRole(ctx, "Animal Crossing New Horizon")

    @commands.command(help="Toggle the 'Announcement Pings' role. Usage: !toggleannocements")
    async def toggleannocements(self, ctx):
        await self.ToggleRole(ctx, "Announcement Pings")

    @commands.command(help="Toggle the 'Tera Raiders' role. Usage: !toggleteraraider")
    async def toggleteraraider(self, ctx):
        await self.ToggleRole(ctx, "Tera Raiders")

    @commands.command(help="Toggle the 'PalWorld' role. Usage: !togglepalworld")
    async def togglepalworld(self, ctx):
        await self.ToggleRole(ctx, "PalWorld")

def setup(bot):
    bot.add_cog(ToggleRoles(bot))