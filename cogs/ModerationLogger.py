import discord
from discord.ext import commands
import os
import json
from datetime import datetime
import utils.utils as utils
from utils.Paginator import Paginator
import re

class ModerationLogger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config.json') as f:
            self.config = json.load(f)

        self.AllowedRoles = ['Owner', 'Admin', 'Moderator', 'Helper', "Bypass"]
        self.BadEmojis = [] # ex: "🚫", "❌"
        with open('Data/BadWordList.txt', 'r') as file:
            self.BadWords = [word.strip() for word in file.read().split(',')]
        print("BadWordList.txt was loaded successfully.")

    @commands.command(help="Add word to the bad word list", hidden=True)
    @commands.has_any_role('Admin', 'Moderator')
    async def addbadword(self, ctx, *, word):
        self.BadWords.append(word)
        with open('Data/BadWordList.txt', 'a') as file:
            file.write(f', {word}')
        await ctx.send(f'Word "{word}" has been added to the bad words list.')

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

    async def LogBlacklistedWords(self, channel, action, target, reason, user_id):
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{target.name}", icon_url=target.avatar_url)
        embed.description = f"{action} in {channel.mention}"
        embed.add_field(name=f"{action} Message", value=reason, inline=False)
        embed.set_footer(text=f"UID: {user_id} • {timestamp}")

        if len(embed.fields) > 25:
            embed.fields = embed.fields[:25]
        await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not isinstance(message.author, discord.Member):
            return

        if os.path.exists('Data/AllowwedLinks.txt'):
            with open('Data/AllowwedLinks.txt', 'r') as file:
                self.AllowedLinks = [line.strip() for line in file.readlines()]
        else:
            self.AllowedLinks = []

        # Check for blacklisted words
        for word in self.BadWords:
            if word in message.content.lower():
                if not any(role.name in self.AllowedRoles for role in message.author.roles):
                    await message.delete()
                    reason = f"Contains banned word: `{word}`\n\n**Message Content:** \n```{message.content}```\n\n**Channel:** {message.channel.mention}"
                    await utils.LogAction(
                        message.guild,
                        "AutoMod",
                        "Blacklisted",
                        message.author,
                        reason,
                        config=self.config,
                    )

        # Check for links
        if 'http://' in message.content or 'https://' in message.content:
            if not any(role.name in self.AllowedRoles for role in message.author.roles):
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', message.content)
                if not any(url in self.AllowedLinks for url in urls):
                    await message.delete()
                    url_message = "Message included a link:\n" + ", ".join(urls) if urls else "No links in message"
                    reason = f"{url_message}\n\n**Message Content:** \n```{message.content}```\n\n**Channel:** {message.channel.mention}"
                    await utils.LogAction(
                        message.guild,
                        "AutoMod",
                        "Blacklisted",
                        message.author,
                        reason,
                        config=self.config,
                    )

        # Check for blacklisted emojis
        for emoji in self.BadEmojis:
            if emoji in message.content:
                if not any(role.name in self.AllowedRoles for role in message.author.roles):
                    await message.delete()
                    reason = f"Message contains banned emoji: `**{emoji}**`\n\n**Message Content:** \n```{message.content}```\n\n**Channel:** {message.channel.mention}"
                    await utils.LogAction(
                        message.guild,
                        "AutoMod",
                        "Blacklisted",
                        message.author,
                        reason,
                        config=self.config,
                    )

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return

        if os.path.exists('Data/AllowedLinks.txt'):
            with open('Data/AllowedLinks.txt', 'r') as file:
                self.AllowedLinks = [line.strip() for line in file.readlines()]
        else:
            self.AllowedLinks = []

        for word in self.BadWords:
            if word in after.content.lower():
                if not any(role.name in self.AllowedRoles for role in after.author.roles):
                    await after.delete()
                    reason = f"Message was edited to include banned word: `**{word}**`\n\n**Original Message Content:** \n```{before.content}```\n\n**Edited Message Content:** \n```{after.content}```\n\n**Channel:** {after.channel.mention}"
                    await utils.LogAction(
                        after.guild,
                        "AutoMod",
                        "Blacklisted",
                        after.author,
                        reason,
                        config=self.config
                    )

        if 'http://' in after.content or 'https://' in after.content:
            if not any(role.name.lower() in self.AllowedRoles for role in after.author.roles):
                urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', after.content)
                if not any(url in self.AllowedLinks for url in urls):
                    await after.delete()
                    url_message = "Message was edited to include a link:\n" + ", ".join(urls) if urls else "No links in message"
                    reason = f"{url_message}\n\n**Original Message Content:** \n```{before.content}```\n\n**Edited Message Content:** \n```{after.content}```\n\n**Channel:** {after.channel.mention}"
                    await utils.LogAction(
                        after.guild,
                        "AutoMod",
                        "Blacklisted",
                        after.author,
                        reason,
                        config=self.config
                    )

        for emoji in self.BadEmojis:
            if emoji in after.content:
                if not any(role.name in self.AllowedRoles for role in after.author.roles):
                    await after.delete()
                    reason = f"Message was edited to include banned word: `**{word}**`\n\n**Original Message Content:** \n```{before.content}```\n\n**Edited Message Content:** \n```{after.content}```\n\n**Channel:** {after.channel.mention}"
                    await utils.LogAction(
                        after.guild,
                        "AutoMod",
                        "Blacklisted",
                        after.author,
                        reason,
                        config=self.config
                    )

        MessageLoggerChannelID = self.config['channel_ids'].get('MessageLogs', None)
        if not MessageLoggerChannelID:
            print("Message logger channel ID is not set in config.json.")
            return

        LoggingChannel = self.bot.get_channel(MessageLoggerChannelID)
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        OrginalMessage = self.truncate_text(before.content, 1024)
        EditedMessage = self.truncate_text(after.content, 1024)

        embed = discord.Embed(color=discord.Color.orange(), title="✏️ Edit Messages")
        embed.set_author(name=f"{before.author.name}", icon_url=before.author.avatar_url)
        embed.description = f"Message edited in {before.channel.mention}"
        embed.add_field(name="Original Message", value=OrginalMessage, inline=False)
        embed.add_field(name="Edited Message", value=EditedMessage, inline=False)
        embed.set_footer(text=f"UID: {before.author.id} • ID: {before.id} • {timestamp}")
        await LoggingChannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        if message.author.bot:
            return

        MessageLoggerChannelID = self.config['channel_ids'].get('MessageLogs', None)
        if not MessageLoggerChannelID:
            print("Message logger channel ID is not set in config.json.")
            return

        LoggingChannel = self.bot.get_channel(MessageLoggerChannelID)
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        embed = discord.Embed(color=discord.Color.red())
        embed.set_author(name=f"{message.author.name}", icon_url=message.author.avatar_url)
        embed.description = f"Message deleted in {message.channel.mention}"

        # Truncate the message if it's longer than 1024 characters
        if len(message.content) > 1024:
            truncated_message = message.content[:1021] + "..."
        else:
            truncated_message = message.content

        embed.add_field(name="Deleted Message", value=truncated_message, inline=False)
        embed.set_footer(text=f"👤 UID: `{message.author.id}` | 🕒 `{timestamp}`")
        # embed.set_footer(text=f"👤 UID: `{message.author.id}` | 📄 ID: `{message.id}` | 🕒 `{timestamp}`")
        await LoggingChannel.send(embed=embed)

    @staticmethod
    def truncate_text(text, length):
        return text[:length]

def setup(bot):
    bot.add_cog(ModerationLogger(bot))
