import requests
from discord.ext import commands

class TwitchRewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='1raidrequest')
    async def raid_request(self, ctx):
        # add actions
        await ctx.send('Command was triggered! ??')

    def listen_to_twitch():
        url = 'https://api.twitch.tv/helix/eventsub/subscriptions'
        headers = {
            'Client-ID': 'TWITCH_CLIENT_ID',
            'Authorization': f'Bearer {TWITCH_API_TOKEN}',
        }
        data = {
            "type": "channel.channel_points_custom_reward_redemption.add",
            "version": "1",
            "condition": {
                "broadcaster_user_id": "TWITCH_USER_ID",
            },
            "transport": {
                "method": "webhook",
                "callback": "WEBHOOK_URL",
                "secret": "WEBHOOK_SECRET",
            }
        }

        response = requests.post(url, json=data, headers=headers)
        response_data = response.json()
        return response_data

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user.name}')
        # Register the Twitch event listener
        self.listen_to_twitch()

def setup(bot):
    bot.add_cog(TwitchRewards(bot))