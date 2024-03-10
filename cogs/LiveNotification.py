import discord
from discord.ext import commands
from discord.ext import tasks
from config import TWITCH, ROLEIDS, CHANNEL_IDS
import aiohttp

class LiveNotification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.twitchIcon = 'https://raw.githubusercontent.com/lGodHatesMel/RandomResources/main/Images/twitchicon.png'
        # self.youtubeIcon = 'https://raw.githubusercontent.com/lGodHatesMel/RandomResources/main/Images/youtubeicon.png'
        self.is_live = False
        self.check_live.start()

    @tasks.loop(minutes=20.0)
    async def check_live(self):
        TwitchAPI = f'https://api.twitch.tv/helix/streams?user_login={TWITCH["twitch_username"]}'
        headers = {
            'Client-ID': TWITCH["twitch_client_id"],
            'Authorization': f'Bearer {TWITCH["twitch_oauth_token"]}'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(TwitchAPI, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data'] and not self.is_live:
                        self.is_live = True
                        user = await self.bot.fetch_user(ROLEIDS["OWNERID"])
                        game_id = data['data'][0]['game_id']
                        title = data['data'][0]['title']
                        game_name = await self.get_game_name(game_id, headers)
                        await self.LiveEmbedNotification(
                            self.bot.get_channel(CHANNEL_IDS['StreamChannel']),
                            f'Hey everyone! {user.mention} is now live on Twitch!',
                            f'https://www.twitch.tv/{TWITCH["twitch_username"]}',
                            self.twitchIcon,
                            game_name,
                            title
                        )
                    elif not data['data']:
                        self.is_live = False

    @check_live.before_loop
    async def before_check_live(self):
        await self.bot.wait_until_ready()

    async def get_game_name(self, game_id, headers):
        TwitchAPI = f'https://api.twitch.tv/helix/games?id={game_id}'

        async with aiohttp.ClientSession() as session:
            async with session.get(TwitchAPI, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        return data['data'][0]['name']
        return None

    async def LiveEmbedNotification(self, ctx, message, streamlink, icon, game_name, title):
        streamlink = f'https://www.twitch.tv/{TWITCH["twitch_username"]}'
        embed = discord.Embed(
            title='Twitch Live Stream Notification',
            description=message,
            color=discord.Color.green()
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=icon)
        embed.add_field(name='Stream Title', value=title, inline=False)
        embed.add_field(name='Game', value=game_name, inline=True)
        embed.add_field(name='Watch Now', value=f'[Stream Link]({streamlink})', inline=True)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(LiveNotification(bot))