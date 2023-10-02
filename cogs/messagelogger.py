import discord
from discord.ext import commands
import json
from datetime import datetime
import utils

class MessageLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(aliases=["clear", "purge"], hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def clearmessages(self, ctx, amount: int):
        """
        Clear a specified number of messages from the channel.
        Usage: !clear_messages <amount>
        """
        if amount <= 0:
            await ctx.send("Please specify a valid number of messages to clear.")
            return

        if amount > 100:
            await ctx.send("You can only clear up to 100 messages at a time.")
            return

        try:
            # Delete the command message
            await ctx.message.delete()
            # Delete the specified number of messages
            deleted_messages = await ctx.channel.purge(limit=amount)

            await ctx.send(f"Cleared {len(deleted_messages)} messages.", delete_after=5)

        except commands.MissingPermissions:
            await ctx.send("Bot doesn't have the necessary permissions to clear messages.")
            
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Check if the message is from a user and not a bot
        if message.author.bot:
            return

        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            message_logger_channel_id = config.get("message_logger_channel_id")

        if not message_logger_channel_id:
            print("Message logger channel ID is not set in config.json.")
            return

        logging_channel = self.bot.get_channel(message_logger_channel_id)
        timestamp = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{message.author.name}", icon_url=message.author.avatar_url)
        embed.description = f"Message deleted in {message.channel.mention}"
        embed.add_field(name="Deleted Message", value=message.content, inline=False)
        embed.set_footer(text=f"UID: {message.author.id} • Message ID: {message.id} • {timestamp}")

        await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        # Check if the edited message is from a user and not a bot
        if before.author.bot:
            return

        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            message_logger_channel_id = config.get("message_logger_channel_id")

        if not message_logger_channel_id:
            print("Message logger channel ID is not set in config.json.")
            return

        logging_channel = self.bot.get_channel(message_logger_channel_id)
        timestamp = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')

        original_message = utils.truncate_text(before.content, 1024)
        edited_message = utils.truncate_text(after.content, 1024)

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=f"{before.author.name}", icon_url=before.author.avatar_url)
        embed.description = f"Message edited in {before.channel.mention}"
        embed.add_field(name="Original Message", value=original_message, inline=False)
        embed.add_field(name="Edited Message", value=edited_message, inline=False)
        embed.set_footer(text=f"UID: {before.author.id} • Message ID: {before.id} • {timestamp}")

        await logging_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(MessageLogger(bot))