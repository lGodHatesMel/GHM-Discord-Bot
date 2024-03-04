import discord
from discord.ext import commands
import json
from datetime import datetime
import utils.utils as utils
from utils.Paginator import Paginator

class ModerationLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config.json') as f:
            self.config = json.load(f)
        with open('Data/BadWordList.txt', 'r') as file:
            self.BadWords = file.read().splitlines()

    @commands.command(help="Add word to the bad word list", hidden=True)
    @commands.has_any_role('Admin', 'Moderator')
    async def addbadword(self, ctx, *, word):
        self.BadWords.append(word)
        with open('Data/BadWordList.txt', 'a') as file:
            file.write(f'{word}\n')
        await ctx.message.reply(f'Word "{word}" has been added to the bad words list.')

    @commands.command(help="Show current bad word list",hidden=True)
    @commands.has_any_role('Admin', 'Moderator')
    async def badwordlist(self, ctx):
        words_per_page = 50  # Adjust as needed
        bad_words = [self.BadWords[i:i + words_per_page] for i in range(0, len(self.BadWords), words_per_page)]
        embeds = [discord.Embed(title="Bad Words List", description=", ".join(words), color=0x3498db) for words in bad_words]
        
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    @commands.command(aliases=["clearmessages"], help="1 to 100", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def purge(self, ctx, amount: int):
        if amount <= 0:
            await ctx.send("Please specify a valid number of messages to clear.")
            return

        if amount > 100:
            await ctx.send("You can only clear up to 100 messages at a time.")
            return

        try:
            await ctx.message.delete()
            deleted_messages = await ctx.channel.purge(limit=amount, bulk=True)
            await ctx.send(f"Cleared {len(deleted_messages)} messages.", delete_after=5)
        except commands.MissingPermissions:
            await ctx.send("Bot doesn't have the necessary permissions to clear messages.")

def setup(bot):
    bot.add_cog(ModerationLogger(bot))
