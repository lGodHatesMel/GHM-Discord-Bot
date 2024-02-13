import os
import asyncio
import discord
from discord.ext import commands
import sqlite3

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('rules.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS rules
                    (id INTEGER PRIMARY KEY, rule TEXT, description TEXT)''')

    async def update_rules(self):
        rules_channel_id = self.config.get("rules_channel_id")
        self.c.execute("SELECT * FROM rules")
        rules_data = self.c.fetchall()

        messages = []
        for rule in rules_data:
            embed = discord.Embed(
                title=f"Rule {rule[0]}",
                description=rule[1],
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
        self.c.execute("SELECT MAX(id) FROM rules")
        next_rule_id = self.c.fetchone()[0]
        if next_rule_id is None:
            next_rule_id = 1
        else:
            next_rule_id += 1

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

        self.c.execute("INSERT INTO rules VALUES (?, ?, ?)", (next_rule_id, question.content, answer.content))
        self.conn.commit()

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['delrule', 'dr'], help='<rules_id>', hidden=True)
    @commands.has_any_role("Admin")
    async def deleterule(self, ctx, rules_id: int = 0):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        self.c.execute("DELETE FROM rules WHERE id=?", (rules_id,))
        self.conn.commit()
        if self.c.rowcount == 0:
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
        self.c.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        await ctx.send("Enter the new {} content:".format(edit_type))
        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")
        if edit_type[0] == "r":
            self.c.execute("UPDATE rules SET rule=? WHERE id=?", (new_content.content, rules_id))
        elif edit_type[0] == "d":
            self.c.execute("UPDATE rules SET description=? WHERE id=?", (new_content.content, rules_id))
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
        self.c.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        if return_type[0] == "r":
            msg = entry[1]
        elif return_type[0] == "d":
            msg = entry[2]
        else:
            msg = "\n\n".join([entry[1], entry[2]])
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command(aliases=['rule', 'showrule'], help='<rules_id>')
    async def viewrule(self, ctx, rules_id: int = 0):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        self.c.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        embed = discord.Embed(color=discord.Color.red())
        embed.title = "R{}. {}".format(rules_id, entry[1])
        embed.description = entry[2]
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def refreshrules(self, ctx):
        await ctx.send("Refreshing rules...")
        self.bot.loop.create_task(self.update_rules())

def setup(bot):
    bot.add_cog(Rules(bot))