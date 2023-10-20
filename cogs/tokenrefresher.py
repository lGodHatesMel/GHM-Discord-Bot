import requests
import time
import json
import discord
from discord.ext import commands, tasks

class TokenRefresher(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.token_config = self.load_token_config()
        self.refresh_token.start()

    def cog_unload(self):
        self.refresh_token.cancel()

    def load_token_config(self):
        with open('token-config.json', 'r') as file:
            return json.load(file)

    def should_run_token_refresher(self):
        with open('config.json', 'r') as file:
            config = json.load(file)
        return config.get('token_refresher_enabled', False)

    @tasks.loop(hours=3)
    async def refresh_token(self):
        if not self.should_run_token_refresher():
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
            print(f'Access token refreshed: {access_token}')
        else:
            print(f'Failed to refresh access token. Status code: {response.status_code}')
            print(response.text)

    @refresh_token.before_loop
    async def before_refresh_token(self):
        await self.bot.wait_until_ready()

def setup(bot):
    bot.add_cog(TokenRefresher(bot))
