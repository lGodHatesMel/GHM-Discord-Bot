import discord
from discord.ext import commands
from discord.ext import tasks
import os
import json
import aiohttp
import requests

class LiveNotification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.twitchIcon = 'https://raw.githubusercontent.com/lGodHatesMel/RandomResources/main/Images/twitchicon.png'
        self.youtubeIcon = 'https://raw.githubusercontent.com/lGodHatesMel/RandomResources/main/Images/youtubeicon.png'
        self.is_live = False
        self.check_live.start()

    def load_config(self):
        with open('config.json', 'r') as f:
            return json.load(f)

    @tasks.loop(minutes=5.0)
    async def check_live(self):
        TwitchAPI = f'https://api.twitch.tv/helix/streams?user_login={self.config["twitch_username"]}'
        headers = {
            'Client-ID': self.config['twitch_client_id'],
            'Authorization': f'Bearer {self.config["twitch_oauth_token"]}'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(TwitchAPI, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data'] and not self.is_live:
                        self.is_live = True
                        user = await self.bot.fetch_user(self.config['owner_id'])
                        game_id = data['data'][0]['game_id']
                        title = data['data'][0]['title']
                        game_name = await self.get_game_name(game_id, headers)
                        await self.LiveEmbedNotification(
                            self.bot.get_channel(self.config['channel_ids']['StreamChannel']),
                            f'Hey everyone! {user.mention} is now live on Twitch!',
                            f'https://www.twitch.tv/{self.config["twitch_username"]}',
                            self.twitchIcon,
                            game_name,
                            title
                        )
                    elif not data['data']:
                        self.is_live = False

    @check_live.before_loop
    async def before_check_live(self):
        await self.bot.wait_until_ready()

    # async def YoutubeLiveNotification(self):
    #     youtube_api_url = f'https://www.googleapis.com/youtube/v3/search?part=snippet&channelId={self.config["youtube_channel_id"]}&eventType=live&type=video&key={self.config["youtube_api_key"]}'
    #     response = requests.get(youtube_api_url)

    #     if response.status_code == 200:
    #         data = response.json()
    #         if data.get('items'):
    #             await self.LiveEmbedNotification(
    #                 f'Hey everyone! {self.config["youtube_channel_name"]} is now live on YouTube!',
    #                 f'https://www.youtube.com/channel/{self.config["youtube_channel_id"]}',
    #                 self.youtubeIcon
    #             )

    async def TwitchLiveNotification(self, ctx):
        TwitchAPI = f'https://api.twitch.tv/helix/streams?user_login={self.config["twitch_username"]}'
        headers = {
            'Client-ID': self.config['twitch_client_id'],
            'Authorization': f'Bearer {self.config["twitch_oauth_token"]}'
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(TwitchAPI, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data['data']:
                        user = await self.bot.fetch_user(self.config['owner_id'])
                        game_id = data['data'][0]['game_id']
                        title = data['data'][0]['title']
                        game_name = await self.get_game_name(game_id, headers)
                        await self.LiveEmbedNotification(
                            ctx,
                            f'Hey everyone! {user.mention} is now live on Twitch!',
                            f'https://www.twitch.tv/{self.config["twitch_username"]}',
                            self.twitchIcon,
                            game_name,
                            title
                        )

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
        streamlink = f'https://www.twitch.tv/{self.config["twitch_username"]}'
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
        # embed.add_field(name='Message', value=f'[Message Here]', inline=False)

        await ctx.send(embed=embed)

    @commands.command()
    async def islive(self, ctx):
        try:
            await self.TwitchLiveNotification(ctx)
        except Exception as e:
            await ctx.send(f'An error occurred: {e}')

def setup(bot):
    bot.add_cog(LiveNotification(bot))