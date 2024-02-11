import os
import asyncio
import sqlite3
import random
import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        database_folder = 'Database'
        self.db_file = os.path.join(database_folder, 'info.db')

        self.conn = sqlite3.connect(self.db_file)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS info
                    (info_name TEXT PRIMARY KEY, question TEXT, answer TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS aliases
                    (alias TEXT PRIMARY KEY, info_name TEXT)''')

    def save_aliases(self):
        self.c.execute("SELECT * FROM aliases")
        aliases_db = self.c.fetchall()
        self.info_aliases = {alias[0]: alias[1] for alias in aliases_db}

    async def update_info(self, ctx):
        info_channel_id = self.bot.config.get('info_channel_id')

        if info_channel_id is None:
            await ctx.send("⚠ info channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        info_channel = ctx.guild.get_channel(info_channel_id)

        if not info_channel:
            await ctx.send("⚠ INFO channel not found. Make sure 'info_channel_id' in config.json points to a valid channel.")
            return

        self.c.execute("SELECT * FROM info")
        info_db = self.c.fetchall()
        messages = []
        for entry in info_db:
            embed = discord.Embed(color=discord.Color.red())
            embed.title = f"INFO {entry[0].upper()}"
            embed.add_field(name="Question:", value=entry[1], inline=False)
            embed.add_field(name="Answer:", value=f"{entry[2]}", inline=False)
            aliases = []
            for word, info in self.info_aliases.items():
                if info == entry[0]:
                    aliases.append(word)
            if aliases:
                embed.set_footer(text="Aliases: " + ", ".join(aliases))
            messages.append(embed)

        for message in messages:
            existing_message = None
            async for msg in info_channel.history(limit=100):
                if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == message.title:
                    existing_message = msg
                    break

            if existing_message:
                await self.edit_message_with_retry(existing_message, message)
            else:
                await self.send_message_with_retry(info_channel, message)

        self.save_aliases()

    async def send_message_with_retry(self, channel, message):
        while True:
            try:
                await channel.send(embed=message)
                break
            except discord.HTTPException as e:
                if e.status == 429:
                    await asyncio.sleep(5)
                else:
                    raise

    async def edit_message_with_retry(self, message, new_message):
        while True:
            try:
                await message.edit(embed=new_message)
                break
            except discord.HTTPException as e:
                if e.status == 429:
                    await asyncio.sleep(5)
                else:
                    raise

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def addinfo(self, ctx):
        info_channel_id = self.bot.config.get('info_channel_id')

        if info_channel_id is None:
            await ctx.send("⚠ INFO channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        info_channel = ctx.guild.get_channel(info_channel_id)

        if not info_channel:
            await ctx.send("⚠ INFO channel not found. Make sure 'info_channel_id' in config.json points to a valid channel.")
            return

        await ctx.send("Type the bot command name for this INFO entry (no spaces or special characters), or type `cancel` to cancel:")

        try:
            name = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            name = name.content.lower()
            if name == "cancel":
                return await ctx.send("❌ Canceled by user.")
            
            await ctx.send("Type the question to be added after this message:")

            question = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=60.0)
            question_content = question.content

            await ctx.send("Type the answer after this message:")

            answer = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=60.0)
            answer_content = answer.content

        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")

        if len("❔ QX. __{}__\n{}".format(question_content, answer_content)) > 1950:
            return await ctx.send("⚠ This INFO entry is too long.")

        self.c.execute("SELECT * FROM info WHERE info_name=?", (name,))
        entry = self.c.fetchone()

        if entry is not None:
            return await ctx.send("⚠ This name is already in use for another INFO entry.")

        self.c.execute("INSERT INTO info VALUES (?, ?, ?)", (name, question_content, answer_content))
        self.conn.commit()

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(aliases=['infoaddaliases'], hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def infoalias(self, ctx, info_name: str = "", *, words: str = ""):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        for word in words.strip().split():
            self.c.execute("INSERT OR REPLACE INTO aliases VALUES (?, ?)", (word, info_name))
        self.conn.commit()
        self.save_aliases()
        await ctx.send("✅ Alias added/updated.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deletealias(self, ctx, word: str):
        self.c.execute("DELETE FROM aliases WHERE alias=?", (word,))
        self.conn.commit()
        if self.c.rowcount == 0:
            return await ctx.send("⚠ INFO alias does not exist.")
        self.save_aliases()
        await ctx.send("✅ Alias removed.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(aliases=['aliases'], help='<infoname> [This will give you all the aliases to that info]')
    async def listaliases(self, ctx, info_name: str = ""):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        aliases = []
        for word, info in self.info_aliases.items():
            if info == info_name:
                aliases.append(word)
        if not aliases:
            return await ctx.send("⚠ No aliases found.")
        await ctx.send("Aliases for INFO entry {}: {}".format(info_name, ", ".join(aliases)))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deleteinfo(self, ctx, info_name: str = ""):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        self.c.execute("DELETE FROM info WHERE info_name=?", (info_name,))
        self.conn.commit()
        if self.c.rowcount == 0:
            return await ctx.send("⚠ No such entry exists.")
        for word, info in list(self.info_aliases.items()):
            if info == info_name:
                del self.info_aliases[word]
        self.save_aliases()
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def editinfo(self, ctx, info_name: str = "", edit_type: str = "a"):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        if not(edit_type[0] == "q" or edit_type[0] == "a"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer` (default).")
        self.c.execute("SELECT * FROM info WHERE info_name=?", (info_name,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        random_num = random.randint(1, 9999)
        edit_type_readable = {
            "q": "question",
            "a": "answer"
        }
        await ctx.send("Enter the new {} content:\n\nType `cancel-{:04d}` to cancel.".format(edit_type_readable[edit_type[0]], random_num))
        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            if new_content.content == "cancel-{:04d}".format(random_num):
                return await ctx.send("❌ Canceled by user.")
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")
        
        if edit_type[0] == "q":
            self.c.execute("UPDATE info SET question=? WHERE info_name=?", (new_content.content, info_name))
        elif edit_type[0] == "a":
            self.c.execute("UPDATE info SET answer=? WHERE info_name=?", (new_content.content, info_name))
        self.conn.commit()
        
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def inforaw(self, ctx, info_name: str = "", return_type: str = "both"):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        if not(return_type[0] == "q" or return_type[0] == "a" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer`, `both` (default).")
        self.c.execute("SELECT * FROM info WHERE info_name=?", (info_name,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        if return_type[0] == "q":
            msg = entry[1]
        elif return_type[0] == "a":
            msg = entry[2]
        else:
            msg = "\n\n".join([entry[1], entry[2]])
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command(aliases=['infoview'], help='<info_name> or <info_alias_name>')
    async def info(self, ctx, info_req: str):
        # Check if info_req is an alias
        if info_req in self.info_aliases:
            info_req = self.info_aliases[info_req]

        self.c.execute("SELECT * FROM info WHERE info_name=?", (info_req,))
        entry = self.c.fetchone()

        if entry is None:
            return await ctx.send("⚠ No such entry exists.")

        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"INFO: {info_req.upper()}"
        embed.add_field(name="Question:", value=entry[1], inline=False)
        embed.add_field(name="Answer:", value=f"{entry[2]}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def refreshinfo(self, ctx):
        await ctx.send("Refreshing INFO...")
        self.bot.loop.create_task(self.update_info(ctx))

def setup(bot):
    bot.add_cog(Info(bot))