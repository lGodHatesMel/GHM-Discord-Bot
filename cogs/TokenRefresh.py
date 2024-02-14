import requests
import json
import discord
from discord.ext import commands, tasks
import utils

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
        with open('config.json', 'r') as file:
            config = json.load(file)
        return config.get('token_refresher_enabled', False)

    @tasks.loop(hours=3)
    async def RefreshToken(self):
        if not self.RunTokenRefresher():
            return

        # Define the token refresh endpoint
        token_url = 'https://id.twitch.tv/oauth2/token'

        # Set the parameters for the POST request to refresh the token
        params = {
            'client_id': self.token_config['client_id'],
            'client_secret': self.token_config['client_secret'],
            'refresh_token': self.token_config['refresh_token'],
            'grant_type': 'refresh_token'
        }

        # Send the POST request to refresh the token
        response = requests.post(token_url, data=params)

        # Check if the request was successful
        if response.status_code == 200:
            data = response.json()
            access_token = data['access_token']
            print(f"=====================================================")
            print(f"======= Access Token Refresh @ {utils.GetLocalTime().strftime('%m-%d-%y %H:%M')} =======")
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