import os
import asyncio
import sqlite3
import random
import discord
from discord.ext import commands

class FactsQuestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = None
        self.cursor = None
        self.c = None
        self.SetupDatabase()

    def SetupDatabase(self):
        self.conn = sqlite3.connect('Database/faq.db')
        self.cursor = self.conn.cursor()
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS faq
                        (name TEXT PRIMARY KEY, question TEXT, answer TEXT)''')
        self.c.execute('''CREATE TABLE IF NOT EXISTS faq_aliases
                        (alias TEXT PRIMARY KEY, faq_name TEXT)''')
        self.conn.commit()

    def __del__(self):
        if self.conn:
            self.conn.close()

    async def UpdateFAQ(self, ctx):
        self.SetupDatabase()
        FAQChannelID = self.bot.config['channel_ids'].get('FAQChannel')

        if FAQChannelID is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        FAQChannel = ctx.guild.get_channel(FAQChannelID)

        if not FAQChannel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'FAQChannel' in config.json points to a valid channel.")
            return

        async for msg in FAQChannel.history(limit=None):
            if msg.author == self.bot.user:
                await msg.delete()
                await asyncio.sleep(1)

        self.c.execute("SELECT * FROM faq")
        faq_db = self.c.fetchall()
        messages = []
        for faq_name, question, answer in faq_db:
            embed = discord.Embed(color=discord.Color.red())
            embed.title = f"FAQ {faq_name.upper()}"
            embed.add_field(name="Question:", value=question, inline=False)
            embed.add_field(name="Answer:", value=f"{answer}", inline=False)
            aliases = []
            self.c.execute("SELECT alias FROM faq_aliases WHERE faq_name = ?", (faq_name,))
            aliases_db = self.c.fetchall()
            for alias in aliases_db:
                aliases.append(alias[0])
            if aliases:
                embed.set_footer(text="Aliases: " + ", ".join(aliases))
            messages.append(embed)

        for message in messages:
            existing_message = None
            async for msg in FAQChannel.history(limit=100):
                if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == message.title:
                    existing_message = msg
                    break

            if existing_message:
                await self.edit_message_with_retry(existing_message, message)
            else:
                await self.send_message_with_retry(FAQChannel, message)
        self.SaveAliases()

    def SaveAliases(self):
        self.SetupDatabase()
        self.c.execute("SELECT * FROM faq_aliases")
        aliases_db = self.c.fetchall()
        self.faq_aliases = {alias[0]: alias[1] for alias in aliases_db}

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
        FAQChannelID = self.bot.config['channel_ids'].get('FAQChannel')

        if FAQChannelID is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        FAQChannel = ctx.guild.get_channel(FAQChannelID)

        if not FAQChannel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'FAQChannel' in config.json points to a valid channel.")
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

        self.cursor.execute("SELECT * FROM faq WHERE name = ?", (name,))
        if self.cursor.fetchone() is not None:
            return await ctx.send("⚠ This name is already in use for another FAQ entry.")

        self.cursor.execute("INSERT INTO faq VALUES (?, ?, ?)", (name, question_content, answer_content))

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.UpdateFAQ(ctx))

    @commands.command(aliases=['faqaddaliases'], hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def faqalias(self, ctx, faq_name: str = "", *, words: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        for word in words.strip().split():
            self.cursor.execute("INSERT INTO faq_aliases VALUES (?, ?)", (word, faq_name))
        self.conn.commit()
        await ctx.send("✅ Alias added/updated.")
        self.bot.loop.create_task(self.UpdateFAQ(ctx))

    @commands.command(aliases=['aliases'], help='<faqname> [This will give you all the aliases to that faq]')
    async def listaliases(self, ctx, faq_name: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        aliases = []
        self.cursor.execute("SELECT alias FROM faq_aliases WHERE faq_name = ?", (faq_name,))
        aliases_db = self.cursor.fetchall()
        for alias in aliases_db:
            aliases.append(alias[0])
        if not aliases:
            return await ctx.send("⚠ No aliases found.")
        await ctx.send("Aliases for FAQ entry {}: {}".format(faq_name, ", ".join(aliases)))

    @commands.command(aliases=['aliases'], help='<faqname> [This will give you all the aliases to that faq]')
    async def listaliases(self, ctx, faq_name: str = ""):
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
        self.cursor.execute("DELETE FROM faq WHERE name = ?", (faq_name,))
        self.cursor.execute("DELETE FROM faq_aliases WHERE faq_name = ?", (faq_name,))
        self.conn.commit()
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.UpdateFAQ(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def editfaq(self, ctx, faq_name: str = "", edit_type: str = "a"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(edit_type[0] == "q" or edit_type[0] == "a"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer` (default).")

        self.cursor.execute("SELECT name FROM faq WHERE name = ?", (faq_name,))
        entry = self.cursor.fetchone()
        if not entry:
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
            self.cursor.execute("UPDATE faq SET question = ? WHERE name = ?", (new_content.content, faq_name))
        elif edit_type[0] == "a":
            self.cursor.execute("UPDATE faq SET answer = ? WHERE name = ?", (new_content.content, faq_name))
        self.conn.commit()

        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.UpdateFAQ(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def faqraw(self, ctx, faq_name: str = "", return_type: str = "both"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(return_type[0] == "q" or return_type[0] == "a" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer`, `both` (default).")

        self.cursor.execute("SELECT question, answer FROM faq WHERE name = ?", (faq_name,))
        entry = self.cursor.fetchone()
        if not entry:
            return await ctx.send("⚠ No such entry exists.")
        question, answer = entry
        if return_type[0] == "q":
            msg = question
        elif return_type[0] == "a":
            msg = answer
        else:
            msg = "\n\n".join([question, answer])
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command(aliases=['faqview'], help='<faq_name> or <faq_alias_name>')
    async def faq(self, ctx, faq_req: str):
        self.cursor.execute("SELECT faq_name FROM faq_aliases WHERE alias = ?", (faq_req,))
        faq_name = self.cursor.fetchone()
        if faq_name:
            faq_req = faq_name[0]
        self.cursor.execute("SELECT question, answer FROM faq WHERE name = ?", (faq_req,))
        entry = self.cursor.fetchone()
        if not entry:
            return await ctx.send("⚠ No such entry exists.")
        question, answer = entry
        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"FAQ: {faq_req.upper()}"
        embed.add_field(name="Question:", value=question, inline=False)
        embed.add_field(name="Answer:", value=f"{answer}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def refreshfaq(self, ctx):
        await ctx.send("Refreshing FAQ...")
        self.bot.loop.create_task(self.UpdateFAQ(ctx))

def setup(bot):
    bot.add_cog(FactsQuestions(bot))