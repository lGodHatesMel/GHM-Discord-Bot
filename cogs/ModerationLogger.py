import discord
from discord.ext import commands
import json
from datetime import datetime
import utils

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
        embed = discord.Embed(
            title="Bad Words List", 
            description=", ".join(self.BadWords), 
            color=0x3498db
        )
        await ctx.send(embed=embed)

    @commands.command(aliases=["clear", "clearmessages"], help="1 to 100", hidden=True)
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

        # Check for blacklisted words
        for word in self.BadWords:
            if word in message.content.lower():
                if not any(role.name in self.AllowedRoles for role in message.author.roles):
                    await message.delete()
                    user_id = message.author.id
                    reason = f"Contains banned word: **{word}**"
                    await utils.LogAction(message.guild, 'AutoMod', 'Deletion', message.author, reason, user_id, None, None, None, self.config)
                    await self.LogBlacklistedWords(message.channel, 'Deletion', message.author, reason, user_id)

        # Check for blacklisted emojis
        for emoji in self.BadEmojis:
            if emoji in message.content:
                if not any(role.name in self.AllowedRoles for role in message.author.roles):
                    await message.delete()
                    user_id = message.author.id
                    reason = f"Contains banned emoji: {emoji}"
                    await utils.LogAction(message.guild, 'AutoMod', "Deletion", message.author, reason, user_id, None, None, None, self.config)
                    await self.LogBlacklistedEmojis(message.channel, 'Deletion', message.author, reason, user_id)

        # Check for links
        if 'http://' in message.content or 'https://' in message.content:
            if not any(role.name in self.AllowedRoles for role in message.author.roles):
                await message.delete()
                user_id = message.author.id
                reason = f"Message included a link: {message.content}"
                await utils.LogAction(message.guild, 'AutoMod', "Deletion", message.author, reason, user_id, None, None, None, self.config)
                await self.LogBlacklistedWords(message.channel, "Deletion", message.author, reason, user_id)

    @commands.Cog.listener()
    async def on_message_edit(self, before, after):
        if after.author.bot:
            return

        # Check for links
        if 'http://' in after.content or 'https://' in after.content:
            if not any(role.name.lower() in self.AllowedRoles for role in after.author.roles):
                await after.delete()
                user_id = after.author.id
                reason = "Message included a link"
                await utils.LogAction(after.guild, 'AutoMod', "Deletion", after.author, before.content, after.content, user_id, None, None, None, self.config)
                await self.LogBlacklistedWords(after.channel, "Deletion", after.author, reason, user_id)

        # Check for blacklisted words and emojis
        if any(word in after.content.lower() for word in self.BadWords) or any(emoji in after.content for emoji in self.BadEmojis):
            if not any(role.name.lower() in self.AllowedRoles for role in after.author.roles):
                await after.delete()
                user_id = after.author.id
                reason = "Message included a blacklisted word or emoji"
                await utils.LogAction(after.guild, 'AutoMod', "Deletion", after.author, before.content, after.content, user_id, None, None, None, self.config)
                await self.LogBlacklistedWords(after.channel, "Deletion", after.author, reason, user_id)

        MessageLoggerChannelID = self.config['channel_ids'].get('MessageLogs', None)

        if not MessageLoggerChannelID:
            print("Message logger channel ID is not set in config.json.")
            return

        LoggingChannel = self.bot.get_channel(MessageLoggerChannelID)
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')

        OrginalMessage = self.truncate_text(before.content, 1024)
        EditedMessage = self.truncate_text(after.content, 1024)

        embed = discord.Embed(color=discord.Color.orange())
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
        embed.set_footer(text=f"UID: {message.author.id} • ID: {message.id} • {timestamp}")

        await LoggingChannel.send(embed=embed)

    @staticmethod
    def truncate_text(text, length):
        return text[:length]

def setup(bot):
    bot.add_cog(ModerationLogger(bot))