import discord
from discord.ext import commands
import json
from datetime import datetime
import utils

class ModerationLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.delete_words = [
            "t.me", "Pedophile", "kys",

            "porn", "sex", "gay", "Homosexual", "Molest", "masterbate",
            "masterbation", "masturbate", "xrated", "vagina", "tittyfuck",
            "chaturbate",

            "niggers", "nigga", "nijja", "niggah", "niggaz", "nigg3r",
        ]
        self.delete_emojis = [] # ex: "🚫", "❌"
        self.reply_words = {
            "trigger1": "response1",
            "trigger2": "response2"
        }

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
            await ctx.message.delete()
            deleted_messages = await ctx.channel.purge(limit=amount)

            await ctx.send(f"Cleared {len(deleted_messages)} messages.", delete_after=5)

        except commands.MissingPermissions:
            await ctx.send("Bot doesn't have the necessary permissions to clear messages.")

    async def log_mod_action(self, guild, action, target, reason, user_id):
        await utils.log_mod_action(guild, action, target, reason, user_id, config=self.config)

    async def LogBlacklistedWords(self, channel, action, target, reason, user_id):
        timestamp = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')

        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{target.name}", icon_url=target.avatar_url)
        embed.description = f"{action} in {channel.mention}"
        embed.add_field(name=f"{action} Message", value=reason, inline=False)
        embed.set_footer(text=f"UID: {user_id} • {timestamp}")

        await channel.send(embed=embed)

        removed_message = f"**Message Removed:** This message contained a blacklisted word/trigger and has been removed."
        await channel.send(removed_message)

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check for blacklisted words
        if any(word in message.content.lower() for word in self.delete_words):
            await message.delete()
            user_id = message.author.id
            reason = "Contains banned word/trigger"
            await self.log_mod_action(message.guild, "Deletion", message.author, reason, user_id)
            await self.LogBlacklistedWords(message.channel, "Deletion", message.author, reason, user_id)

        # Check for blacklisted emojis
        if any(emoji in message.content for emoji in self.delete_emojis):
            if not any(role.name.lower() in ["admin", "moderator", "helper"] for role in message.author.roles):
                await message.delete()
                user_id = message.author.id
                reason = "Contains banned emoji"
                await self.log_mod_action(message.guild, "Deletion", message.author, reason, user_id)
                await self.LogBlacklistedEmojis(message.channel, "Deletion", message.author, reason, user_id)

        # Check for trigger words
        for trigger, response in self.reply_words.items():
            if trigger in message.content.lower():
                if not any(role.name.lower() in ["admin", "moderator", "helper"] for role in message.author.roles):
                    await message.channel.send(response)
                    user_id = message.author.id
                    reason = f"Contains trigger word: {trigger}"
                    await self.log_mod_action(message.guild, "Response Sent", message.author, reason, user_id)
                    await self.LogBlacklistedWords(message.channel, "Response Sent", message.author, reason, user_id)

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
        embed.set_footer(text=f"UID: {message.author.id} • ID: {message.id} • {timestamp}")

        await logging_channel.send(embed=embed)

    @staticmethod
    def truncate_text(text, length):
        return text[:length]

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if before.author.bot:
            return

        # Check if the edited message or its embeds contain a link
        if 'http://' in after.content or 'https://' in after.content or any('http://' in e.url or 'https://' in e.url for e in after.embeds):
            await after.delete()
            user_id = after.author.id
            reason = "Edited message to include a link"
            await self.log_mod_action(after.guild, "Deletion", after.author, reason, user_id)
            await self.LogBlacklistedWords(after.channel, "Deletion", after.author, reason, user_id)
            return  # Return early to prevent logging the edit

        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            message_logger_channel_id = config.get("message_logger_channel_id")

        if not message_logger_channel_id:
            print("Message logger channel ID is not set in config.json.")
            return

        logging_channel = self.bot.get_channel(message_logger_channel_id)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
    async def on_ready(self):
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

def setup(bot):
    bot.add_cog(ModerationLogger(bot))