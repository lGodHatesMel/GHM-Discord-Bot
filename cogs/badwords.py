import discord
from discord.ext import commands

class BannedWordsEmojis(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # t.me temu youtu.be
        self.delete_words = [
            "youtu.be", "temu", "t.me", "discord.gg", "youtu.be", "porn site",
            "TikTok", "9/11", "porno", "Hot Girls", "twin towers", "n-word",
            "nigger", "niger", "retard", "faggot", "fagot", "fagget", "faget",
            "nijjer", "nigjer", "nigher"
        ]
        self.reply_words = {
            "trigger1": "response1", 
            "trigger2": "response2"
        }
        #self.emoji_to_remove = "👎"  # Replace with the emoji you want to be removed

    @commands.Cog.listener()
    async def on_message(self, message):
        if any(word in message.content.lower() for word in self.delete_words):
            await message.delete()
            # await message.channel.send(f"{message.author.mention}, please refrain from using inappropriate language.")
            # can possibly log the incident or take further action

        for trigger, response in self.reply_words.items():
            if trigger in message.content.lower():
                await message.channel.send(response)
                # can possibly log the incident or take further action

    # @commands.Cog.listener()
    # async def on_reaction_add(self, reaction, user):
    #     if reaction.emoji == self.emoji_to_remove:
    #         await reaction.remove()
            # can possibly log the incident or take further action

def setup(bot):
    bot.add_cog(BannedWordsEmojis(bot))
