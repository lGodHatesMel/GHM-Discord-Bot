import requests
from discord.ext import commands

class TwitchRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='1raidrequest')
    async def raid_request(self, ctx):
        # add actions
        await ctx.send('Command was triggered! ??')

    def listen_to_twitch(self):
        # Add the code for registering with Twitch here
        pass

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        # Register the Twitch event listener
        self.listen_to_twitch()

def setup(bot):
    bot.add_cog(TwitchRewards(bot))