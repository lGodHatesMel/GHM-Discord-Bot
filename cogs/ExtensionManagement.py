import asyncio
import os
import discord
from discord.ext import commands
import importlib
import config
import sys
import traceback

class ExtensionManagement(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def cog_unload(self):
        # Cleanup code if needed
        pass

    # def cog_unload(self):
    #     self.my_background_task.cancel()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reloadcogs(self, ctx, *, cog: str = None):
        if not cog:
            async with ctx.typing():
                embed = discord.Embed(
                    title="Reloading all cogs!",
                    color=discord.Color.red(),
                    timestamp=ctx.message.created_at
                )
                for ext in os.listdir("./cogs/"):
                    if ext.endswith(".py") and not ext.startswith("_"):
                        try:
                            self.bot.unload_extension(f"cogs.{ext[:-3]}")
                            self.bot.load_extension(f"cogs.{ext[:-3]}")
                            embed.add_field(
                                name=f"Reloaded: `{ext}`", value='\uFEFF', inline=False)
                        except Exception as e:
                            embed.add_field(
                                name=f"Failed to reload: `{ext}`", value=e, inline=False)
                        await asyncio.sleep(0.5)
                await ctx.send(embed=embed)
        else:
            async with ctx.typing():
                embed = discord.Embed(
                    title=f"Reloading {cog}!",
                    color=discord.Color.red(),
                    timestamp=ctx.message.created_at
                )
                ext = f"{cog.lower()}.py"
                if not os.path.exists(f"./cogs/{ext}"):
                    embed.add_field(
                        name=f"Failed to reload: `{ext}`", value="This cog does not exist.", inline=False)

                elif ext.endswith(".py") and not ext.startswith("_"):
                    try:
                        self.bot.unload_extension(f"cogs.{ext[:-3]}")
                        self.bot.load_extension(f"cogs.{ext[:-3]}")
                        embed.add_field(
                            name=f"Reloaded: `{ext}`", value='\uFEFF', inline=False)
                    except Exception:
                        desired_trace = traceback.format_exc()
                        embed.add_field(
                            name=f"Failed to reload: `{ext}`", value=desired_trace, inline=False)
                await ctx.send(embed=embed)

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
    async def stop(self, ctx, extension: str):
        try:
            self.bot.unload_extension(extension)
            await ctx.send(f":white_check_mark: Extension '{extension}' stopped.")
        except Exception as e:
            await ctx.send(f":x: Operation failed!\n\n{type(e).__name__}: {e}")
            traceback.print_exc()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def refreshconfig(self, ctx):
        try:
            importlib.reload(config)
            self.bot.config = vars(config)
            await ctx.send(":white_check_mark: Config.py has been refreshed!")
        except Exception as e:
            await ctx.send(f":x: Operation failed!\n\n{type(e).__name__}: {e}")
            traceback.print_exc()

    @commands.command(hidden=True)
    @commands.is_owner()
    async def reloadutils(self, ctx, *, module: str):
        try:
            module_name = f"utils.{module}"
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
                await ctx.send(f"Reloaded utils module `{module}`")
            else:
                await ctx.send(f"No such utils module `{module}`")
        except Exception as e:
            await ctx.send(f"Failed to reload utils module `{module}`: {e}")

def setup(bot):
    bot.add_cog(ExtensionManagement(bot))