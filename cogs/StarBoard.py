import sqlite3
import json
import utils
import asyncio
import discord
from discord import RawReactionActionEvent, Embed, File
from discord.ext import commands
# from PIL import Image, ImageDraw, ImageFont
# import requests
# from io import BytesIO

@staticmethod
def star_level(star_count):
    levels = [(5, "⭐"), (10, "🌟"), (15, "✨"), (20, "💫")]
    for level, emoji in levels:
        if star_count < level:
            return emoji
    return "🌠"

class Starboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('Database/starboard.db')
        self.c = self.conn.cursor()
        self.c.execute("""
            CREATE TABLE IF NOT EXISTS starboard_table (
                message_id INTEGER PRIMARY KEY,
                author_id INTEGER,
                star_count INTEGER,
                starboard_id INTEGER,
                channel_id INTEGER,
                creation_date TEXT
            )
        """)
        self.conn.commit()

        with open('config.json') as f:
            self.config = json.load(f)

    def cog_unload(self):
        self.conn.close()

    # def create_message_image(self, author_name, author_avatar_url, content):
    #     img = Image.new('RGB', (500, 100), color = (255, 255, 255))
    #     d = ImageDraw.Draw(img)
    #     response = requests.get(author_avatar_url)
    #     avatar = Image.open(BytesIO(response.content))
    #     avatar = avatar.resize((32, 32))
    #     img.paste(avatar, (10, 10))
    #     # Use a truetype font
    #     fnt = ImageFont.truetype('./assets/DejaVuSans-Bold.ttf', 15)

    #     d.text((50,10), author_name, font=fnt, fill=(0, 0, 0))
    #     d.text((50,30), content, font=fnt, fill=(0, 0, 0))
    #     img.save('message.png')

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, reaction_event: RawReactionActionEvent):
        if str(reaction_event.channel_id) in self.config["channel_ids"]["BlacklistedChannels"]:
            return

        if str(reaction_event.emoji) in ['⭐', '🌟', '✨', '💫', '🌠']:
            channel = self.bot.get_channel(reaction_event.channel_id)
            message = await channel.fetch_message(reaction_event.message_id)
            self.c.execute("SELECT * FROM starboard_table WHERE message_id=?", (message.id,))
            result = self.c.fetchone()
            if result is None:
                creation_date = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                self.c.execute("INSERT INTO starboard_table VALUES (?,?,?,?,?,?)", (message.id, message.author.id, 1, None, channel.id, creation_date))
            else:
                self.c.execute("UPDATE starboard_table SET star_count = star_count + 1 WHERE message_id=?", (message.id,))
            self.conn.commit()

            self.c.execute("SELECT * FROM starboard_table WHERE message_id=?", (message.id,))
            result = self.c.fetchone()
            if result[2] >= 3: # Min star count per message
                StarboardChannelID = self.config["channel_ids"]["StarBoardChannel"]
                starboard_channel = self.bot.get_channel(StarboardChannelID)
                if result[3] is None:
                    embed = Embed(
                        title=f"{result[2]} ⭐ in <#{channel.id}>\n",
                        description=f"\n\n**Message Content**\n*{message.content}*\n\n**Message Link**\n[Jump to Content]({message.jump_url})",
                        color=0xFFD700
                    )
                    stars = star_level(result[2])
                    embed = Embed(
                        title=f"{result[2]} {stars} in <#{channel.id}>\n",
                        description=f"\n\n**Message Content**\n*{message.content}*\n\n**Message Link**\n[Jump to Content]({message.jump_url})",
                        color=0xFFD700
                    )
                    if message.attachments:
                        embed.add_field(name="Attachment", value=f"[Link]({message.attachments[0].url})", inline=False)
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    embed.set_thumbnail(url=self.config["logo_url"])
                    starboard_message = await starboard_channel.send(embed=embed)
                    embed.set_footer(text=f"Starboard ID: {starboard_message.id} | {result[5]}")
                    await starboard_message.edit(embed=embed)
                    self.c.execute("UPDATE starboard_table SET starboard_id = ? WHERE message_id=?", (starboard_message.id, message.id))
                else:
                    starboard_message = await starboard_channel.fetch_message(result[3])
                    stars = star_level(result[2])
                    embed = Embed(
                        title=f"{result[2]} {stars} in <#{channel.id}>\n",
                        description=f"\n\n**Message Content**\n*{message.content}*\n\n**Message Link**\n[Jump to Content]({message.jump_url})",
                        color=0xFFD700
                    )
                    if message.attachments:
                        embed.add_field(name="Attachment", value=f"[Link]({message.attachments[0].url})", inline=False)
                    embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                    embed.set_thumbnail(url=self.config["logo_url"])
                    embed.set_footer(text=f"Starboard ID: {starboard_message.id} | {result[5]}")
                    await starboard_message.edit(embed=embed)
                self.conn.commit()

    @commands.command(help='<starboard_id>', hidden=True)
    @commands.has_any_role("Admin")
    async def addstar(self, ctx, starboard_id: int):
        self.c.execute("SELECT * FROM starboard_table WHERE starboard_id=?", (starboard_id,))
        result = self.c.fetchone()
        if result is not None:
            self.c.execute("UPDATE starboard_table SET star_count = star_count + 1 WHERE starboard_id=?", (starboard_id,))
            self.conn.commit()
            StarboardChannelID = self.config["channel_ids"]["StarBoardChannel"]
            starboard_channel = self.bot.get_channel(StarboardChannelID)
            starboard_message = await starboard_channel.fetch_message(starboard_id)
            self.c.execute("SELECT * FROM starboard_table WHERE starboard_id=?", (starboard_id,))
            result = self.c.fetchone()
            channel = self.bot.get_channel(result[4])
            embed = starboard_message.embeds[0]
            stars = star_level(result[2])
            embed.title = f"{result[2]} {stars} in <#{channel.id}>\n",
            embed.set_footer(text=f"Starboard ID: {starboard_id} | {result[5]}")
            await starboard_message.edit(embed=embed)

    @commands.command(help='<starboard_id>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removestar(self, ctx, starboard_id: int):
        self.c.execute("SELECT * FROM starboard_table WHERE starboard_id=?", (starboard_id,))
        result = self.c.fetchone()
        if result is not None:
            self.c.execute("UPDATE starboard_table SET star_count = star_count - 1 WHERE starboard_id=?", (starboard_id,))
            self.conn.commit()
            StarboardChannelID = self.config["channel_ids"]["StarBoardChannel"]
            starboard_channel = self.bot.get_channel(StarboardChannelID)
            starboard_message = await starboard_channel.fetch_message(starboard_id)
            self.c.execute("SELECT * FROM starboard_table WHERE starboard_id=?", (starboard_id,))
            result = self.c.fetchone()
            channel = self.bot.get_channel(result[4])
            embed = starboard_message.embeds[0]
            stars = star_level(result[2])
            embed.title = f"{result[2]} {stars} in <#{channel.id}>\n",
            embed.set_footer(text=f"Starboard ID: {starboard_id} | {result[5]}")
            await starboard_message.edit(embed=embed)

    @commands.command(help='<starboard_id>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletestarboard(self, ctx, starboard_id: int):
        self.c.execute("SELECT * FROM starboard_table WHERE starboard_id=?", (starboard_id,))
        result = self.c.fetchone()
        if result is not None:
            StarboardChannelID = self.config["channel_ids"]["StarBoardChannel"]
            starboard_channel = self.bot.get_channel(StarboardChannelID)
            starboard_message = await starboard_channel.fetch_message(starboard_id)
            await starboard_message.delete()

            self.c.execute("DELETE FROM starboard_table WHERE starboard_id=?", (starboard_id,))
            self.conn.commit()
            await ctx.send(f"Starboard with ID {starboard_id} has been deleted.")
        else:
            await ctx.send(f"No starboard found with ID {starboard_id}.")

    @commands.command(help="Delete all starboards", hidden=True)
    @commands.is_owner()
    async def deleteallstarboards(self, ctx):
        StarboardChannelID = self.config["channel_ids"]["StarBoardChannel"]
        starboard_channel = self.bot.get_channel(StarboardChannelID)

        self.c.execute("SELECT starboard_id FROM starboard_table")
        starboard_ids = self.c.fetchall()
        for starboard_id in starboard_ids:
            try:
                starboard_message = await starboard_channel.fetch_message(starboard_id[0])
                await starboard_message.delete()
            except:
                pass

        self.c.execute("DELETE FROM starboard_table")
        self.conn.commit()
        await ctx.send("All starboards have been deleted.")

    @commands.command(help="Refresh all starboards", hidden=True)
    @commands.is_owner()
    async def refreshstarboards(self, ctx):
        StarboardChannelID = self.config["channel_ids"]["StarBoardChannel"]
        starboard_channel = self.bot.get_channel(StarboardChannelID)

        self.c.execute("SELECT * FROM starboard_table")
        starboard_records = self.c.fetchall()

        for record in starboard_records:
            try:
                starboard_message = await starboard_channel.fetch_message(record[3])
                await starboard_message.delete()
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Error while deleting message: {e}")
            try:
                channel = self.bot.get_channel(record[4])
                message = await channel.fetch_message(record[0])
                embed = Embed(
                    title=f"{record[2]} ⭐ in <#{channel.id}>",
                    description=f"\n\n**Message Content**\n*{message.content}*\n\n**Message Link**\n[Jump to Content]({message.jump_url})",
                    color=0xFFD700
                )
                embed.set_author(name=message.author.name, icon_url=message.author.avatar_url)
                embed.set_thumbnail(url=self.config["logo_url"])
                embed.set_footer(text=f"Starboard ID: {record[3]} | {record[5]}")
                starboard_message = await starboard_channel.send(embed=embed)
                self.c.execute("UPDATE starboard_table SET starboard_id = ? WHERE message_id=?", (starboard_message.id, message.id))
                await asyncio.sleep(1)
            except discord.errors.NotFound:
                print(f"Message {record[0]} not found.")
                continue
        self.conn.commit()
        await ctx.send("All starboards have been refreshed.")

def setup(bot):
    bot.add_cog(Starboard(bot))
