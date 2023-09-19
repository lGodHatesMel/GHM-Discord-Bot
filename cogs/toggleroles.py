import discord
from discord.ext import commands
import json

class ToggleRoles(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.load_config()

    def load_config(self):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

    @commands.command(name='togglesv')
    async def toggle_sv(self, ctx):
        role_name = "Pokemon Scarlet Violet"
        role_channel_id = self.config.get('role_channel_id')
        if ctx.channel.id != role_channel_id:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The role '{role_name}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{role_name}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{role_name}' role to {ctx.author.mention}.")

    @commands.command(name='togglebdsp')
    async def toggle_sv(self, ctx):
        role_name = "Pokemon BDSP"
        role_channel_id = self.config.get('role_channel_id')
        if ctx.channel.id != role_channel_id:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The role '{role_name}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{role_name}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{role_name}' role to {ctx.author.mention}.")

    @commands.command(name='togglepla')
    async def toggle_sv(self, ctx):
        role_name = "Pokemon Legends Arceus"
        role_channel_id = self.config.get('role_channel_id')
        if ctx.channel.id != role_channel_id:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The role '{role_name}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{role_name}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{role_name}' role to {ctx.author.mention}.")

    @commands.command(name='toggleswsh')
    async def toggle_sv(self, ctx):
        role_name = "Pokemon Sword Shield"
        role_channel_id = self.config.get('role_channel_id')
        if ctx.channel.id != role_channel_id:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The role '{role_name}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{role_name}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{role_name}' role to {ctx.author.mention}.")

    @commands.command(name='toggleacnh')
    async def toggle_sv(self, ctx):
        role_name = "Animal Crossing New Horizon"
        role_channel_id = self.config.get('role_channel_id')
        if ctx.channel.id != role_channel_id:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The role '{role_name}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{role_name}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{role_name}' role to {ctx.author.mention}.")

    @commands.command(name='toggleannocement')
    async def toggle_sv(self, ctx):
        role_name = "Annocement Pings"
        role_channel_id = self.config.get('role_channel_id')
        if ctx.channel.id != role_channel_id:
            await ctx.send("You can only use this command in the <#956769501607755806> channel.")
            return

        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if not role:
            await ctx.send(f"The role '{role_name}' does not exist on this server.")
            return

        if role in ctx.author.roles:
            await ctx.author.remove_roles(role)
            await ctx.send(f"Removed the '{role_name}' role from {ctx.author.mention}.")
        else:
            await ctx.author.add_roles(role)
            await ctx.send(f"Gave the '{role_name}' role to {ctx.author.mention}.")

def setup(bot):
    bot.add_cog(ToggleRoles(bot))
