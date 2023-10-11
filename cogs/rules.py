import os
import asyncio
import sqlite3
import discord
from discord.ext import commands

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.commands_file = os.path.join(self.database_folder, 'GHM_Discord_Bot.db')
        self.conn = sqlite3.connect(self.commands_file)
        self.cursor = self.conn.cursor()
        self.initialize_database()

    def initialize_database(self):
        # Create a table if it doesn't exist
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY,
                rule TEXT,
                description TEXT
            )
        ''')
        self.conn.commit()

    async def update_rules(self):
        rules_channel_id = self.config.get("rules_channel_id")
        
        # Fetch rules from the database
        self.cursor.execute("SELECT * FROM rules")
        rows = self.cursor.fetchall()

        messages = []

        for row in rows:
            rule_id, rule, description = row
            embed = discord.Embed(
                title=f"Rule {rule_id}",
                description=description,
                color=discord.Color.green()
            )
            messages.append(embed)

        counter = 0
        try:
            msg = await self.bot.get_channel(rules_channel_id).fetch_message(rules_channel_id)
        except discord.errors.NotFound:
            msg = None
        async for message in self.bot.get_channel(rules_channel_id).history(limit=100, oldest_first=True, after=msg).filter(lambda m: m.author == self.bot.user):
            if counter < len(messages):
                if message.embeds and message.embeds[0].title == messages[counter].title \
                    and message.embeds[0].description == messages[counter].description:
                    counter += 1
                    continue
                await message.edit(embed=messages[counter])
                counter += 1
            else:
                await message.delete()
        for message_info in messages[counter:]:
            embed = message_info
            await self.bot.get_channel(rules_channel_id).send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def addrule(self, ctx):
        await ctx.send("Type the rule to be added after this message:\n(note: all rules are automatically underlined)")
        try:
            question = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")

        await ctx.send("Type the rule description after this message:")
        try:
            answer = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")

        # Insert the new rule into the database
        self.cursor.execute("INSERT INTO rules (rule, description) VALUES (?, ?)", (question.content, answer.content))
        self.conn.commit()

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['delrule', 'dr'], help='<rules_id>', hidden=True)
    @commands.has_any_role("Admin")
    async def deleterule(self, ctx, rules_id: int = 0):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        try:
            self.cursor.execute("DELETE FROM rules WHERE id=?", (rules_id,))
            self.conn.commit()
        except sqlite3.Error:
            return await ctx.send("⚠ No such entry exists.")
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['modify'], help='<rules_id>', hidden=True)
    @commands.has_any_role("Admin")
    async def editrule(self, ctx, rules_id: int = 0, edit_type: str = "d"):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        if not(edit_type[0] == "r" or edit_type[0] == "d"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `rule`, `description` (default).")
        
        # Fetch the existing rule from the database
        try:
            self.cursor.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
            entry = self.cursor.fetchone()
        except sqlite3.Error:
            return await ctx.send("⚠ No such entry exists.")

        await ctx.send(f"Enter the new {edit_type} content:")
        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")

        if edit_type[0] == "r":
            self.cursor.execute("UPDATE rules SET rule=? WHERE id=?", (new_content.content, rules_id))
        elif edit_type[0] == "d":
            self.cursor.execute("UPDATE rules SET description=? WHERE id=?", (new_content.content, rules_id))

        self.conn.commit()
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['source'], hidden=True)
    @commands.has_any_role("Admin")
    async def raw(self, ctx, rules_id: int = 0, return_type: str = "both"):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        if not(return_type[0] == "r" or return_type[0] == "d" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `rule`, `description`, `both` (default).")

        # Fetch the existing rule from the database
        try:
            self.cursor.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
            entry = self.cursor.fetchone()
        except sqlite3.Error:
            return await ctx.send("⚠ No such entry exists.")

        if return_type[0] == "r":
            msg = entry[1]  # Rule content
        elif return_type[0] == "d":
            msg = entry[2]  # Description content
        else:
            msg = "\n\n".join([entry[1], entry[2]])  # Both rule and description

        await ctx.send(f"```\n{msg}\n```")

    @commands.command(aliases=['rule', 'showrule'], help='<rules_id>')
    async def viewrule(self, ctx, rules_id: int = 0):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")

        # Fetch the existing rule from the database
        try:
            self.cursor.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
            entry = self.cursor.fetchone()
        except sqlite3.Error:
            return await ctx.send("⚠ No such entry exists.")

        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"R{rules_id}. {entry[1]}"  # Rule title
        embed.description = entry[2]  # Description content
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def refreshrules(self, ctx):
        await ctx.send("Refreshing rules...")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(hidden=True)
    async def refreshrules(self, ctx):
        await ctx.send("Refreshing rules...")
        self.bot.loop.create_task(self.update_rules())

    def cog_unload(self):
        self.conn.close()

def setup(bot):
    bot.add_cog(Rules(bot))
