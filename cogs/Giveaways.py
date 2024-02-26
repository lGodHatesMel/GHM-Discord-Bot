import discord
from discord.ext import commands
import utils.utils as utils
from utils.Paginator import Paginator
import json
import sqlite3
import json
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import random

import logging
logging.basicConfig(filename='giveaways.log', level=logging.DEBUG)
logging.debug('This message should go to the log file')

scheduler = AsyncIOScheduler()

conn = sqlite3.connect('Database/giveaways.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS giveaways (title text, description text, end_time text, message_id integer)''')
c.execute("PRAGMA table_info(giveaways)")
columns = c.fetchall()
if not any(column[1] == 'winner_id' for column in columns):
    c.execute("ALTER TABLE giveaways ADD COLUMN winner_id INTEGER")
conn.commit()
conn.close()

class Giveaway(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.emoji = '🎉'

        conn = sqlite3.connect('Database/giveaways.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS giveaway_entries (message_id integer, user_id integer)''')
        conn.commit()
        conn.close()

        with open('config.json') as f:
            config = json.load(f)
        self.channel_id = int(config['channel_ids']['GiveawayChannel'])

    @commands.command(help="<title> <description> <days from now> <end time in 24-hour HH:MM format>", hidden=True)
    async def startgiveaway(self, ctx, title: str, description: str, days_from_now: int, end_time: str):
        logging.debug(f'Starting giveaway: {title}')
        start_time = utils.GetLocalTime()
        end_date = start_time + utils.TimeDelta(days=days_from_now)
        end_hour, end_minute = map(int, end_time.split(":"))
        end_datetime = end_date.replace(hour=end_hour, minute=end_minute)

        with open('config.json') as f:
            config = json.load(f)
        logo_url = config['logo_url']

        days, remainder = divmod(days_from_now * 24 * 60, 1440)
        hours, minutes = divmod(remainder, 60)
        duration_str = ""
        if days > 0:
            duration_str += f"{days} days "
        if hours > 0:
            duration_str += f"{hours} hours "
        if minutes > 0:
            duration_str += f"{minutes} minutes"

        embed = discord.Embed(title=f"🎉 **GIVEAWAY: {title}** 🎉", description="", color=0x00ff00)
        embed.add_field(name="Description", value=description, inline=False)
        embed.set_footer(text=f"React with 🎉 to enter! - Start Time: {start_time.strftime('%m-%d-%y %I:%M %p')} - End Time: {end_datetime.strftime('%m-%d-%y %I:%M %p')}")
        embed.set_thumbnail(url=logo_url)

        embed = discord.Embed(title=f"🎉 **GIVEAWAY** 🎉", description="", color=0x00ff00)
        embed.add_field(name=f"🎉 __**{title}**__ 🎉", value=description, inline=False)
        embed.set_footer(text=f"React with 🎉 to enter! - Start Time: {start_time.strftime('%m-%d-%y %I:%M %p')} - End Time: {end_datetime.strftime('%m-%d-%y %I:%M %p')}")
        embed.set_thumbnail(url=logo_url)

        message = await self.bot.get_channel(self.channel_id).send(embed=embed)
        await message.add_reaction(self.emoji)

        conn = sqlite3.connect('Database/giveaways.db')
        c = conn.cursor()
        c.execute("INSERT INTO giveaways (title, description, end_time, message_id, winner_id) VALUES (?, ?, ?, ?, ?)", 
                (title, description, end_datetime.strftime('%m-%d-%y %I:%M %p'), message.id, None))
        conn.commit()
        conn.close()

        scheduler.add_job(self.announcewinner, 'date', run_date=end_datetime, args=[self.channel_id, message.id])
        if not scheduler.running:
            scheduler.start()

        scheduler.add_job(lambda: self.announce_winner_sync(self.channel_id, message.id), 'date', run_date=end_datetime)

    def announce_winner_sync(self, channel_id: int, message_id: int):
        logging.debug(f'Announcing winner for message_id: {message_id} in channel_id: {channel_id}')
        asyncio.run_coroutine_threadsafe(self.announcewinner(channel_id, message_id), self.bot.loop)

    @commands.command(help="<channel_id> <message_id>", hidden=True)
    async def announcewinner(self, channel_id: int, message_id: int):
        logging.debug(f'Announcing winner for message_id: {message_id}')
        conn = sqlite3.connect('Database/giveaways.db')
        c = conn.cursor()
        c.execute("SELECT user_id FROM giveaway_entries WHERE message_id=?", (message_id,))
        user_ids = c.fetchall()

        if not user_ids:
            await self.bot.get_channel(channel_id).send("No one entered the giveaway.")
            conn.close()
            return

        winner_id = random.choice(user_ids)[0]
        winner = self.bot.get_user(winner_id)

        c.execute("SELECT title FROM giveaways WHERE message_id = ?", (message_id,))
        title = c.fetchone()[0]

        c.execute("UPDATE giveaways SET winner_id = ? WHERE message_id = ?", (winner_id, message_id))
        conn.commit()
        conn.close()

        embed = discord.Embed(
            title="🎉 Congratulations! 🎉",
            description=f"{winner.mention} won the giveaway for **{title}**!",
            color=0x00FF00,
        )
        embed.set_footer(text="We will message you as soon as we can <3")
        embed.set_author(name=winner.name, icon_url=winner.avatar_url)
        await self.bot.get_channel(channel_id).send(embed=embed)

    @commands.command(help="<message_id>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def endgiveaway(self, ctx, message_id: int):
        logging.debug(f'Ending giveaway with message_id: {message_id}')
        conn = sqlite3.connect('Database/giveaways.db')
        c = conn.cursor()
        c.execute("DELETE FROM giveaways WHERE message_id=?", (message_id,))
        conn.commit()
        conn.close()

        message = await self.bot.get_channel(self.channel_id).fetch_message(message_id)
        await message.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, EmojiID: discord.RawReactionActionEvent):
        logging.debug(f'Reaction added by user_id: {EmojiID.user_id} on message_id: {EmojiID.message_id}')
        if EmojiID.emoji.name == self.emoji:
            if EmojiID.user_id == self.bot.user.id:
                return

            conn = sqlite3.connect('Database/giveaways.db')
            c = conn.cursor()
            c.execute("INSERT INTO giveaway_entries VALUES (?, ?)", (EmojiID.message_id, EmojiID.user_id))
            conn.commit()
            conn.close()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, EmojiID: discord.RawReactionActionEvent):
        logging.debug(f'Reaction removed by user_id: {EmojiID.user_id} on message_id: {EmojiID.message_id}')
        if EmojiID.emoji.name == self.emoji:
            conn = sqlite3.connect('Database/giveaways.db')
            c = conn.cursor()
            c.execute("DELETE FROM giveaway_entries WHERE message_id=? AND user_id=?", (EmojiID.message_id, EmojiID.user_id))
            conn.commit()
            conn.close()

    @commands.command(help="Shows all giveaways", hidden=True)
    async def showgiveaways(self, ctx):
        logging.debug('Starting showgiveaways command')
        conn = sqlite3.connect('Database/giveaways.db')
        c = conn.cursor()
        c.execute("SELECT * FROM giveaways")
        giveaways = c.fetchall()
        logging.debug(f'Fetched {len(giveaways)} giveaways from the database')

        with open('config.json') as f:
            config = json.load(f)
        logo_url = config['logo_url']

        embeds = []
        for giveaway in giveaways:
            title, description, end_time, message_id, winner_id = giveaway

            if winner_id:
                winner = self.bot.get_user(winner_id)
                status = f"Ended\n**winner:**\n{winner.name} (ID: {winner_id})"
            else:
                status = "Ongoing"

            c.execute("SELECT user_id FROM giveaway_entries WHERE message_id=?", (message_id,))
            user_ids = c.fetchall()
            user_mentions = [f'<@{user_id[0]}>' for user_id in user_ids]
            user_mentions_chunks = [user_mentions[i:i + 100] for i in range(0, len(user_mentions), 100)]

            for i, user_mentions_chunk in enumerate(user_mentions_chunks, start=1):
                user_mentions_text = ', '.join(user_mentions_chunk)
                if len(user_mentions_chunks) > 1:
                    participants_field = f"**Participants (Part {i}/{len(user_mentions_chunks)}):**  {user_mentions_text or 'None'}"
                else:
                    participants_field = f"**Participants:**  {user_mentions_text or 'None'}"

                embed = discord.Embed(
                    title=f"🎉 **Giveaway** 🎉",
                    description=f"🎉 __**{title}**__ 🎉\n\n**Description:**\n{description}\n\n**End Time:**\n{end_time}\n\n**Status:** {status}\n\n{participants_field}",
                    color=0x00FF00,
                )
                embed.set_thumbnail(url=logo_url)
                embed.set_footer(text="Use the reactions to navigate through the giveaways.")
                embeds.append(embed)
        conn.close()

        paginator = Paginator(ctx, embeds)
        await paginator.start()

def setup(bot):
    bot.add_cog(Giveaway(bot))
