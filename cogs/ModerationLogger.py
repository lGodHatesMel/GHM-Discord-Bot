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
        self.BadWords = [
            "t.me", "Pedophile", "kys",

            "porn", "sex", "gay", "Homosexual", "Molest", "masterbate",
            "masterbation", "masturbate", "xrated", "vagina", "tittyfuck",
            "chaturbate",

            "niggers", "nigga", "nijja", "niggah", "niggaz", "nigg3r",
        ]
        self.BadEmojis = [] # ex: "🚫", "❌"

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

        # removed_message = f"**Message Removed:** This message contained a blacklisted word/trigger and has been removed."
        # await channel.send(removed_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check for blacklisted words
        for word in self.BadWords:
            if word in message.content.lower():
                if not any(role.name.lower() in self.AllowedRoles for role in message.author.roles):
                    await message.delete()
                    user_id = message.author.id
                    reason = f"Contains banned word: **{word}**"
                    await self.LogModAction(message.guild, "Deletion", message.author, reason, user_id)
                    await self.LogBlacklistedWords(message.channel, "Deletion", message.author, reason, user_id)

        # Check for blacklisted emojis
        for emoji in self.BadEmojis:
            if emoji in message.content:
                if not any(role.name.lower() in self.AllowedRoles for role in message.author.roles):
                    await message.delete()
                    user_id = message.author.id
                    reason = f"Contains banned emoji: {emoji}"
                    await self.LogModAction(message.guild, "Deletion", message.author, reason, user_id)
                    await self.LogBlacklistedEmojis(message.channel, "Deletion", message.author, reason, user_id)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return

        # Check for blacklisted links
        if 'http://' in after.content or 'https://' in after.content:
            if not any(role.name.lower() in self.AllowedRoles for role in after.author.roles):
                await after.delete()
                user_id = after.author.id
                reason = "Message included a link"
                await self.LogModAction(after.guild, "Deletion", after.author, before.content, after.content, user_id)
                await self.LogBlacklistedWords(after.channel, "Deletion", after.author, reason, user_id)

        # Check for blacklisted words and emojis
        if any(word in after.content.lower() for word in self.BadWords) or any(emoji in after.content for emoji in self.BadEmojis):
            if not any(role.name.lower() in self.AllowedRoles for role in after.author.roles):
                await after.delete()
                user_id = after.author.id
                reason = "Message included a blacklisted word or emoji"
                await self.LogModAction(after.guild, "Deletion", after.author, before.content, after.content, user_id)
                await self.LogBlacklistedWords(after.channel, "Deletion", after.author, reason, user_id)

        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            message_logger_channel_id = config.get("message_logger_channel_id")

        if not message_logger_channel_id:
            print("Message logger channel ID is not set in config.json.")
            return

        LoggingChannel = self.bot.get_channel(message_logger_channel_id)
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')

        original_message = self.truncate_text(before.content, 1024)
        edited_message = self.truncate_text(after.content, 1024)

        embed = discord.Embed(color=discord.Color.orange())
        embed.set_author(name=f"{before.author.name}", icon_url=before.author.avatar_url)
        embed.description = f"Message edited in {before.channel.mention}"
        embed.add_field(name="Original Message", value=original_message, inline=False)
        embed.add_field(name="Edited Message", value=edited_message, inline=False)
        embed.set_footer(text=f"UID: {before.author.id} • ID: {before.id} • {timestamp}")

        await LoggingChannel.send(embed=embed)

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

        LoggingChannel = self.bot.get_channel(message_logger_channel_id)
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

        await LoggingChannel.send(embed=embed)

    @staticmethod
    def truncate_text(text, length):
        return text[:length]

    @commands.Cog.listener()
    async def on_ready(self):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

def setup(bot):
    bot.add_cog(ModerationLogger(bot))