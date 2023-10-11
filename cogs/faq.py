import os
import asyncio
import random
import sqlite3
import discord
from discord.ext import commands

class FactsQuestions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.commands_file = os.path.join(self.database_folder, 'GHM_Discord_Bot.db')
        self.conn = sqlite3.connect(self.commands_file)
        self.cursor = self.conn.cursor()

        # Create tables if they don't exist
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS faq (
                                name TEXT PRIMARY KEY,
                                question TEXT,
                                answer TEXT
                            )''')

        self.cursor.execute('''CREATE TABLE IF NOT EXISTS aliases (
                                word TEXT PRIMARY KEY,
                                faq_name TEXT,
                                FOREIGN KEY (faq_name) REFERENCES faq (name) ON DELETE CASCADE
                            )''')

        self.conn.commit()

    def save_aliases(self):
        # This method is not needed when using SQLite
        pass

    async def update_faq(self, ctx):
        faq_channel_id = self.bot.config.get('faq_channel_id')

        if faq_channel_id is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        faq_channel = ctx.guild.get_channel(faq_channel_id)

        if not faq_channel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'faq_channel_id' in config.json points to a valid channel.")
            return

        self.cursor.execute("SELECT * FROM faq")
        rows = self.cursor.fetchall()

        messages = []
        for row in rows:
            faq_name, question, answer = row
            embed = discord.Embed(color=discord.Color.red())
            embed.title = f"FAQ {faq_name.upper()}"
            embed.add_field(name="Question:", value=question, inline=False)
            embed.add_field(name="Answer:", value=f"{answer}", inline=False)
            
            # Fetch aliases for the FAQ entry
            self.cursor.execute("SELECT word FROM aliases WHERE faq_name=?", (faq_name,))
            alias_rows = self.cursor.fetchall()
            aliases = [alias_row[0] for alias_row in alias_rows]

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
                await existing_message.edit(embed=message)
            else:
                await faq_channel.send(embed=message)

        self.save_aliases()

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

        self.cursor.execute("INSERT INTO faq (name, question, answer) VALUES (?, ?, ?)", (name, question_content, answer_content))
        self.conn.commit()

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(aliases=['faqaddaliases'], hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def faqalias(self, ctx, faq_name: str = "", *, words: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")

        # Split the words and add aliases to the database
        for word in words.strip().split():
            self.cursor.execute("INSERT OR REPLACE INTO aliases (word, faq_name) VALUES (?, ?)", (word, faq_name))
        self.conn.commit()

        await ctx.send("✅ Alias added/updated.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deletealias(self, ctx, word: str):
        # Delete the alias from the database
        self.cursor.execute("DELETE FROM aliases WHERE word=?", (word,))
        self.conn.commit()

        await ctx.send("✅ Alias removed.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(aliases=['aliases'], help='<faqname> [This will give you all the aliases to that faq]')
    async def listaliases(self, ctx, faq_name: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")

        # Fetch aliases from the database for the given FAQ
        self.cursor.execute("SELECT word FROM aliases WHERE faq_name=?", (faq_name,))
        rows = self.cursor.fetchall()
        aliases = [row[0] for row in rows]

        if not aliases:
            return await ctx.send("⚠ No aliases found.")

        await ctx.send(f"Aliases for FAQ entry {faq_name}: {', '.join(aliases)}")

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deletefaq(self, ctx, faq_name: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")

        # Delete the FAQ entry and associated aliases from the database
        self.cursor.execute("DELETE FROM faq WHERE name=?", (faq_name,))
        self.cursor.execute("DELETE FROM aliases WHERE faq_name=?", (faq_name,))
        self.conn.commit()

        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def editfaq(self, ctx, faq_name: str = "", edit_type: str = "a"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(edit_type[0] == "q" or edit_type[0] == "a"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer` (default).")

        random_num = random.randint(1, 9999)
        edit_type_readable = {
            "q": "question",
            "a": "answer"
        }

        await ctx.send(f"Enter the new {edit_type_readable[edit_type[0]]} content:\n\nType `cancel-{random_num:04d}` to cancel.")

        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            if new_content.content == f"cancel-{random_num:04d}":
                return await ctx.send("❌ Canceled by user.")
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")

        # Update the FAQ entry in the database
        self.cursor.execute(f"UPDATE faq SET {edit_type_readable[edit_type[0]]}=? WHERE name=?", (new_content.content, faq_name))
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

        # Fetch the FAQ entry from the database
        self.cursor.execute("SELECT * FROM faq WHERE name=?", (faq_name,))
        row = self.cursor.fetchone()

        if not row:
            return await ctx.send("⚠ No such entry exists.")

        faq_name, question, answer = row

        if return_type[0] == "q":
            msg = question
        elif return_type[0] == "a":
            msg = answer
        else:
            msg = f"\n\n".join([question, answer])

        await ctx.send(f"```\n{msg}\n```")

    @commands.command(aliases=['faqview'], help='<faq_name> or <faq_alias_name>')
    async def faq(self, ctx, faq_req: str):
        # Check if faq_req is an alias
        self.cursor.execute("SELECT faq_name FROM aliases WHERE word=?", (faq_req,))
        alias_row = self.cursor.fetchone()

        if alias_row:
            faq_req = alias_row[0]

        # Fetch the FAQ entry from the database
        self.cursor.execute("SELECT * FROM faq WHERE name=?", (faq_req,))
        row = self.cursor.fetchone()

        if not row:
            return await ctx.send("⚠ No such entry exists.")

        faq_name, question, answer = row

        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"FAQ: {faq_name}"
        embed.add_field(name="Question:", value=question, inline=False)
        embed.add_field(name="Answer:", value=f"{answer}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def refreshfaq(self, ctx):
        await ctx.send("Refreshing FAQ...")
        self.bot.loop.create_task(self.update_faq(ctx))

def setup(bot):
    bot.add_cog(FactsQuestions(bot))
