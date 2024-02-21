import asyncio
import datetime
from datetime import datetime, timedelta
import discord
from discord.ext import commands
import random
import json
import utils
from typing import Union
import sqlite3
from sqlite3 import Error

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class Moderation(commands.Cog):
    hidden = True

    def __init__(self, bot):
        self.bot = bot
        self.database_file = 'Database/DBInfo.db'
        self.conn = self.create_connection(self.database_file)
        self.WelcomeChannelID = config.get('channel_ids', {}).get('WelcomeChannel')

    def create_connection(self, db_file):
        conn = None
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS UserInfo (
                    uid TEXT PRIMARY KEY,
                    info TEXT NOT NULL
                );
            """)
            return conn
        except Error as e:
            print(e)

        return conn

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
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
            print(f"Updated user {username} : {uid} @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel):
            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            print(f"Received DM from {message.author.name} at {timestamp}: {message.content}")
            await utils.LogAction(
                guild=self.bot.get_guild(config['guild_id']),
                channel_name='DMLogs',
                action='BOT DM',
                target=f"{message.author}\n(UID: {message.author.id})",
                reason=f"Received DM at {timestamp}\n\n**DM Message:**\n\n{message.content}",
                config=config
            )
        elif not message.author.bot:
            uid = str(message.author.id)
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if user:
                user_info = json.loads(user[1])
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()

    @commands.command(help='<username> or <UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateuser(self, ctx, new_username: str):
        uid = str(ctx.author.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            user_info["username"] = new_username
            cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            self.conn.commit()
            await ctx.send(f"Updated username to {new_username}.")
        else:
            await ctx.send("User not found in the database.")
        print(f"Updated {new_username} : {uid} to the database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url:
            # If the user's avatar URL has changed
            uid = str(after.id)
            username = after.name
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if user:
                user_info = json.loads(user[1])
                user_info["info"]["avatar_url"] = str(after.avatar_url)
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()
            print(f"Updated user ({username} : {uid}) @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

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
                if not member.bot:
                    user_info["info"]["roles"] = [role.name for role in member.roles]
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (uid, json.dumps(user_info)))
                print(f"Added new user ({member.name} : {uid}) to the database  @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")
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
                        await utils.LogAction(server, 'ModLogs', 'Ban', member, f"User is still banned: {ban_info['reason']}", config=config)

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
            if user:
                user_info = json.loads(user[1])
                user_info["info"]["Left"] = datetime.now().strftime('%m-%d-%y %H:%M')
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
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (uid, json.dumps(user_info)))
            self.conn.commit()

    # Good to use if you are using this after already having alot of members in your server
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def addalluserstodb(self, ctx):
        guild = ctx.guild
        cursor = self.conn.cursor()

        for member in guild.members:
            uid = str(member.id)
            cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
            user = cursor.fetchone()
            if not user:
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
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (uid, json.dumps(user_info)))
            print(f"Adding ({member.name} : {uid}) to the database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

        self.conn.commit()
        await ctx.send("Database updated with all server members!")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def forcesavedb(self, ctx):
        self.conn.commit()
        await ctx.send("Database saved successfully!")
        print(f"Forced saved database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def info(self, ctx, uid: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            join_date = user_info["info"]["Joined"] if "Joined" in user_info["info"] else "N/A"
            leave_date = user_info["info"]["Left"] if "Left" in user_info["info"] else "N/A"

            embed = discord.Embed(
                title=f"User Info for {user_info['info']['username']}",
                color=0x00ff00
            )

            embed.set_thumbnail(url=user_info["info"]["avatar_url"])

            embed.add_field(name="Join Date", value=join_date, inline=True)
            embed.add_field(name="Leave Date", value=leave_date, inline=True)

            roles = ", ".join(user_info["info"]["roles"])
            embed.add_field(name="Roles", value=roles, inline=False)

            if "warns" in user_info and user_info["moderation"]["warns"]:
                total_warnings = len(user_info["moderation"]["warns"])
                embed.add_field(name="Warnings", value=total_warnings, inline=True)

            if "kicks_amount" in user_info:
                total_kicks = user_info["moderation"]["kicks_amount"]
                embed.add_field(name="Kicks", value=total_kicks, inline=True)

            if "notes" in user_info["moderation"] and user_info["moderation"]["notes"]:
                total_notes = len(user_info["moderation"]["notes"])
                embed.add_field(name="Notes", value=total_notes, inline=True)
                
            if "banned" in user_info and user_info["moderation"]["banned"]:
                embed.add_field(name="Banned", value="Yes", inline=True)
            else:
                embed.add_field(name="Banned", value="No", inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<user_id> <key> <value>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateinfo(self, ctx, uid: int, key: str, *, value: str):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            if key in user_info:
                user_info[key] = value
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), str(uid)))
                self.conn.commit()
                await ctx.send(f"Updated {key} for user {uid} to {value}.")
            else:
                await ctx.send("Key does not exist.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addusertodb(self, ctx, uid: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if not user:
            member = ctx.guild.get_member(uid)
            if member:
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
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (str(uid), json.dumps(user_info)))
                self.conn.commit()
                await ctx.send(f"User with ID `{uid}` (username: `{member.name}`) added to the database.")
                await utils.LogAction(ctx.guild, 'ModLogs', 'Database', member, f"User added to the database by {ctx.author.name}", config=config)
            else:
                await ctx.send("User not found in the server.")
        else:
            await ctx.send(f"User with ID {uid} already exists in the database.")
        print(f"Adding ({member.name} : {uid}) to the Database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @commands.command(help='<UID> <Note>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addnote(self, ctx, discord_user: discord.User, *, note_content: str):
        uid = str(discord_user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_row = cursor.fetchone()
        if not user_row:
            member = ctx.guild.get_member(discord_user.id)
            if member:
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
                cursor.execute("INSERT INTO UserInfo VALUES (?, ?)", (uid, json.dumps(user_info)))
                self.conn.commit()
            else:
                await ctx.send("User not found in the server.")
                return

        user_info = json.loads(user_row[1])
        notes = user_info["moderation"]["notes"]
        timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        note_number = 1
        for note in notes:
            if note.get("number"):
                note_number = note["number"] + 1

        notes.append({
            "number": note_number,
            "timestamp": timestamp,
            "author": ctx.author.name,
            "content": note_content
        })

        cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
        self.conn.commit()
        await ctx.send(f"📝 **Note Added**: {ctx.author.name} added a note for {discord_user.mention} (#{note_number})")
        await utils.LogAction(ctx.guild, 'ModLogs', 'Note', discord_user, f"Note added by {ctx.author.name}\n\n Note: {note_content}", config=config)

    @commands.command(aliases=["removenote", "delnote"], help='<UID> <Note #>', hidden=True)
    @commands.has_any_role("Admin")
    async def deletenote(self, ctx, uid: int, note_number: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            notes = user_info["moderation"]["notes"]

            found_note = None
            for note in notes:
                if note.get("number") == note_number:
                    found_note = note
                    break

            if found_note:
                deleted_content = found_note.get("content", "")
                notes.remove(found_note)
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), str(uid)))
                self.conn.commit()
                await ctx.send(f"🗑 **Note Removed**: {ctx.author.name} removed a note for {uid}\n(#{note_number}) - {deleted_content}")
                await utils.LogAction(ctx.guild, 'ModLogs', 'Note', ctx.author, f"**Note Removed**: {ctx.author.name} removed a note for {uid}\n(#{note_number}) - {deleted_content}", config=config)
            else:
                await ctx.send(f"Note #{note_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["notes", "checknotes"], help='<UID>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def listnotes(self, ctx, uid: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            notes = user_info["moderation"].get("notes", [])

            if notes:
                embed = discord.Embed(
                    title=f"Notes for {user_info['info']['username']} (UID: {uid})",
                    color=0x00ff00,
                )

                embed.add_field(name="Username", value=user_info["info"]["username"], inline=False)

                for note in notes:
                    embed.add_field(
                        name=f"Note #{note['number']} - {note['timestamp']} - {note['author']}:",
                        value=note['content'],
                        inline=False
                    )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No notes found for user {uid}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=['warn'], help='<UID> <Reason>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addwarning(self, ctx, member: discord.Member, *, warning: str):
        uid = str(member.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            warnings = user_info.get("warns", [])
            warning_number = len(warnings) + 1
            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            author = ctx.author.name

            # Customize the message based on other conditions, for example:
            if "badword" in warning.lower():
                warning += " Your warning contains offensive language."
            elif "spam" in warning.lower():
                warning += " Your warning is related to spamming."
            elif "promoting" in warning.lower():
                warning += " Your warning is related to Promoting other services / Platforms."

            new_warning = {
                "number": warning_number,
                "timestamp": timestamp,
                "author": author,
                "warning": warning,
                "issuer": ctx.author.name
            }

            warnings.append(new_warning)

            await utils.LogAction(ctx.guild, 'ModLogs', 'Warning', member, warning, warning_number, ctx.author.name, config=config)

            # Check if this is the 3rd warning
            if warning_number == 3:

                await member.send("You were kicked because of this warning. You can join again right away. Reaching 5 warnings will result in an automatic ban. Permanent invite link: https://discord.gg/SrREp2BbkS.")
                await member.kick(reason="3rd Warning")
                await ctx.send(f"{member.mention} has been kicked due to their 3rd warning.")
                await utils.LogAction(ctx.guild, 'ModLogs', 'Kick', member, f"3rd Warning: {warning}", warning_number, ctx.author.name, config=config)

                user_info["moderation"]["kicks_amount"] = user_info.get("kicks_amount", 0) + 1

            # Check if this is the 5th warning
            if warning_number == 5:
                
                ban_info = {
                    "timestamp": timestamp,
                    "issuer": ctx.author.name,
                    "reason": "Banned due to their 5th warning"
                }

                bans = user_info["moderation"].get("banned", [])
                bans.append(ban_info)
                user_info["moderation"]["banned"] = bans

                await member.send("You have received your 5th warning and have been banned from the server.")
                await ctx.guild.ban(member, reason="5th Warning")
                await ctx.send(f"{member.mention} has been banned due to their 5th warning.")

                await utils.LogAction(ctx.guild, 'ModLogs', 'Ban', member, f"5th Warning: {warning}", warning_number, ctx.author.name, config=config)

            user_info["moderation"]["warns"] = warnings

            cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            self.conn.commit()
            await ctx.send(f"⚠️ **Warned**: {ctx.author.mention} warned {member.mention} (warn #{warning_number})\n**Warning Message**:\n{warning}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["listwarnings", "listwarns"], help='<UID> <Warning #>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def checkwarnings(self, ctx, user: discord.User, warning_number: Union[int, None]):
        if warning_number is None:
            await ctx.send("Please provide a warning number after the user ID.")
            return

        uid = str(user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            warnings = user_info.get("warns", [])

            found_warning = None
            for warning in warnings:
                if warning.get("number") == warning_number:
                    found_warning = warning
                    break

            if found_warning:
                timestamp = found_warning.get("timestamp", "N/A")
                issuer = found_warning.get("issuer", "N/A")
                warning_text = found_warning.get("warning", "N/A")

                await ctx.send(f"**Warning #{warning_number} for {user.mention}:**\n"
                            f"Time: {timestamp}\n"
                            f"Issuer: {issuer}\n"
                            f"Warning: {warning_text}")
            else:
                await ctx.send(f"Warning #{warning_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["delwarning", "removewarning"], help='<UID> <Warning #>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletewarning(self, ctx, user: discord.User, warning_number: int):
        uid = str(user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            warnings = user_info.get("warns", [])

            found_warning = None
            for warning in warnings:
                if warning.get("number") == warning_number:
                    found_warning = warning
                    break

            if found_warning:
                deleted_content = found_warning.get("warning", "")
                warnings.remove(found_warning)
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()
                await ctx.send(f"Deleted warning #{warning_number} for {user.mention}: {deleted_content}")

                await utils.LogAction(ctx.guild, 'ModLogs', 'Warning', user, warning, warning_number, ctx.author, config=config)
            else:
                await ctx.send(f"Warning #{warning_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <Reason>')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Union[discord.Member, int], *, reason: str):
        if isinstance(member, int):
            try:
                member = await ctx.guild.fetch_member(member)
            except discord.NotFound:
                await ctx.send("User not found in this server.")
                return

        uid = str(member.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            user_info["moderation"]["kicks_amount"] = user_info.get("kicks_amount", 0) + 1

            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')

            kick_info = {
                "number": 1,
                "timestamp": timestamp,
                "issuer": ctx.author.name,
                "reason": reason
            }

            kicks = user_info.get("kick_reason", [])
            existing_numbers = [kick.get("number", 0) for kick in kicks]
            if existing_numbers:
                kick_info["number"] = max(existing_numbers) + 1

            kicks.append(kick_info)
            user_info["moderation"]["kick_reason"] = kicks

            cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            self.conn.commit()

            try:
                kick_message = f"You are about to be kicked from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou may join back but please learn from your mistakes. Permanent invite link: https://discord.gg/SrREp2BbkS"
                await member.send(kick_message)
            except discord.Forbidden:
                await ctx.send(f"Failed to send a kick message to {member.mention} due to permission or privacy settings.")
            except Exception as e:
                await ctx.send(f"An error occurred while sending a kick message to {member.mention}: {e}")

            try:
                await member.kick(reason=reason)
                await ctx.send(f"{member.mention} has been kicked for the following reason: {reason}")
                await utils.LogAction(ctx.guild, 'ModLogs', 'Kick', member, reason, issuer=ctx.author, config=config)
            except discord.Forbidden:
                await ctx.send(f"Failed to kick {member.mention} due to permission settings.")
            except Exception as e:
                await ctx.send(f"An error occurred while kicking {member.mention}: {e}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["listkicks", "checkkicks"], help='<UID>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def listkickreasons(self, ctx, uid: int):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            kicks = user_info.get("kick_reason", [])

            if kicks:
                embed = discord.Embed(
                    title=f"Kick Reasons for {user_info['username']} (UID: {uid})",
                    color=0x00ff00,
                )

                embed.add_field(name="Username", value=user_info["username"], inline=False)

                for kick in kicks:
                    embed.add_field(
                        name=f"Kick #{kick['number']} - {kick['timestamp']} - {kick['issuer']}:",
                        value=kick['reason'],
                        inline=False
                    )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No kick reasons found for user {uid}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <Reason>')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, discord_user: discord.User, *, reason: str = None):
        if reason is None:
            await ctx.send("Please provide a reason for the ban.")
            return

        uid = str(discord_user.id)
        user_with_uid = f"{discord_user.name} - UID: {uid}"
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_row = cursor.fetchone()
        if user_row:
            user_info = json.loads(user_row[1])
            try:
                ban_message = f"You have been banned from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou can appeal this ban by creating a ticket in the ban appeal discord server. Permanent invite link: https://discord.gg/CBuJgaWkrr"
                await discord_user.send(ban_message)
            except discord.Forbidden:
                await ctx.send(f"Failed to send a ban message to {user_with_uid} due to permission or privacy settings.")
                return
            except Exception as e:
                await ctx.send(f"An error occurred while sending a ban message to {user_with_uid}: {e}")
                return

            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')

            ban_info = {
                "timestamp": timestamp,
                "issuer": ctx.author.name,
                "reason": reason
            }

            bans = user_info["moderation"].get("banned", [])
            bans.append(ban_info)
            user_info["moderation"]["banned"] = bans

            cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            self.conn.commit()

            await ctx.guild.ban(discord_user, reason=reason)

            embed = discord.Embed(
                title="Ban",
                color=discord.Color.red(),
            )
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="User", value=user_with_uid, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Time", value=timestamp, inline=True)

            await utils.LogAction(ctx.guild, 'ModLogs', 'Ban', discord_user, reason, issuer=ctx.author, user_data=user_info, config=config, embed=embed)

            await ctx.send(f"{user_with_uid} has been banned for the following reason: {reason}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <Reason>')
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, discord_user: discord.Object, *, reason: str = None):
        try:
            user = await self.bot.fetch_user(discord_user.id)
        except discord.NotFound:
            await ctx.send(f"No user found with ID {discord_user.id}.")
            return
        if reason is None:
            await ctx.send("Please provide a reason for the unban.")
            return

        uid = str(discord_user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_row = cursor.fetchone()
        if user_row:
            user_info = json.loads(user_row[1])
            bans = user_info["moderation"].get("banned", [])
            if bans:
                LastBan = bans[-1]
                LastBan["unban_reason"] = reason
                LastBan["lifted"] = True

                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()

                try:
                    await ctx.guild.unban(discord_user, reason=reason)
                    await ctx.send(f"{user.name} has been unbanned for the following reason: {reason}")

                    await utils.LogAction(ctx.guild, 'ModLogs', 'Unban', user, reason, issuer=ctx.author, user_data=user_info, config=config)

                except discord.errors.NotFound:
                    await ctx.send(f"No ban found for user {user.name} in the Discord server.")
            else:
                await ctx.send(f"No bans found for user {uid} in the database.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Helpers", "Moderator", "Admin")
    async def checkbans(self, ctx, discord_user: discord.User):
        uid = str(discord_user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_row = cursor.fetchone()
        if user_row:
            user_info = json.loads(user_row[1])
            bans = user_info["moderation"].get("banned", [])

            if bans:
                embed = discord.Embed(
                    title=f"Bans for {user_info['info']['username']} (UID: {uid})",
                    color=0xFF0000,
                )

                embed.add_field(name="Username", value=user_info["info"]["username"], inline=False)

                for index, ban_info in enumerate(bans, start=1):
                    timestamp = ban_info["timestamp"]
                    issuer = ban_info["issuer"]
                    reason = ban_info["reason"]
                    unban_reason = ban_info.get("unban_reason", "N/A")

                    embed.add_field(
                        name=f"Ban #{index}",
                        value=f"Date/Time: {timestamp}\nIssuer: {issuer}\nReason: {reason}\nUnban Reason: {unban_reason}",
                        inline=False
                    )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No bans found for user {uid}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID>', hidden=True)
    @commands.has_permissions(ban_members=True)
    async def deleteban(self, ctx, discord_user: discord.User):
        uid = str(discord_user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_row = cursor.fetchone()
        if user_row:
            user_info = json.loads(user_row[1])
            user_info["moderation"]["banned"] = []

            cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            self.conn.commit()

            await ctx.send(f"Ban data for user {discord_user.name} has been deleted.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <Reason>', hidden=True)
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: Union[discord.Member, int], *, reason: str):
        if isinstance(member, int):
            try:
                member = await ctx.guild.fetch_member(member)
            except discord.NotFound:
                await ctx.send("User not found in this server.")
                return

        uid = str(member.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])

            try:
                ban_message = f"You have been Soft-Banned from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou may join back but please learn from your mistakes. Permanent invite link: https://discord.gg/SrREp2BbkS"
                await member.send(ban_message)
                await member.ban(reason=reason)
                await asyncio.sleep(2)
                await member.unban(reason="Soft ban")

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')

                ban_info = {
                    "timestamp": timestamp,
                    "issuer": ctx.author.name,
                    "reason": reason
                }

                user_info["moderation"].setdefault("banned", []).append(ban_info)

                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()

                await utils.LogAction(ctx.guild, 'ModLogs', 'SoftBanned', member, reason, issuer=ctx.author, config=config)

                await ctx.send(f"{member.mention} has been soft-banned.")
            except discord.Forbidden:
                await ctx.send("Failed to send a DM to the user or perform the soft ban due to permission settings.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def accountage(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        elif not ctx.guild.get_member(member.id):
            return await ctx.send("⚠ Unable to get user info as they are not in the server.")

        AccountCreatedDate = member.created_at
        AccountAge = datetime.utcnow() - AccountCreatedDate

        if AccountAge < timedelta(days=30):
            color = discord.Color.red()  # Red for less than 1 month old
        elif AccountAge < timedelta(days=365):
            color = discord.Color.blue()  # Blue for 1 month to 1 year old
        else:
            color = discord.Color.green()  # Green for 1 year or older

        embed = discord.Embed(title=f"{member.name}'s Account Info", color=color)
        embed.add_field(name="Account Creation Date", value=AccountCreatedDate.strftime('%Y-%m-%d'), inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(help='<UID> <NewName', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def changenickname(self, ctx, member: discord.Member, *, new_name: str):
        try:
            await member.edit(nick=new_name)
            await ctx.send(f"Nickname changed for {member.mention} to {new_name}.")
        except discord.Forbidden:
            await ctx.send("Failed to change the nickname due to permission settings.")

    @commands.command(help="<uid> <Message>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def dm(self, ctx, user_id: int, *, message: str):
        user = self.bot.get_user(user_id)
        if user is None:
            await ctx.send("User not found.")
            return
        try:
            await user.send(message)
            await ctx.send(f"Message sent to {user.name}. Message content: `{message}`")
        except discord.Forbidden:
            await ctx.send("I'm not able to DM that user.")

    @commands.command(help="<uid> <Message>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def dm(self, ctx, user_id: int, *, message: str):
        user = self.bot.get_user(user_id)
        if user is None:
            await ctx.send("User not found.")
            return
        try:
            await user.send(message)
            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            print(f"At {timestamp} {ctx.author} sent a DM to {user.name}. \nMessage content: '{{{message}}}'")
            await utils.LogAction(
                guild=ctx.guild,
                channel_name='ModLogs',
                action='BOT DM',
                target=user,
                reason=f"**DM Message:**\n\n{message}",
                issuer=ctx.author,
                config=config
            )
        except discord.Forbidden:
            await ctx.send("I'm not able to DM that user.")

def setup(bot):
    bot.add_cog(Moderation(bot))