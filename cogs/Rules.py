import discord
from discord.ext import commands
from utils.botdb import CreateRulesDatabase
import sqlite3
from config import CHANNELIDS
import asyncio


class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('Database/rules.db')
        self.c = self.conn.cursor()
        self.c = CreateRulesDatabase(self.c)
        self.conn.commit()

    async def update_rules(self):
        RulesChannelID = CHANNELIDS['RulesChannel']
        self.c.execute("SELECT * FROM rules")
        rules_data = self.c.fetchall()

        messages = []
        for rule in rules_data:
            embed = discord.Embed(
                title=f"{rule[1]}",
                description=rule[2],
                color=discord.Color.green()
            )
            messages.append(embed)

        rules_channel = self.bot.get_channel(RulesChannelID)
        await rules_channel.purge()
        await asyncio.sleep(0.5)
        for embed in messages:
            await rules_channel.send(embed=embed)
            await asyncio.sleep(1)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def addrule(self, ctx):
        self.c.execute("SELECT MAX(id) FROM rules")
        next_rule_id = self.c.fetchone()[0]
        if next_rule_id is None:
            next_rule_id = 1
        else:
            next_rule_id += 1

        timeout_rulename = 30.0
        await ctx.send(f"Type the rule #:\nExample: If the last rule is (Rule #10) Then this rule should be typed out like (Rule #11)\nOnly the Rule # goes here, once you write the Rule #, press enter then it will as you to type the rule description (you have {timeout_rulename} seconds to respond):")
        try:
            question = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=timeout_rulename)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")

        timeout_rule_description = 45.0
        await ctx.send(f"Type the rule description after this message (you have {timeout_rule_description} seconds to respond):")
        try:
            answer = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=timeout_rule_description)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.\n May be better to have everything ready then copy and paste it to be faster")

        self.c.execute("INSERT INTO rules VALUES (?, ?, ?)", (next_rule_id, f"**{question.content}**", answer.content))
        self.conn.commit()

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['delrule'], help='<rules_id or name>', hidden=True)
    @commands.has_any_role("Admin")
    async def deleterule(self, ctx, RuleNameID: str):
        try:
            rules_id = int(RuleNameID)
            self.c.execute("DELETE FROM rules WHERE id=?", (rules_id,))
        except ValueError:
            rule_name = f"**{RuleNameID}**"
            self.c.execute("DELETE FROM rules WHERE rule=?", (rule_name,))
        self.conn.commit()
        if self.c.rowcount == 0:
            return await ctx.send("⚠ No such entry exists.")
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(help='<rules_id or name>', hidden=True)
    @commands.has_any_role("Admin")
    async def editrule(self, ctx, RuleNameID: str, edit_type: str = "description"):
        try:
            rules_id = int(RuleNameID)
            self.c.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
        except ValueError:
            rule_name = f"**{RuleNameID}**"
            self.c.execute("SELECT * FROM rules WHERE rule=?", (rule_name,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        if not(edit_type.lower() in ["rulename", "description"]):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `rulename`, `description` (default).")
        timeout_edit = 30.0
        await ctx.send(f"Enter the new {edit_type} content (you have {timeout_edit} seconds to respond):")
        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=timeout_edit)
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")
        if edit_type.lower() == "rulename":
            self.c.execute("UPDATE rules SET rule=? WHERE id=?", (f"**{new_content.content}**", entry[0]))
        elif edit_type.lower() == "description":
            self.c.execute("UPDATE rules SET description=? WHERE id=?", (new_content.content, entry[0]))
        self.conn.commit()
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['rulesource'], hidden=True)
    @commands.has_any_role("Admin")
    async def ruleraw(self, ctx, RuleNameID: str, return_type: str = "both"):
        try:
            rules_id = int(RuleNameID)
            self.c.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
        except ValueError:
            rule_name = f"**{RuleNameID}**"
            self.c.execute("SELECT * FROM rules WHERE rule=?", (rule_name,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        if not(return_type[0] == "r" or return_type[0] == "d" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `rule`, `description`, `both` (default).")
        if return_type[0] == "r":
            msg = entry[1]
        elif return_type[0] == "d":
            msg = entry[2]
        else:
            msg = "\n\n".join([entry[1], entry[2]])
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command(aliases=['veiwrule', 'showrule'], help='<rules id or name>')
    async def rule(self, ctx, RuleNameID: str):
        try:
            rules_id = int(RuleNameID)
            self.c.execute("SELECT * FROM rules WHERE id=?", (rules_id,))
        except ValueError:
            rule_name = f"**{RuleNameID}**"
            self.c.execute("SELECT * FROM rules WHERE rule=?", (rule_name,))
        entry = self.c.fetchone()
        if entry is None:
            return await ctx.send("⚠ No such entry exists.")
        embed = discord.Embed(color=discord.Color.red())
        embed.title = entry[1]
        embed.description = entry[2]
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    async def refreshrules(self, ctx):
        await ctx.send("Refreshing rules...")
        self.bot.loop.create_task(self.update_rules())

def setup(bot):
    bot.add_cog(Rules(bot))