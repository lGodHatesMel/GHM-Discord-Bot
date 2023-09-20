import discord
from discord.ext import commands
import json
from datetime import timezone, datetime
import asyncio
import utils

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.countdown_message = None

    @commands.Cog.listener()
    async def on_ready(self):
        if config.get('enable_countdown', False) and config.get('countdown_channel_id') is not None:
            await self.run_countdown()

    async def run_countdown(self):
        countdown_channel_id = config.get('countdown_channel_id')
        target_timestamp = config.get('target_timestamp')
        channel = self.bot.get_channel(countdown_channel_id)  # Get the channel using the ID

        current_timestamp = utils.get_local_time()
        time_remaining = target_timestamp - current_timestamp

        if time_remaining <= 0:  # This is the message it will give once the countdown is finished
            countdown_text = """
            <:shiny:1072343743778259015> DLC IS NOW OUT!!! <:shiny:1072343743778259015>
            <:shiny:1072343743778259015> Countdown has ended! <:shiny:1072343743778259015>
            <:shiny:1072343743778259015> HAPPY GAMING <:shiny:1072343743778259015>
            """
        else:
            days = int(time_remaining // 86400)
            hours = int((time_remaining % 86400) // 3600)
            minutes = int((time_remaining % 3600) // 60)
            countdown_text = f"""
            ***UPDATED FOR REAL-TIME RELEASE***
            **POKEMON SCARLET & VIOLET DLC DROPS IN**
            <:happySquirtle:1071190313344958605> `{days} days, {hours} hours, {minutes} minutes` <:shiny:1072343743778259015>

            These Should be the times Pokemon Scarlet Violet DLC should be released in these Time Zones:
            `Sept 12, 9:00 PM EST`
            `Sept 13, 10:00 AM JST`
            `Sept 12, 6:00 PM PT`
            `Sept 12, 8:00 PM CT`
            NOTE: Could be around an hour difference...
            """

        if self.countdown_message is None:
            self.countdown_message = await channel.send(countdown_text)
        else:
            await self.countdown_message.edit(content=countdown_text)

        await asyncio.sleep(60)
        await self.run_countdown()  # Recursive call to keep running the countdown

def setup(bot):
    bot.add_cog(Countdown(bot))
