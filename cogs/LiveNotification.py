import discord
from discord.ext import commands
import os
import json
import requests

class LiveNotification(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = self.load_config()
        self.twitchIcon = os.path.join('images', 'twitchicon.png')
        self.youtubeIcon = os.path.join('images', 'youtubeicon.png')

    def load_config(self):
        with open('config.json', 'r') as f:
            return json.load(f)

    async def TwitchLiveNotification(self):
        twitch_api_url = f'https://api.twitch.tv/helix/streams?user_login={self.config["twitch_username"]}'
        headers = {'Client-ID': self.config['twitch_client_id']}
        response = requests.get(twitch_api_url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            if data['data']:
                await self.LiveEmbedNotification(
                f'Hey everyone! {self.config["twitch_username"]} is now live on Twitch!',
                f'https://www.twitch.tv/{self.config["twitch_username"]}',
                self.twitchIcon
            )

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

    async def LiveEmbedNotification(self, message, link, icon):
        embed = discord.Embed(
            title='Live Notification',
            description=message,
            color=discord.Color.green()
        )
        embed.set_author(name=self.bot.user.name, icon_url=self.bot.user.avatar_url)
        embed.set_thumbnail(url=f'attachment://{icon}')
        embed.add_field(name='Watch Now', value=f'Click Here')
        await self.bot.get_channel(self.config['stream_channel_id']).send(embed=embed, file=discord.File(icon))

    @commands.command()
    async def islive(self, ctx):
        await self.TwitchLiveNotification()
        # await self.YoutubeLiveNotification()

def setup(bot):
    bot.add_cog(LiveNotification(bot))