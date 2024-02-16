import discord
from discord.ext import commands
import json
from datetime import datetime
import utils

class ModerationLogger(commands.Cog):
    hidden = True

    def __init__(self, bot):
        self.bot = bot
        self.AllowedRoles = ['Admin', 'Moderator', 'Helper', "Bypass"]
        self.DeleteWords = [
            "t.me", "Pedophile", "kys",

            "porn", "sex", "gay", "Homosexual", "Molest", "masterbate",
            "masterbation", "masturbate", "xrated", "vagina", "tittyfuck",
            "chaturbate",

            "niggers", "nigga", "nijja", "niggah", "niggaz", "nigg3r",
        ]
        self.delete_emojis = [] # ex: "🚫", "❌"
        self.reply_words = {
            # "trigger1": "response1",
            # "trigger2": "response2"
        }

    @commands.command(aliases=["clear", "clearmessages"], hidden=True)
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
            deleted_messages = await ctx.channel.purge(limit=amount)

            await ctx.send(f"Cleared {len(deleted_messages)} messages.", delete_after=5)

        except commands.MissingPermissions:
            await ctx.send("Bot doesn't have the necessary permissions to clear messages.")

    async def LogModAction(self, guild, action, target, reason, user_id):
        await utils.LogModAction(guild, action, target, reason, user_id, config=self.config)

    async def LogBlacklistedWords(self, channel, action, target, reason, user_id):
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{target.name}", icon_url=target.avatar_url)
        embed.description = f"{action} in {channel.mention}"
        embed.add_field(name=f"{action} Message", value=reason, inline=False)
        embed.set_footer(text=f"UID: {user_id} • {timestamp}")

        if len(embed.fields) > 25:
            embed.fields = embed.fields[:25]

        await channel.send(embed=embed)

        removed_message = f"**Message Removed:** This message contained a blacklisted word/trigger and has been removed."
        await channel.send(removed_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check for blacklisted words
        if any(word in message.content.lower() for word in self.DeleteWords):
            if not any(role.name.lower() in self.AllowedRoles for role in message.author.roles):
                await message.delete()
                user_id = message.author.id
                reason = "Contains banned word/trigger"
                await self.LogModAction(message.guild, "Deletion", message.author, message.content, user_id)
                await self.LogBlacklistedWords(message.channel, "Deletion", message.author, reason, user_id)

        # Check for blacklisted emojis
        if any(emoji in message.content for emoji in self.delete_emojis):
            if not any(role.name.lower() in self.AllowedRoles for role in message.author.roles):
                await message.delete()
                user_id = message.author.id
                reason = "Contains banned emoji"
                await self.LogModAction(message.guild, "Deletion", message.author, reason, user_id)
                await self.LogBlacklistedEmojis(message.channel, "Deletion", message.author, reason, user_id)

        # Check for trigger words
        for trigger, response in self.reply_words.items():
            if trigger in message.content.lower():
                if not any(role.name.lower() in self.AllowedRoles for role in message.author.roles):
                    await message.channel.send(response)
                    user_id = message.author.id
                    reason = f"Contains trigger word: {trigger}"
                    await self.LogModAction(message.guild, "Response Sent", message.author, reason, user_id)
                    await self.LogBlacklistedWords(message.channel, "Response Sent", message.author, reason, user_id)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return

        if after.channel.name == 'message-logs':
            return
        # Check for blacklisted links
        if 'http://' in after.content or 'https://' in after.content:
            if not any(role.name.lower() in self.AllowedRoles for role in after.author.roles):
                await after.delete()
                user_id = after.author.id
                reason = "Message included a link"
                await self.LogModAction(after.guild, "Deletion", after.author, after.content, user_id)
                await self.LogBlacklistedWords(after.channel, "Deletion", after.author, reason, user_id)

        if before.content != after.content:
            await self.LogModAction(after.guild, "Edit", after.author, "Message edited", before.content)

        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            message_logger_channel_id = config.get("message_logger_channel_id")

        if not message_logger_channel_id:
            print("Message logger channel ID is not set in config.json.")
            return

        logging_channel = self.bot.get_channel(message_logger_channel_id)
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')

        original_message = self.truncate_text(before.content, 1024)
        edited_message = self.truncate_text(after.content, 1024)

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=f"{before.author.name}", icon_url=before.author.avatar_url)
        embed.description = f"Message edited in {before.channel.mention}"
        embed.add_field(name="Original Message", value=original_message, inline=False)
        embed.add_field(name="Edited Message", value=edited_message, inline=False)
        embed.set_footer(text=f"UID: {before.author.id} • ID: {before.id} • {timestamp}")

        await logging_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            message_logger_channel_id = config.get("message_logger_channel_id")

        if not message_logger_channel_id:
            print("Message logger channel ID is not set in config.json.")
            return

        logging_channel = self.bot.get_channel(message_logger_channel_id)
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{message.author.name}", icon_url=message.author.avatar_url)
        embed.description = f"Message deleted in {message.channel.mention}"
        
        # Truncate the message if it's longer than 1024 characters
        if len(message.content) > 1024:
            truncated_message = message.content[:1021] + "..."
        else:
            truncated_message = message.content

        embed.add_field(name="Deleted Message", value=truncated_message, inline=False)
        embed.set_footer(text=f"UID: {message.author.id} • ID: {message.id} • {timestamp}")

        await logging_channel.send(embed=embed)

    @staticmethod
    def truncate_text(text, length):
        return text[:length]

    @commands.Cog.listener()
    async def on_ready(self):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

def setup(bot):
    bot.add_cog(ModerationLogger(bot))