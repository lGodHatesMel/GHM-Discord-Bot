import requests
import json
import discord
from discord.ext import commands, tasks
import utils.utils as utils
from config import TOKEN_REFRESHER_ENABLED

class TokenRefresher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token_config = self.LoadTokenConfig()
        self.RefreshToken.start()

    def cog_unload(self):
        self.RefreshToken.cancel()

    def LoadTokenConfig(self):
        with open('token-config.json', 'r') as file:
            return json.load(file)

    def RunTokenRefresher(self):
        return TOKEN_REFRESHER_ENABLED

    @tasks.loop(hours=3)
    async def RefreshToken(self):
        if not self.RunTokenRefresher():
            return

        token_url = 'https://id.twitch.tv/oauth2/token'
        params = {
            'client_id': self.token_config['client_id'],
            'client_secret': self.token_config['client_secret'],
            'refresh_token': self.token_config['refresh_token'],
            'grant_type': 'refresh_token'
        }

        response = requests.post(token_url, data=params)
        if response.status_code == 200:
            data = response.json()
            access_token = data['access_token']
            print(f"=====================================================")
            print(f"===== Access Token Refreshed @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')} ====")
            print(f"==== New Token: ({access_token}) ====")
            print(f"=====================================================")
        else:
            print(f'Failed to refresh access token. Status code: {response.status_code}')
            print(response.text)

    @RefreshToken.before_loop
    async def BeforeRefreshToken(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(TokenRefresher(bot))