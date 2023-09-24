import discord
from discord.ext import commands
import json
import traceback

class ExtensionManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        # Cleanup code if needed
        pass

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reload(self, ctx, extension: str):
        try:
            self.bot.unload_extension(extension)
            self.bot.load_extension(extension)
            await ctx.send(f":white_check_mark: Extension '{extension}' reloaded.")
        except Exception as e:
            await ctx.send(f":x: Operation failed!\n\n{type(e).__name__}: {e}")
            traceback.print_exc()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def load(self, ctx, extension: str):
        try:
            self.bot.load_extension(extension)
            await ctx.send(f":white_check_mark: Extension '{extension}' loaded.")
        except Exception as e:
            await ctx.send(f":x: Operation failed!\n\n{type(e).__name__}: {e}")
            traceback.print_exc()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def refreshconfig(self, ctx):
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)

        self.bot.config = config
        try:
            await ctx.send(":white_check_mark: Config.json has been refreshed!")
        except Exception as e:
            await ctx.send(f":x: Operation failed!\n\n{type(e).__name__}: {e}")
            traceback.print_exc()

def setup(bot):
    bot.add_cog(ExtensionManagement(bot))
