import discord
from discord.ext import commands
import json

class ToggleRoles(commands.Cog):
    hidden = True

    def __init__(self, bot):
        self.bot = bot
        self.load_config()
        self.RoleChannelID = self.config['channel_ids'].get('RoleChannel')

    def load_config(self):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

    @commands.command(help="Toggle the 'Pokemon Scarlet Violet' role. Usage: !togglesv")
    async def togglesv(self, ctx):
        RoleName = "Pokemon Scarlet Violet"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

    @commands.command(help="Toggle the 'Pokemon BDSP' role. Usage: !togglebdsp")
    async def togglebdsp(self, ctx):
        RoleName = "Pokemon BDSP"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

    @commands.command(help="Toggle the 'Pokemon Legends Arceus' role. Usage: !togglepla")
    async def togglepla(self, ctx):
        RoleName = "Pokemon Legends Arceus"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

    @commands.command(help="Toggle the 'Pokemon Sword Shield' role. Usage: !toggleswsh")
    async def toggleswsh(self, ctx):
        RoleName = "Pokemon Sword Shield"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

    @commands.command(help="Toggle the 'Animal Crossing New Horizon' role. Usage: !toggleacnh")
    async def toggleacnh(self, ctx):
        RoleName = "Animal Crossing New Horizon"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

    @commands.command(help="Toggle the 'Announcement Pings' role. Usage: !toggleannocements")
    async def toggleannocements(self, ctx):
        RoleName = "Announcement Pings"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

    @commands.command(help="Toggle the 'Tera Raiders' role. Usage: !toggleteraraider")
    async def toggleteraraider(self, ctx):
        RoleName = "Tera Raiders"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")
            
    @commands.command(help="Toggle the 'PalWorld' role. Usage: !togglepalworld")
    async def togglepalworld(self, ctx):
        RoleName = "PalWorld"
        if ctx.channel.id != self.RoleChannelID:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=RoleName)
        if not role:
            await ctx.send(f"The role '{RoleName}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{RoleName}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{RoleName}' role to {ctx.author.mention}.")

def setup(bot):
    bot.add_cog(ToggleRoles(bot))
