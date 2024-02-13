import os
import asyncio
import sqlite3
import random
import discord
from discord.ext import commands

class FactsQuestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        database_folder = 'Database'
        self.db_file = os.path.join(database_folder, 'faq.db')

        self.conn = sqlite3.connect(self.db_file)
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS faq
                    (faq_name TEXT PRIMARY KEY, question TEXT, answer TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS aliases
                    (alias TEXT PRIMARY KEY, faq_name TEXT)''')

    def save_aliases(self):
        self.c.execute("SELECT * FROM aliases")
        aliases_db = self.c.fetchall()
        self.faq_aliases = {alias[0]: alias[1] for alias in aliases_db}

    async def update_faq(self, ctx):
        faq_channel_id = self.bot.config.get('faq_channel_id')

        if faq_channel_id is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        faq_channel = ctx.guild.get_channel(faq_channel_id)

        if not faq_channel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'faq_channel_id' in config.json points to a valid channel.")
            return

        self.c.execute("SELECT * FROM faq")
        faq_db = self.c.fetchall()
        messages = []
        for entry in faq_db:
            embed = discord.Embed(color=discord.Color.red())
            embed.title = f"FAQ {entry[0].upper()}"
            embed.add_field(name="Question:", value=entry[1], inline=False)
            embed.add_field(name="Answer:", value=f"{entry[2]}", inline=False)
            aliases = []
            for word, faq in self.faq_aliases.items():
                if faq == entry[0]:
                    aliases.append(word)
            if aliases:
                embed.set_footer(text="Aliases: " + ", ".join(aliases))
            messages.append(embed)

        for message in messages:
            existing_message = None
            async for msg in faq_channel.history(limit=100):
                if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == message.title:
                    existing_message = msg
                    break

            if existing_message:
                await self.edit_message_with_retry(existing_message, message)
            else:
                await self.send_message_with_retry(faq_channel, message)

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
    async def addfaq(self, ctx):
        faq_channel_id = self.bot.config.get('faq_channel_id')

        if faq_channel_id is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        faq_channel = ctx.guild.get_channel(faq_channel_id)

        if not faq_channel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'faq_channel_id' in config.json points to a valid channel.")
            return

        await ctx.send("Type the bot command name for this FAQ entry (no spaces or special characters), or type `cancel` to cancel:")

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
            return await ctx.send("⚠ This FAQ entry is too long.")

        self.c.execute("SELECT * FROM faq WHERE faq_name=?", (name,))
        entry = self.c.fetchone()

        if entry is not None:
            return await ctx.send("⚠ This name is already in use for another FAQ entry.")

        self.c.execute("INSERT INTO faq VALUES (?, ?, ?)", (name, question_content, answer_content))
        self.conn.commit()

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(aliases=['faqaddaliases'], hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def faqalias(self, ctx, faq_name: str = "", *, words: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        for word in words.strip().split():
            self.c.execute("INSERT OR REPLACE INTO aliases VALUES (?, ?)", (word, faq_name))
        self.conn.commit()
        self.save_aliases()
        await ctx.send("✅ Alias added/updated.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deletealias(self, ctx, word: str):
        self.c.execute("DELETE FROM aliases WHERE alias=?", (word,))
        self.conn.commit()
        if self.c.rowcount == 0:
            return await ctx.send("⚠ FAQ alias does not exist.")
        self.save_aliases()
        await ctx.send("✅ Alias removed.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(aliases=['listaliases'], help='<faq aliases name>')
    async def faqaliases(self, ctx, faq_name: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        aliases = []
        for word, faq in self.faq_aliases.items():
            if faq == faq_name:
                aliases.append(word)
        if not aliases:
            return await ctx.send("⚠ No aliases found.")
        await ctx.send("Aliases for FAQ entry {}: {}".format(faq_name, ", ".join(aliases)))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deletefaq(self, ctx, faq_name: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        self.c.execute("DELETE FROM faq WHERE faq_name=?", (faq_name,))
        self.conn.commit()
        if self.c.rowcount == 0:
            return await ctx.send("⚠ No such entry exists.")
        for word, faq in list(self.faq_aliases.items()):
            if faq == faq_name:
                del self.faq_aliases[word]
        self.save_aliases()
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def editfaq(self, ctx, faq_name: str = "", edit_type: str = "a"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(edit_type[0] == "q" or edit_type[0] == "a"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer` (default).")
        self.c.execute("SELECT * FROM faq WHERE faq_name=?", (faq_name,))
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
            self.c.execute("UPDATE faq SET question=? WHERE faq_name=?", (new_content.content, faq_name))
        elif edit_type[0] == "a":
            self.c.execute("UPDATE faq SET answer=? WHERE faq_name=?", (new_content.content, faq_name))
        self.conn.commit()
        
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def faqraw(self, ctx, faq_name: str = "", return_type: str = "both"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(return_type[0] == "q" or return_type[0] == "a" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer`, `both` (default).")
        self.c.execute("SELECT * FROM faq WHERE faq_name=?", (faq_name,))
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

    @commands.command(aliases=['faqview'], help='<faq name> or <faq alias name>')
    async def faq(self, ctx, faq_req: str):
        # Check if faq_req is an alias
        if faq_req in self.faq_aliases:
            faq_req = self.faq_aliases[faq_req]

        self.c.execute("SELECT * FROM faq WHERE faq_name=?", (faq_req,))
        entry = self.c.fetchone()

        if entry is None:
            return await ctx.send("⚠ No such entry exists.")

        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"FAQ: {faq_req.upper()}"
        embed.add_field(name="Question:", value=entry[1], inline=False)
        embed.add_field(name="Answer:", value=f"{entry[2]}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def refreshfaq(self, ctx):
        await ctx.send("Refreshing FAQ...")
        self.bot.loop.create_task(self.update_faq(ctx))

def setup(bot):
    bot.add_cog(FactsQuestions(bot))