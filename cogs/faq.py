import os
import asyncio
import json
import random
import time
import discord
from discord.ext import commands

class Faq(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.faq_aliases = {}
        with open('faq_aliases.json', 'r') as f:
            self.faq_aliases = json.load(f)
        database_folder = 'Database'
        self.json_file = os.path.join(database_folder, 'faq.json')
    
    def save_aliases(self):
        with open('faq_aliases.json', 'w') as f:
            json.dump(self.faq_aliases, f, indent=4)

    async def update_faq(self, ctx):
        faq_channel_id = self.bot.config.get('faq_channel_id')

        if faq_channel_id is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        # Get the FAQ channel from the guild
        faq_channel = ctx.guild.get_channel(faq_channel_id)

        if not faq_channel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'faq_channel_id' in config.json points to a valid channel.")
            return

        with open(self.json_file, "r") as f:
            faq_db = json.load(f)
        messages = []
        for faq_name, entry in faq_db.items():
            embed = discord.Embed(color=discord.Color.red())
            embed.title = f"FAQ {faq_name.upper()}"
            embed.add_field(name="Question:", value=entry['question'], inline=False)  # Using an embed field for the question
            embed.add_field(name="Answer:", value=f"```{entry['answer']}```", inline=False)  # Using an embed field for the answer
            aliases = []
            for word, faq in self.faq_aliases.items():
                if faq == faq_name:
                    aliases.append(word)
            if aliases:
                embed.set_footer(text="Aliases: " + ", ".join(aliases))
            messages.append(embed)
        
        for message in messages:
            # Check if a message with the same title exists in the FAQ channel
            existing_message = None
            async for msg in faq_channel.history(limit=100):
                if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == message.title:
                    existing_message = msg
                    break
            
            if existing_message:
                # If an existing message is found, edit it
                await existing_message.edit(embed=message)
            else:
                # If no existing message is found, send a new one
                await faq_channel.send(embed=message)

        self.save_aliases()

    @commands.command()
    @commands.has_any_role("Admin")
    async def addfaq(self, ctx):
        # Check if 'faq_channel_id' is set
        faq_channel_id = self.bot.config.get('faq_channel_id')

        if faq_channel_id is None:
            await ctx.send("⚠ FAQ channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        # Get the FAQ channel from the guild
        faq_channel = ctx.guild.get_channel(faq_channel_id)

        if not faq_channel:
            await ctx.send("⚠ FAQ channel not found. Make sure 'faq_channel_id' in config.json points to a valid channel.")
            return

        await ctx.send("Type the name for this FAQ entry (no spaces or special characters), or type `cancel` to cancel:")

        try:
            name = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            name = name.content.lower()  # Convert the name to lowercase and remove special characters if needed
            if name == "cancel":
                return await ctx.send("❌ Canceled by user.")
            
            await ctx.send("Type the question to be added after this message (note: all questions are automatically underlined):")

            question = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            question_content = question.content

            await ctx.send("Type the answer after this message:")

            answer = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            answer_content = answer.content

        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")

        if len("❔ QX. __{}__\n{}".format(question_content, answer_content)) > 1950:
            return await ctx.send("⚠ This FAQ entry is too long.")

        # Read existing faq_db from the JSON file
        with open(self.json_file, "r") as f:
            faq_db = json.load(f)

        # Check if the name is already in use
        if name in faq_db:
            return await ctx.send("⚠ This name is already in use for another FAQ entry.")

        # Append the new FAQ entry with the name as the key
        faq_db[name] = {
            "question": question_content,
            "answer": answer_content
        }

        # Write the updated faq_db back to the JSON file
        with open(self.json_file, "w") as f:
            json.dump(faq_db, f, indent=4)

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command()
    @commands.has_any_role("Admin")
    async def faqalias(self, ctx, faq_name: str = "", *, words: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        for word in words.strip().split():
            self.faq_aliases[word] = faq_name
        with open('faq_aliases.json', "w") as f:
            json.dump(self.faq_aliases, f, indent=4)
        await ctx.send("✅ Alias added/updated.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command()
    @commands.has_any_role("Admin")
    async def delalias(self, ctx, word: str):
        if word not in self.faq_aliases:
            return await ctx.send("⚠ FAQ alias does not exist.")
        del self.faq_aliases[word]
        with open('faq_aliases.json', "w") as f:
            json.dump(self.faq_aliases, f, indent=4)
        await ctx.send("✅ Alias removed.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command()
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

    @commands.command(aliases=['df'])
    @commands.has_any_role("GitHub Contributors", "Moderators", "aww")
    async def deletefaq(self, ctx, faq_name: str = ""):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        with open(self.json_file, "r") as f:
            faq_db = json.load(f)
        try:
            del faq_db[faq_name]
            for word, faq in self.faq_aliases.items():
                if faq == faq_name:
                    del self.faq_aliases[word]
            with open('faq_aliases.json', "w") as f:
                json.dump(self.faq_aliases, f, indent=4)
        except KeyError:
            return await ctx.send("⚠ No such entry exists.")
        with open(self.json_file, "w") as f:
            json.dump(faq_db, f, indent=4)
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command()
    @commands.has_any_role("Admin")
    async def editfaq(self, ctx, faq_name: str = "", edit_type: str = "a"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(edit_type[0] == "q" or edit_type[0] == "a"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer` (default).")
        with open(self.json_file, "r") as f:
            faq_db = json.load(f)
        try:
            entry = faq_db[faq_name]
        except KeyError:
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
        
        # Update the appropriate field in the FAQ entry
        if edit_type[0] == "q":
            entry['question'] = new_content.content
        elif edit_type[0] == "a":
            entry['answer'] = new_content.content
        
        # Update the entry in the faq_db
        faq_db[faq_name] = entry
        
        with open(self.json_file, "w") as f:
            json.dump(faq_db, f, indent=4)
        
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_faq(ctx))

    @commands.command(aliases=['fr'])
    async def faqraw(self, ctx, faq_name: str = "", return_type: str = "both"):
        if not faq_name:
            return await ctx.send("⚠ FAQ entry name is required.")
        if not(return_type[0] == "q" or return_type[0] == "a" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `answer`, `both` (default).")
        with open(self.json_file, "r") as f:
            faq_db = json.load(f)
        try:
            entry = faq_db[faq_name]
        except KeyError:
            return await ctx.send("⚠ No such entry exists.")
        if return_type[0] == "q":
            msg = entry['question']
        elif return_type[0] == "a":
            msg = entry['answer']
        else:
            msg = "\n\n".join([entry['question'], entry['answer']])
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command()
    async def faqview(self, ctx, faq_req: str):
        with open(self.json_file, "r") as f:
            faq_db = json.load(f)

        if faq_req not in faq_db:
            return await ctx.send("⚠ No such entry exists.")

        entry = faq_db[faq_req]
        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"FAQ: {faq_req.upper()}"
        embed.add_field(name="Question:", value=entry['question'], inline=False)
        embed.add_field(name="Answer:", value=f"```{entry['answer']}```", inline=False)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.has_any_role("Admin")
    async def refreshfaq(self, ctx):
        await ctx.send("Refreshing FAQ...")
        self.bot.loop.create_task(self.update_faq(ctx))

def setup(bot):
    bot.add_cog(Faq(bot))
