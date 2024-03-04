import discord
from discord.ext import commands
import utils.utils as utils
from utils.botdb import create_connection
from utils.utils import custom_emojis
import os
import json
import sqlite3
from sqlite3 import Error
import random
import re
from colorama import Fore, Style


class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = create_connection('Database/DBInfo.db')
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)
        self.AllowedRoles = ['Owner', 'Admin', 'Moderator', 'Helper', "Bypass", "🤫"]
        self.BadEmojis = [] # ex: "🚫", "❌"
        with open('Data/BadWordList.txt', 'r') as file:
            self.BadWords = [word.strip() for word in file.read().split(',')]
        print("BadWordList.txt was loaded successfully.")

    ## ON_MEMBERS
    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = self.bot.get_channel(int(self.WelcomeChannelID))

        if channel:
            server = member.guild
            member_count = sum(1 for member in server.members if not member.bot)
            member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"
            random_color = random.randint(0, 0xFFFFFF)

            uid = str(member.id)
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if user:
                print(f"User ({member.name} : {uid}) is already in the database and has joined back @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")
                user_info = json.loads(user[1])
                print(f"User left at {user_info['info']['Left']}")
                user_info["info"]["Left"] = None
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                embed = discord.Embed(
                    title="Welcome Back!",
                    description=f"Welcome back to GodHatesMe Gaming Centre {member.mention}, you are our {member_number}!\n\n"
                                f"Don't forget to read <#956760032232484884> and to get your Roles go to <#956769501607755806>!",
                    color=random_color,
                )
            else:
                user_info = {
                    "info": {
                        "Joined": member.joined_at.strftime('%m-%d-%y %H:%M'),
                        "Account_Created": member.created_at.strftime('%m-%d-%y %H:%M'),
                        "Left": None,
                        "username": member.name,
                        "avatar_url": str(member.avatar_url),
                    },
                    "moderation": {
                        "warns": [],
                        "notes": [],
                        "banned": [],
                        "kick_reason": [],
                        "kicks_amount": 0
                    }
                }
                print(f"{Fore.GREEN}Added new user ({member.name} : {uid}) to the database  @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}User joined at {user_info['info']['Joined']} and account was created at {user_info['info']['Account_Created']}{Style.RESET_ALL}")
                if not member.bot:
                    user_info["info"]["roles"] = [role.name for role in member.roles]
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (uid, json.dumps(user_info)))
                embed = discord.Embed(
                    title="Welcome!",
                    description=f"Welcome to GodHatesMe Gaming Centre {member.mention}, you are our {member_number}!\n\n"
                                f"Don't forget to read <#956760032232484884> and to get your Roles go to <#956769501607755806>!",
                    color=random_color,
                )

            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text=member.name)
            await channel.send(embed=embed)
            self.conn.commit()

            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if user:
                user_info = json.loads(user[1])
                if user_info["moderation"].get("banned"):
                    for ban_info in user_info["moderation"]["banned"]:
                        await utils.LogAction(
                            server,
                            "ModLogs",
                            "Previously Banned",
                            member,
                            f"Previously banned for: {ban_info['reason']}",
                            config=self.config,
                        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # print(f"DEBUG: on_member_remove event triggered for {member.name} ({member.id})")
        channel = self.bot.get_channel(int(self.WelcomeChannelID))
        if channel:
            server = member.guild
            member_count = sum(1 for member in server.members if not member.bot)
            member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"
            random_color = random.randint(0, 0xFFFFFF)
            goodbye = {
                "title": "Goodbye!",
                "description": f"We are sad to see you go, {member.mention}. You were our {member_number}.\n\n"
                            f"We hope you enjoyed your stay at GodHatesMe Gaming Centre!",
                "color": random_color,
            }

            embed = discord.Embed(**goodbye)
            embed.set_thumbnail(url=member.avatar_url)
            embed.set_footer(text=member.name)

            await channel.send(embed=embed)

            uid = str(member.id)
            print(f"({member.name} : {uid}) left the server as the {member_number} @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            left_datetime = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            if user:
                user_info = json.loads(user[1])
                print(f"{Fore.YELLOW}User ({member.name} : {uid}) left the server as the {member_number} @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}User joined at {user_info['info']['Joined']}{Style.RESET_ALL} and {Fore.RED}account was created at {user_info['info']['Account_Created']}{Style.RESET_ALL}")
                if "Left" in user_info["info"] and user_info["info"]["Left"] is not None:
                    user_info["info"]["Left"].append(left_datetime)
                else:
                    user_info["info"]["Left"] = [left_datetime]
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            else:
                user_info = {
                    "info": {
                        "Joined": member.joined_at.strftime('%m-%d-%y %H:%M'),
                        "Account_Created": member.created_at.strftime('%m-%d-%y %H:%M'),
                        "Left": None,
                        "username": member.name,
                        "avatar_url": str(member.avatar_url),
                        "roles": [role.name for role in member.roles]
                    },
                    "moderation": {
                        "warns": [],
                        "notes": [],
                        "banned": [],
                        "kick_reason": [],
                        "kicks_amount": 0
                    }
                }
                print(f"{Fore.GREEN}Added new user ({member.name} : {uid}) to the database  @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}{Style.RESET_ALL}")
                print(f"{Fore.BLUE}User joined at {user_info['info']['Joined']} and account was created at {user_info['info']['Account_Created']}{Style.RESET_ALL}")
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (uid, json.dumps(user_info)))
            self.conn.commit()

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.name != after.name:
            await utils.LogUserChange(utils.config, after, f"Username changed from {before.name} to {after.name}")

        if before.roles != after.roles:
            added_roles = [role.name for role in after.roles if role not in before.roles]
            removed_roles = [role.name for role in before.roles if role not in after.roles]
            uid = str(after.id)
            username = after.name
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if user:
                user_info = json.loads(user[1])
                user_info["info"]["roles"] = [role.name for role in after.roles]
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()
            print(f"{Fore.MAGENTA}Updated user ({username} : {uid}) @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}{Style.RESET_ALL}")
            if added_roles:
                await utils.LogUserChange(utils.config, after, f"Roles added: {', '.join([role.name for role in added_roles])}")
                print(f"{Fore.GREEN}Added roles: {', '.join(added_roles)}{Style.RESET_ALL}")
            if removed_roles:
                await utils.LogUserChange(utils.config, after, f"Roles removed: {', '.join([role.name for role in removed_roles])}")
                print(f"{Fore.RED}Removed roles: {', '.join(removed_roles)}{Style.RESET_ALL}")

        if before.premium_since is None and after.premium_since is not None:
            channel_id = self.bot.config["channel_ids"]["ServerAnnocementChannel"]
            channel = self.bot.get_channel(channel_id)
            
            # Use custom emojis if available, otherwise use a default string
            nitroboost_emoji = custom_emojis.get('nitroboost', ':nitroboost:')
            tada_emoji = custom_emojis.get('tada', ':tada:')
            
            embed = discord.Embed(title=f"{nitroboost_emoji} New Server Boost! {nitroboost_emoji}", description=f"{tada_emoji} Thank you {after.mention} for boosting the server! {tada_emoji}", color=discord.Color.purple())
            embed.set_author(name=str(after), icon_url=after.avatar_url)
            await channel.send(embed=embed)

    ## ON_MESSAGES
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user or not isinstance(message.author, discord.Member):
            return

        if os.path.exists('Data/AllowwedLinks.txt'):
            with open('Data/AllowwedLinks.txt', 'r') as file:
                self.AllowedLinks = [line.strip() for line in file.readlines()]
        else:
            self.AllowedLinks = []

        # Extract all URLs from the message content
        urls = re.findall('(http[s]?://|www\.)[^ ]+', message.content)

        # Check for blacklisted words
        for word in self.BadWords:
            if word in message.content.lower():
                if not any(role.name in self.AllowedRoles for role in message.author.roles) and not any(allowed_link in url for allowed_link in self.AllowedLinks for url in urls):
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
        if 'http://' in message.content or 'https://' in message.content or 'www.' in message.content:
            if not any(role.name in self.AllowedRoles for role in message.author.roles):
                if not any(allowed_link in url for allowed_link in self.AllowedLinks for url in urls):
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

        urls = re.findall('(http[s]?://|www\.)[^ ]+', after.content)

        for word in self.BadWords:
            if word in after.content.lower():
                if not any(role.name in self.AllowedRoles for role in after.author.roles) and not any(allowed_link in url for allowed_link in self.AllowedLinks for url in urls):
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

        if 'http://' in after.content or 'https://' in after.content or 'www.' in after.content:
            if not any(role.name in self.AllowedRoles for role in after.author.roles):
                if not any(allowed_link in url for allowed_link in self.AllowedLinks for url in urls):
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
                    reason = f"Message was edited to include banned emoji: `**{emoji}**`\n\n**Original Message Content:** \n```{before.content}```\n\n**Edited Message Content:** \n```{after.content}```\n\n**Channel:** {after.channel.mention}"
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
        OrginalMessage = utils.TruncateText(before.content, 1024)
        EditedMessage = utils.TruncateText(after.content, 1024)

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
        
        # Check if the message is from a DMChannel or TextChannel
        if isinstance(message.channel, discord.DMChannel):
            embed.description = f"Message deleted in DM with {message.author.name}"
        else:
            embed.description = f"Message deleted in {message.channel.mention}"

        # Truncate the message if it's longer than 1024 characters
        if len(message.content) > 1024:
            truncated_message = message.content[:1021] + "..."
        else:
            truncated_message = message.content

        embed.add_field(name="Deleted Message", value=truncated_message, inline=False)
        embed.set_footer(text=f"👤 UID: `{message.author.id}` | 🕒 `{timestamp}`")
        await LoggingChannel.send(embed=embed)

    ## ON_USER
    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url:
            uid = str(after.id)
            username = after.name
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if user:
                user_info = json.loads(user[1])
                old_avatar_url = user_info["info"]["avatar_url"]
                new_avatar_url = str(after.avatar_url)
                user_info["info"]["avatar_url"] = new_avatar_url
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()
                print(f"Updated user ({username} : {uid}) @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")
                # print(f"Updated avatar URL from {old_avatar_url} to {new_avatar_url}")

    ## ON_GUILD
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        ServerLogsChannelID = self.config['channel_ids'].get('ServerLogs', None)

        if ServerLogsChannelID:
            ServerLogsChannel = channel.guild.get_channel(int(ServerLogsChannelID))

            if ServerLogsChannel:
                embed = discord.Embed(
                    title="Text Channel Created",
                    description=f"Name: {channel.name}\nCategory: {channel.category}",
                    color=discord.Color.green(),
                )

                changes = []
                # Add the permission overwrites for each role or user
                for target, overwrite in channel.overwrites.items():
                    target_type = "Role" if isinstance(target, discord.Role) else "User"
                    target_mention = utils.GetMention(target)
                    changes.append(f"{target_type} override for {target_mention}")

                    # Iterate over all permissions
                    for name, value in vars(overwrite).items():
                        if value is not None:
                            emoji = ":white_check_mark:" if value else ":x:"
                            changes.append(f"{name.replace('_', ' ').title()}: {emoji}")

                change_message = "\n".join(changes)
                if change_message:
                    while len(change_message) > 1024:
                        index = change_message.rfind('\n', 0, 1024)
                        embed.add_field(name="**Permission Details**", value=change_message[:index], inline=False)
                        change_message = change_message[index+1:]
                    embed.add_field(name="**Permission Details**", value=change_message, inline=False)

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                embed.set_footer(text=f"Channel ID: {channel.id} • {timestamp}")
                await ServerLogsChannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        ServerLogsChannelID = self.config['channel_ids'].get('ServerLogs', None)

        if ServerLogsChannelID:
            ServerLogsChannel = after.guild.get_channel(int(ServerLogsChannelID))

            if ServerLogsChannel:
                embed = discord.Embed(
                    title="Text Channel Updated",
                    description=f"Overwrites in {after.mention} updated",
                    color=discord.Color.blue(),
                )

                changes = []
                for target, overwrite in after.overwrites.items():
                    if target not in before.overwrites or before.overwrites[target] != overwrite:
                        # Check if the target is a role or a user
                        target_type = "Role" if isinstance(target, discord.Role) else "User"
                        target_mention = utils.get_mention(target)
                        changes.append(f"{target_type} override for {target_mention}")

                        # Iterate over the permissions in the overwrite
                        for perm, value in overwrite:
                            emoji = ":white_check_mark:" if value else ":x:"
                            changes.append(f"{perm.replace('_', ' ').title()}: {emoji}")

                change_message = "\n".join(changes)
                if change_message:
                    while len(change_message) > 1024:
                        index = change_message.rfind('\n', 0, 1024)
                        embed.add_field(name="**Changed Details**", value=change_message[:index], inline=False)
                        change_message = change_message[index+1:]

                    embed.add_field(name="**Changed Details**", value=change_message, inline=False)
                    timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                    embed.set_footer(text=f"Channel ID: {after.id} • {timestamp}")
                    await ServerLogsChannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        ServerLogsChannelID = self.config['channel_ids'].get('ServerLogs', None)

        if ServerLogsChannelID:
            ServerLogsChannel = channel.guild.get_channel(int(ServerLogsChannelID))

            if ServerLogsChannel:
                # Fetch the audit logs
                audit_logs = await channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete).flatten()
                # The user who deleted the channel is the user who triggered the latest 'channel_delete' audit log entry
                deleter = audit_logs[0].user.name if audit_logs else "Unknown"

                embed = discord.Embed(
                    title="Text Channel Deleted",
                    description=f"Name: {channel.name}\n\nCategory: {channel.category}\n\nDeleted by: {deleter}",
                    color=discord.Color.red(),
                )

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                embed.set_footer(text=f"Channel ID: {channel.id} • {timestamp}")
                await ServerLogsChannel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logs(bot))