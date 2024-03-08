import sqlite3
import discord
from discord.ext import commands
from discord import Embed
import utils.utils as utils
from utils.Paginator import Paginator
from config import ENABLE_COUNTDOWN
import asyncio
from datetime import datetime, timezone

def GetLocalTime():
    return datetime.now(timezone.utc)

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('Database/countdowns.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS countdowns (
                id INTEGER PRIMARY KEY,
                message TEXT,
                end_message TEXT,
                end_timestamp INTEGER,
                channel_id INTEGER
            )
        ''')
        self.conn.commit()

    @commands.Cog.listener()
    async def on_ready(self):
        if not ENABLE_COUNTDOWN:
            return

        self.cursor.execute('SELECT id FROM countdowns')
        for (countdown_id,) in self.cursor.fetchall():
            await self.run_countdown(countdown_id)

    async def run_countdown(self, countdown_id):
        self.cursor.execute('SELECT * FROM countdowns WHERE id = ?', (countdown_id,))
        countdown = self.cursor.fetchone()
        if countdown is None:
            return

        id, message, end_message, end_timestamp, channel_id = countdown
        print(id)
        channel = self.bot.get_channel(channel_id)

        current_timestamp = datetime.utcnow().timestamp()
        time_remaining = end_timestamp - current_timestamp

        if time_remaining <= 0:
            countdown_text = end_message
            self.cursor.execute('DELETE FROM countdowns WHERE id = ?', (countdown_id,))
            self.conn.commit()
        else:
            days = int(time_remaining // 86400)
            hours = int((time_remaining % 86400) // 3600)
            minutes = int((time_remaining % 3600) // 60)
            countdown_text = message.format(days=days, hours=hours, minutes=minutes)

        try:
            await channel.send(countdown_text)
        except discord.NotFound:
            pass

        if time_remaining > 0:
            await asyncio.sleep(60)
            await self.run_countdown(countdown_id)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def addcountdown(self, ctx, message: str, end_message: str, end_timestamp: int, channel_id: int):
        self.cursor.execute('''
            INSERT INTO countdowns (message, end_message, end_timestamp, channel_id)
            VALUES (?, ?, ?, ?)
        ''', (message, end_message, end_timestamp, channel_id))
        self.conn.commit()
        await ctx.send(f"Countdown added with ID {self.cursor.lastrowid}")
        await self.run_countdown(self.cursor.lastrowid)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def removecountdown(self, ctx, countdown_id: int):
        self.cursor.execute('DELETE FROM countdowns WHERE id = ?', (countdown_id,))
        self.conn.commit()
        await ctx.send(f"Countdown with ID {countdown_id} removed")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def editcountdown(self, ctx, countdown_id: int, message: str, end_message: str, end_timestamp: int, channel_id: int):
        self.cursor.execute('''
            UPDATE countdowns
            SET message = ?, end_message = ?, end_timestamp = ?, channel_id = ?
            WHERE id = ?
        ''', (message, end_message, end_timestamp, channel_id, countdown_id))
        self.conn.commit()
        await ctx.send(f"Countdown with ID {countdown_id} updated")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def listcountdowns(self, ctx):
        self.cursor.execute('SELECT * FROM countdowns')
        countdowns = self.cursor.fetchall()
        if countdowns:
            embeds = []
            for countdown in countdowns:
                id, message, end_message, end_timestamp, channel_id = countdown
                end_time = datetime.fromtimestamp(end_timestamp).strftime('%m-%d-%y %H:%M')
                embed = discord.Embed(title=f"Countdown ID: {id}", color=discord.Color.blue())
                embed.add_field(name="Message", value=message, inline=False)
                embed.add_field(name="End Message", value=end_message, inline=False)
                embed.add_field(name="End Time", value=end_time, inline=False)
                embed.add_field(name="Channel ID", value=channel_id, inline=False)
                embed.set_footer(text="Countdown Details")
                embed.timestamp = datetime.datetime.utcnow()
                embeds.append(embed)
            paginator = Paginator(ctx, embeds)
            await paginator.start()
        else:
            await ctx.send("No countdowns found")

def setup(bot):
    bot.add_cog(Countdown(bot))

# !addcountdown "Days left: {days} hours: {hours} minutes: {minutes}" "Countdown ended!" 1640995200 123456789012345678
# !editcountdown 1 "Days left: {days} hours: {hours} minutes: {minutes}" "Countdown ended!" 1640995200 123456789012345678
# !removecountdown 1