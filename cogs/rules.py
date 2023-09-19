import os
import random
import asyncio
import json
import time
import discord
from discord.ext import commands
import utils

class Rules(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config.json", "r") as f:
            self.config = json.load(f)
        self.image_folder = "Images"  # Replace with your folder path

    async def update_rules(self):
        rules_channel_id = self.config.get("rules_channel_id")
        with open("Database/rules.json", "r") as f:
            rules_db = json.load(f)
        messages = []
        image_files = os.listdir(self.image_folder)

        for rules_id, entry in enumerate(rules_db, start=1):
            # Create an embed with a random image from the folder as the header
            embed = discord.Embed(
                title=f"Rule {rules_id}",
                description=entry[1],
                color=discord.Color.green()
            )

            # Select a random image from the folder
            if image_files:
                random_image = random.choice(image_files)
                image_path = os.path.join(self.image_folder, random_image)
                embed.set_image(url="attachment://" + random_image)
                file = discord.File(image_path, filename=random_image)
                messages.append((embed, file))
            else:
                messages.append(embed)

        counter = 0
        msg = await self.bot.get_channel(rules_channel_id).fetch_message(rules_channel_id)
        async for message in self.bot.get_channel(rules_channel_id).history(limit=100, oldest_first=True, after=msg).filter(lambda m: m.author == self.bot.user):
            if counter < len(messages):
                if message.embeds and message.embeds[0].title == messages[counter][0].title \
                    and message.embeds[0].description == messages[counter][0].description:
                    counter += 1
                    continue
                time.sleep(2)  # avoid rate limits
                if len(messages[counter]) > 1:
                    await message.edit(embed=messages[counter][0], file=messages[counter][1])
                else:
                    await message.edit(embed=messages[counter][0])
                counter += 1
            else:
                await message.delete()
        for message_info in messages[counter:]:
            time.sleep(2)  # avoid rate limits
            embed = message_info[0]
            file = message_info[1] if len(message_info) > 1 else None
            await self.bot.get_channel(rules_channel_id).send(embed=embed, file=file)

    @commands.command()
    @commands.has_any_role("Admin")
    async def addrule(self, ctx):
        random_num = random.randint(1, 9999)
        await ctx.send("Type the rule to be added after this message:\n(note: all rules are automatically underlined)\n\nType `cancel-{:04d}` to cancel.".format(random_num))
        try:
            question = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            if question.content == "cancel-{:04d}".format(random_num):
                return await ctx.send("❌ Canceled by user.")
            random_num = random.randint(1, 9999)
            await ctx.send("Type the rule description after this message:\n\nType `cancel-{:04d}` to cancel.".format(random_num))
            answer = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            if answer.content == "cancel-{:04d}".format(random_num):
                return await ctx.send("❌ Canceled by user.")
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")
        if len("RX. __{}__\n{}".format(question.content, answer.content)) > 1950:
            return await ctx.send("⚠ This rule entry is too long.")
        with open("Database/rules.json", "r") as f:
            rules_db = json.load(f)
        rules_db.append([question.content, answer.content])
        with open("Database/rules.json", "w") as f:
            json.dump(rules_db, f, indent=4)
        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['delrule', 'dr'])
    @commands.has_any_role("Admin")
    async def deleterule(self, ctx, rules_id: int = 0):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        with open("Database/rules.json", "r") as f:
            rules_db = json.load(f)
        try:
            rules_db.pop(rules_id - 1)
        except IndexError:
            return await ctx.send("⚠ No such entry exists.")
        with open("Database/rules.json", "w") as f:
            json.dump(rules_db, f, indent=4)
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['modify'])
    @commands.has_any_role("Admin")
    async def editrule(self, ctx, rules_id: int = 0, edit_type: str = "d"):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        if not(edit_type[0] == "r" or edit_type[0] == "d"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `rule`, `description` (default).")
        with open("Database/rules.json", "r") as f:
            rules_db = json.load(f)
        try:
            rules_db[rules_id - 1]
        except IndexError:
            return await ctx.send("⚠ No such entry exists.")
        random_num = random.randint(1, 9999)
        edit_type_readable = {
            "r": "rule",
            "d": "description"
        }
        await ctx.send("Enter the new {} content:\n\nType `cancel-{:04d}` to cancel.".format(edit_type_readable[edit_type[0]], random_num))
        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            if new_content.content == "cancel-{:04d}".format(random_num):
                return await ctx.send("❌ Canceled by user.")
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, stopping.")
        if edit_type[0] == "r":
            rules_db[rules_id - 1][0] = new_content.content
        elif edit_type[0] == "d":
            rules_db[rules_id - 1][1] = new_content.content
        with open("Database/rules.json", "w") as f:
            json.dump(rules_db, f, indent=4)
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_rules())

    @commands.command(aliases=['source'])
    @commands.has_any_role("Admin")
    async def raw(self, ctx, rules_id: int = 0, return_type: str = "both"):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        if not(return_type[0] == "r" or return_type[0] == "d" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `rule`, `description`, `both` (default).")
        with open("Database/rules.json", "r") as f:
            rules_db = json.load(f)
        try:
            entry = rules_db[rules_id - 1]
        except IndexError:
            return await ctx.send("⚠ No such entry exists.")
        if return_type[0] == "r":
            msg = entry[0]
        elif return_type[0] == "d":
            msg = entry[1]
        else:
            msg = "\n\n".join(entry)
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command(aliases=['rule', 'showrule'])
    async def viewrule(self, ctx, rules_id: int = 0):
        if rules_id == 0:
            return await ctx.send("⚠ Rule entry ID is required.")
        with open("Database/rules.json", "r") as f:
            rules_db = json.load(f)
        try:
            entry = rules_db[rules_id - 1]
        except IndexError:
            return await ctx.send("⚠ No such entry exists.")
        embed = discord.Embed(color=discord.Color.red())
        embed.title = "R{}. {}".format(rules_id, entry[0])
        embed.description = entry[1]
        await ctx.send(embed=embed)

    @commands.command()
    async def refreshrules(self, ctx):
        await ctx.send("Refreshing rules...")
        self.bot.loop.create_task(self.update_rules())

def setup(bot):
    bot.add_cog(Rules(bot))
