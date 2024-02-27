import discord
from discord.ext import commands
import utils.utils as utils
from utils.Paginator import Paginator
import json
import asyncio
import sqlite3
from sqlite3 import Error
import random
from typing import Union
from colorama import Fore, Style


with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = self.create_connection('Database/DBInfo.db')
        self.WelcomeChannelID = config.get('channel_ids', {}).get('WelcomeChannel')

    def create_connection(self, database):
        conn = None
        try:
            conn = sqlite3.connect(database)
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
                print(f"{Fore.GREEN}Added roles: {', '.join(added_roles)}{Style.RESET_ALL}")
            if removed_roles:
                print(f"{Fore.RED}Removed roles: {', '.join(removed_roles)}{Style.RESET_ALL}")

    @commands.Cog.listener()
    async def on_message(self, message):
        if isinstance(message.channel, discord.DMChannel):
            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            print(f"{Fore.BLUE}Received DM from {message.author.name} at {timestamp}: {message.content}{Style.RESET_ALL}")
            await utils.LogAction(
                guild=self.bot.get_guild(config['guild_id']),
                channel_name='DMLogs',
                action=f'BOT DM',
                target=message.author,
                reason=f"Message Received from {message.author.name} (UID: {message.author.id}) at {timestamp}\n\n**Message Content:**\n{message.content}.",
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
            old_username = user_info["username"]
            user_info["username"] = new_username
            cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
            self.conn.commit()
            await ctx.send(f"Updated username to {new_username}.")
            print(f"{Fore.YELLOW}Updated username from {old_username} to {new_username} for user {uid} in the database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}{Style.RESET_ALL}")
        else:
            await ctx.send("User not found in the database.")

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
                            "Ban",
                            member,
                            f"User is still banned: {ban_info['reason']}",
                            config=config,
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

    # Good to use if you are using this after already having alot of members in your server
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def addalluserstodb(self, ctx):
        guild = ctx.guild
        cursor = self.conn.cursor()

        added_count = 0

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
                print(f"Added ({member.name} : {uid}) to the database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")
                added_count += 1  # Increment the counter when a user is added

        self.conn.commit()
        await ctx.send(f"Database updated with all server members! {added_count} new users were added.")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def forcesavedb(self, ctx):
        self.conn.commit()
        await ctx.send("Database saved successfully!")
        print(f"Forced saved database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @commands.command(help='<@username or UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def info(self, ctx, user: discord.User):
        uid = user.id
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if user:
            user_info = json.loads(user[1])
            # print(f"User info: {user_info}")
            join_date = user_info["info"]["Joined"] if "Joined" in user_info["info"] else "N/A"
            leave_date = user_info["info"]["Left"] if "Left" in user_info["info"] else "N/A"

            embeds = []
            embed = discord.Embed(
                title=f"User Info for {user_info['info']['username']}",
                color=0x00ff00
            )

            embed.set_thumbnail(url=user_info["info"]["avatar_url"])
            embed.add_field(name="Join Date", value=join_date, inline=True)
            embed.add_field(name="Leave Date", value=leave_date, inline=True)
            roles = ", ".join(user_info["info"]["roles"])
            embed.add_field(name="Roles", value=roles, inline=False)

            if "warns" in user_info["moderation"] and user_info["moderation"]["warns"]:
                total_warnings = len(user_info["moderation"]["warns"])
                embed.add_field(name="Warnings", value=total_warnings, inline=True)
            if "kicks_amount" in user_info["moderation"]:
                total_kicks = user_info["moderation"]["kicks_amount"]
                embed.add_field(name="Kicks", value=total_kicks, inline=True)
            if "notes" in user_info["moderation"] and user_info["moderation"]["notes"]:
                total_notes = len(user_info["moderation"]["notes"])
                embed.add_field(name="Notes", value=total_notes, inline=True)
            if "banned" in user_info and user_info["moderation"]["banned"]:
                embed.add_field(name="Banned", value="Yes", inline=True)
            else:
                embed.add_field(name="Banned", value="No", inline=True)
            embeds.append(embed)

            if "warns" in user_info["moderation"]:
                embed = discord.Embed(title="Warnings:", color=0xff0000)
                for warn in user_info["moderation"]["warns"]:
                    warn_content = f"**Date/Time:** {warn['timestamp']}\n" \
                                f"**Issuer:** {warn['issuer']}\n" \
                                f"**Warning:** {warn['warning']}"
                                # f"Number: {warn['number']}\n" \
                    embed.add_field(name=f"Warning {warn['number']}", value=warn_content, inline=False)
                embeds.append(embed)

            if "notes" in user_info["moderation"]:
                embed = discord.Embed(title="Notes:", color=0x0000ff)
                for note in user_info["moderation"]["notes"]:
                    note_content = f"**Author:** {note['author']}\n" \
                                f"**Content:** {note['content']}"
                                # f"Number: {note['number']}\n" \
                                    # f"Date/Time: {note['timestamp']}\n" \
                    embed.add_field(name=f"Note {note['number']}", value=note_content, inline=False)
                embeds.append(embed)

            if "ban_reason" in user_info["moderation"]:
                embed = discord.Embed(title="Bans:", color=0xff0000)
                for ban in user_info["moderation"]["ban_reason"]:
                    ban_content = f"**Date/Time:** {ban['timestamp']}\n" \
                                f"**Issuer:** {ban['issuer']}\n" \
                                f"**Reason:** {ban['reason']}"
                                # f"Number: {ban['number']}\n" \
                    embed.add_field(name=f"Ban {ban['number']}", value=ban_content, inline=False)
                embeds.append(embed)

            if "kick_reason" in user_info["moderation"]:
                embed = discord.Embed(title="Kicks:", color=0xff0000)
                for kick in user_info["moderation"]["kick_reason"]:
                    kick_content = f"**Date/Time:** {kick['timestamp']}\n" \
                                f"**Issuer:** {kick['issuer']}\n" \
                                f"**Reason:** {kick['reason']}"
                    embed.add_field(name=f"Kick {kick['number']}", value=kick_content, inline=False)
                embeds.append(embed)

            if "banned" in user_info["moderation"]:
                embed = discord.Embed(title="Unbans:", color=0x00ff00)
                for ban in user_info["moderation"]["banned"]:
                    if ban.get("lifted", False):
                        unban_content = f"**Date/Time:** {ban['timestamp']}\n" \
                                        f"**Issuer:** {ban['issuer']}\n" \
                                        f"**Unban Reason:** {ban['unban_reason']}"
                        embed.add_field(name=f"Unban {ban['number']}", value=unban_content, inline=False)
                embeds.append(embed)

            paginator = Paginator(ctx, embeds)
            await paginator.start()
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

    @commands.command(help='<@username or UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addusertodb(self, ctx, user: discord.User):
        uid = user.id
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
        user = cursor.fetchone()
        if not user:
            try:
                member = await utils.GetMember(ctx, uid)
            except ValueError:
                await ctx.send("User not found in the server.")
                return

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
            await utils.LogAction(
                ctx.guild,
                "ModLogs",
                "Database",
                member,
                f"User added to the database by {ctx.author.name}",
                config=config,
            )
        else:
            await ctx.send(f"User with ID {uid} already exists in the database.")
        print(f"Adding ({member.name} : {uid}) to the Database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @commands.command(help='<@username or UID> <Note>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addnote(self, ctx, user: discord.User, *, note_content: str):
        uid = user.id
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_row = cursor.fetchone()
        if not user_row:
            try:
                member = await utils.GetMember(ctx, user.id)
            except ValueError:
                await ctx.send("User not found in the server.")
                return

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
        await ctx.send(f"📝 **Note Added**: {ctx.author.name} added a note for {user.mention} (#{note_number})")
        await utils.LogAction(
            ctx.guild,
            "ModLogs",
            "Note",
            user,
            f"Note added by {ctx.author.name}\n\n Note: {note_content}",
            config=config,
        )

    @commands.command(aliases=["removenote", "delnote"], help='<@username or UID> <Note #>', hidden=True)
    @commands.has_any_role("Admin")
    async def deletenote(self, ctx, user: discord.User, note_number: int):
        uid = user.id
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
                await utils.LogAction(
                    ctx.guild,
                    "ModLogs",
                    "Note",
                    ctx.author,
                    f"**Note Removed**: {ctx.author.name} removed a note for {uid}\n(#{note_number}) - {deleted_content}",
                    config=config,
                )
            else:
                await ctx.send(f"Note #{note_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=['warn'], help='<@username or UID> <Reason>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addwarning(self, ctx, user: discord.User, *, warning: str):
        uid = str(user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_info_db = cursor.fetchone()
        if user_info_db:
            user_info = json.loads(user_info_db[1])
            warnings = user_info["moderation"].get("warns", [])
            warning_number = len(warnings) + 1
            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            author = ctx.author.name

            if "badword" in warning.lower():
                warning += " Your warning contains offensive language."
            elif "spam" in warning.lower():
                warning += " Your warning is related to spamming."
            elif "promoting" in warning.lower():
                warning += " Your warning is related to Promoting other services / Platforms."
            elif "scam" in warning.lower():
                warning += " Your warning is related to Scamming / Phishing."
            elif "harassment" in warning.lower():
                warning += " Your warning is related to harassment of other users."
            elif "doxing" in warning.lower():
                warning += " Your warning is related to sharing private information without consent."
            elif "impersonation" in warning.lower():
                warning += " Your warning is related to impersonating another user or staff."
            elif "disrespect" in warning.lower():
                warning += " Your warning is related to disrespecting other users or staff."
            elif "trolling" in warning.lower():
                warning += " Your warning is related to trolling or disruptive behavior."
            elif "hatespeech" in warning.lower():
                warning += " Your warning is related to using hate speech or discriminatory language."
            elif "inappropriatecontent" in warning.lower():
                warning += " Your warning is related to sharing inappropriate content."
            elif "rulesviolation" in warning.lower():
                warning += " Your warning is related to violating server rules."
            elif "bot abuse" in warning.lower():
                warning += " Your warning is related to abusing bot commands."
            elif "spoilers" in warning.lower():
                warning += " Your warning is related to sharing spoilers without warning."
            elif "misinformation" in warning.lower():
                warning += " Your warning is related to spreading misinformation or false news."
            elif 'offtopic' in warning.lower():
                warning += " Your warning is related to consistently going off-topic in channels."
            elif 'caps' in warning.lower():
                warning += " Your warning is related to excessive use of capital letters (CAPS)."
            elif 'emoji' in warning.lower():
                warning += " Your warning is related to excessive use of emojis."
            elif 'tagging' in warning.lower():
                warning += " Your warning is related to unnecessary tagging of users or roles."
            elif 'language' in warning.lower():
                warning += " Your warning is related to using inappropriate or offensive language."
            elif 'arguing' in warning.lower():
                warning += " Your warning is related to arguing with staff or not following instructions."
            elif 'drama' in warning.lower():
                warning += " Your warning is related to creating or escalating drama."
            elif 'necroposting' in warning.lower():
                warning += " Your warning is related to necroposting or reviving old, inactive threads."
            elif 'inactivity' in warning.lower():
                warning += " Your warning is related to prolonged inactivity."
            elif 'uncooperative' in warning.lower():
                warning += " Your warning is related to being uncooperative with other members or staff."

            new_warning = {
                "number": warning_number,
                "timestamp": timestamp,
                "author": author,
                "warning": warning,
                "issuer": ctx.author.name
            }

            await utils.LogAction(
                ctx.guild,
                "ModLogs",
                "Warning",
                user,
                f"Warning #{warning_number}\n\n**Warning:**\n{warning}",
                issuer=ctx.author,
                config=config,
            )

            # Get the Member object for the user in the guild
            member = ctx.guild.get_member(user.id)

            # Check if this is the 3rd warning
            if warning_number == 3:
                await user.send("You were kicked because of this warning. You can join again right away. Reaching 5 warnings will result in an automatic ban. Permanent invite link: https://discord.gg/SrREp2BbkS.")
                await ctx.guild.kick(member, reason="3rd Warning")
                await ctx.send(f"{user.mention} has been kicked due to their 3rd warning.")
                await utils.LogAction(
                    ctx.guild,
                    "ModLogs",
                    "Kick",
                    user,
                    f"3rd Warning (Warning #{warning_number}): {warning}",
                    issuer=ctx.author,
                    config=config,
                )
                user_info["moderation"]["kicks_amount"] = user_info.get("kicks_amount", 0) + 1

            # Check if this is the 5th warning
            if warning_number == 5:
                ban_info = {
                    "timestamp": timestamp,
                    "issuer": ctx.author,
                    "reason": "Banned due to their 5th warning"
                }

                bans = user_info["moderation"].get("banned", [])
                bans.append(ban_info)
                user_info["moderation"]["banned"] = bans

                await user.send("You have received your 5th warning and have been banned from the server.")
                await ctx.guild.ban(user, reason="5th Warning")
                await ctx.send(f"{user.mention} has been banned due to their 5th warning.")
                await utils.LogAction(
                    ctx.guild,
                    "ModLogs",
                    "Ban",
                    user,
                    f"5th Warning (Warning #{warning_number}): {warning}",
                    issuer=ctx.author,
                    config=config,
                )

            warnings.append(new_warning)
            user_info["moderation"]["warns"] = warnings
            try:
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()
            except Exception as e:
                print(f"Error updating database: {e}")
            await ctx.send(f"⚠️ **Warned**: {ctx.author.mention} warned {user.mention} (warn #{warning_number})\n**Warning Message**:\n{warning}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["delwarning", "removewarning"], help='<@username or UID> <Warning #>', hidden=True)
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
                await utils.LogAction(
                    ctx.guild,
                    "ModLogs",
                    "Warning",
                    user,
                    warning,
                    warning_number,
                    ctx.author,
                    config=config,
                )
            else:
                await ctx.send(f"Warning #{warning_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<@username or UID> <Reason>', hidden=True)
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: Union[discord.Member, discord.User], *, reason: str):
        if isinstance(user, discord.User):
            try:
                user = await utils.FetchMember(ctx.guild, user.id)
            except ValueError:
                await ctx.send("User not found in this server.")
                return

        uid = str(user.id)
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
        user_info_db = cursor.fetchone()
        if user_info_db:
            user_info = json.loads(user_info_db[1])
            user_info["moderation"]["kicks_amount"] = user_info.get("kicks_amount", 0) + 1

            if user_info["moderation"]["kicks_amount"] >= 3:
                await ctx.invoke(self.bot.get_command('ban'), discord_user=user, reason="3rd kick - " + reason)
                return

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
                await user.send(kick_message)
            except discord.Forbidden:
                await ctx.send(f"Failed to send a kick message to {user.mention} due to permission or privacy settings.")
            except Exception as e:
                await ctx.send(f"An error occurred while sending a kick message to {user.mention}: {e}")

            try:
                await user.kick(reason=reason)
                await ctx.send(f"{user.mention} has been kicked for the following reason: {reason}")
                await utils.LogAction(
                    ctx.guild,
                    "ModLogs",
                    "Kick",
                    user,
                    reason,
                    issuer=ctx.author,
                    config=config,
                )
            except discord.Forbidden:
                await ctx.send(f"Failed to kick {user.mention} due to permission settings.")
            except Exception as e:
                await ctx.send(f"An error occurred while kicking {user.mention}: {e}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<@username or UID> <Reason>', hidden=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, discord_user: discord.User, *, reason: str = None):
        uid = str(discord_user.id)
        if reason is None:
            await ctx.send("Please provide a reason for the ban.")
            return

        if 'cheating' in reason:
            reason += " The ban reason involves cheating or exploiting game mechanics."
        elif 'harassment' in reason:
            reason += " The ban reason involves harassment of other members."
        elif 'impersonation' in reason:
            reason += " The ban reason involves impersonating other members or staff."
        elif 'nsfw' in reason:
            reason += " The ban reason involves sharing NSFW content in non-NSFW channels."
        elif 'hatespeech' in reason:
            reason += " The ban reason involves hate speech or discriminatory language."
        elif 'threats' in reason:
            reason += " The ban reason involves threats towards other members or staff."
        elif 'doxing' in reason:
            reason += " The ban reason involves sharing personal information of others without consent."
        elif 'illegal' in reason:
            reason += " The ban reason involves sharing or promoting illegal content."
        elif 'raid' in reason:
            reason += " The ban reason involves participating in or organizing a raid."
        elif 'troll' in reason:
            reason += " The ban reason involves trolling or disruptive behavior."
        elif 'spoilers' in reason:
            reason += " The ban reason involves sharing spoilers without proper warning or in non-designated areas."
        elif 'botting' in reason:
            reason += " The ban reason involves using bots or automated scripts."
        elif 'disrespect' in reason:
            reason += " The ban reason involves disrespect towards other members or staff."
        elif 'inappropriate' in reason:
            reason += " The ban reason involves inappropriate behavior or language."
        elif 'advertising' in reason:
            reason += " The ban reason involves unsolicited advertising or self-promotion."
        elif 'phishing' in reason:
            reason += " The ban reason involves phishing or scam attempts."
        elif 'griefing' in reason:
            reason += " The ban reason involves griefing or ruining the experience for others."
        elif 'stalking' in reason:
            reason += " The ban reason involves stalking or unwanted attention towards other members."
        elif 'spamming' in reason:
            reason += " The ban reason involves excessive spamming or flooding the chat."
        elif 'toxic' in reason:
            reason += " The ban reason involves toxic behavior or creating a hostile environment."
        elif 'solicitation' in reason:
            reason += " The ban reason involves solicitation or asking for goods/services."
        # elif 'leaking' in reason:
        #     reason += " The ban reason involves leaking confidential or proprietary information."
        elif 'exploiting' in reason:
            reason += " The ban reason involves exploiting vulnerabilities or bugs."
        elif 'ddos' in reason:
            reason += " The ban reason involves DDoS attacks or other forms of cyber attacks."
        elif 'invasion' in reason:
            reason += " The ban reason involves invasion of privacy."
        elif 'fraud' in reason:
            reason += " The ban reason involves fraudulent activities."
        elif 'blackmail' in reason:
            reason += " The ban reason involves blackmail or threats to reveal sensitive information."
        elif 'scam' in reason:
            reason += " The ban reason involves scamming or deceptive practices."
        elif 'flaming' in reason:
            reason += " The ban reason involves flaming or instigating arguments."

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

            await utils.LogAction(
                ctx.guild,
                "ModLogs",
                "Ban",
                discord_user,
                reason,
                issuer=ctx.author,
                user_data=user_info,
                config=config,
                embed=embed,
            )
            await ctx.send(f"{user_with_uid} has been banned for the following reason: {reason}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<@username or UID> <Reason>', hidden=True)
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, discord_user: discord.User, *, reason: str = None):
        uid = str(discord_user.id)
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
                    await utils.LogAction(
                        ctx.guild,
                        "ModLogs",
                        "Unban",
                        user,
                        reason,
                        issuer=ctx.author,
                        user_data=user_info,
                        config=config,
                    )
                except discord.errors.NotFound:
                    await ctx.send(f"No ban found for user {user.name} in the Discord server.")
            else:
                await ctx.send(f"No bans found for user {uid} in the database.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<@username or UID>', hidden=True)
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

    @commands.command(help='<@username or UID> <Reason>', hidden=True)
    @commands.has_permissions(ban_members=True)
    async def softban(self, ctx, member: Union[discord.Member, discord.User], *, reason: str):
        if isinstance(member, discord.User):
            try:
                member = await utils.FetchMember(ctx.guild, member.id)
            except ValueError:
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

                await utils.LogAction(
                    ctx.guild,
                    "ModLogs",
                    "SoftBanned",
                    member,
                    reason,
                    issuer=ctx.author,
                    config=config,
                )
                await ctx.send(f"{member.mention} has been soft-banned.")
            except discord.Forbidden:
                await ctx.send("Failed to send a DM to the user or perform the soft ban due to permission settings.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<@username or UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def accountage(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author
        else:
            try:
                member = await utils.GetMember(ctx, member.id)
            except ValueError:
                return await ctx.send("⚠ Unable to get user info as they are not in the server.")

        AccountCreatedDate = member.created_at
        AccountAge = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        if AccountAge < utils.TimeDelta(days=30):
            color = discord.Color.red()  # Red for less than 1 month old
        elif AccountAge < utils.TimeDelta(days=365):
            color = discord.Color.blue()  # Blue for 1 month to 1 year old
        else:
            color = discord.Color.green()  # Green for 1 year or older

        embed = discord.Embed(title=f"{member.name}'s Account Info", color=color)
        embed.add_field(name="Account Creation Date", value=AccountCreatedDate.strftime('%Y-%m-%d'), inline=False)
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(help='<@username or UID> <NewName', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def changenickname(self, ctx, member: discord.Member, *, new_name: str):
        try:
            await member.edit(nick=new_name)
            await ctx.message.reply(f"Nickname changed for {member.mention} to {new_name}.")
        except discord.Forbidden:
            await ctx.message.reply("Failed to change the nickname due to permission settings.")
    
    @commands.command(help="Set the bot's nickname", hidden=True)
    @commands.is_owner()
    async def setbotnickname(self, ctx, *, nickname):
        await ctx.guild.me.edit(nick=nickname)
        await ctx.message.reply(f"Nickname was changed to **{nickname}**")

    @commands.command(help="<@username or UID> <Message>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def dm(self, ctx, user_id: int, *, message: str):
        user = self.bot.get_user(user_id)
        if user is None:
            await ctx.message.reply("User not found.")
            return
        try:
            await user.send(message)
            timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            print(f"At {timestamp} {ctx.author} sent a DM to {user.name}. \nMessage content: '{{{message}}}'")
            await utils.LogAction(
                guild=ctx.guild,
                channel_name='DMLogs',
                action=f'BOT DM',
                target=user,
                reason=f"**Message Sent:**\n{message}",
                issuer=ctx.author,
                config=config
            )
        except discord.Forbidden:
            await ctx.message.reply("I'm not able to DM that user.")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def mergeroles(self, ctx, old_role: discord.Role, new_role: discord.Role):
        try:
            count = 0
            for member in ctx.guild.members:
                if old_role in member.roles:
                    await member.remove_roles(old_role)
                    await member.add_roles(new_role)
                    await asyncio.sleep(1)
                    count += 1
            await ctx.send(f"Roles merged: {old_role.name} -> {new_role.name}. {count} members affected.")
        except Exception as e:
            await ctx.send(f"An error occurred: {e}")

    @commands.command(help='Displays a list of ban reason', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def banshortcuts(self, ctx):
        shortcuts = {
            'cheating': '🎮 The ban reason involves cheating or exploiting game mechanics.',
            'harassment': '👥 The ban reason involves harassment of other members.',
            'impersonation': '🎭 The ban reason involves impersonating other members or staff.',
            'nsfw': '🔞 The ban reason involves sharing NSFW content in non-NSFW channels.',
            'hatespeech': '🚫 The ban reason involves hate speech or discriminatory language.',
            'threats': '⚠️ The ban reason involves threats towards other members or staff.',
            'doxing': '🔒 The ban reason involves sharing personal information of others without consent.',
            'illegal': '⛔ The ban reason involves sharing or promoting illegal content.',
            'raid': '🚷 The ban reason involves participating in or organizing a raid.',
            'troll': '🃏 The ban reason involves trolling or disruptive behavior.',
            'spoilers': '📚 The ban reason involves sharing spoilers without proper warning or in non-designated areas.',
            'botting': '🤖 The ban reason involves using bots or automated scripts.',
            'disrespect': '😡 The ban reason involves disrespect towards other members or staff.',
            'inappropriate': '🙅‍♂️ The ban reason involves inappropriate behavior or language.',
            'advertising': '📣 The ban reason involves unsolicited advertising or self-promotion.',
            'phishing': '🎣 The ban reason involves phishing or scam attempts.',
            'griefing': '😢 The ban reason involves griefing or ruining the experience for others.',
            'stalking': '👀 The ban reason involves stalking or unwanted attention towards other members.',
            'spamming': '🔁 The ban reason involves excessive spamming or flooding the chat.',
            'toxic': '☣️ The ban reason involves toxic behavior or creating a hostile environment.',
            'solicitation': '💰 The ban reason involves solicitation or asking for goods/services.',
            'leaking': '💧 The ban reason involves leaking confidential or proprietary information.',
            'exploiting': '💻 The ban reason involves exploiting vulnerabilities or bugs.',
            'ddos': '🌐 The ban reason involves DDoS attacks or other forms of cyber attacks.',
            'invasion': '🔍 The ban reason involves invasion of privacy.',
            'fraud': '💸 The ban reason involves fraudulent activities.',
            'blackmail': '📧 The ban reason involves blackmail or threats to reveal sensitive information.',
            'scamming': '🎩 The ban reason involves scamming or deceptive practices.',
            'flaming': '🔥 The ban reason involves flaming or instigating arguments.',
        }

        embeds = []
        shortcuts_per_page = 5
        for i in range(0, len(shortcuts), shortcuts_per_page):
            embed = discord.Embed(
                title="🚫 Ban Reason Shortcuts",
                description="Here are the shortcuts you can use when banning a user:",
                color=discord.Color.random()
            )
            for shortcut, description in list(shortcuts.items())[i:i+shortcuts_per_page]:
                embed.add_field(name=shortcut, value=description, inline=False)
                embed.set_footer(text="Use the reactions to navigate through the pages.")
            embeds.append(embed)

        paginator = Paginator(ctx, embeds)
        await paginator.start()

    @commands.command(help='Displays a list of warning reason', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def warningshortcuts(self, ctx):
        shortcuts = {
            'badword': '🔤 Your warning contains offensive language.',
            'spam': '🔁 Your warning is related to spamming.',
            'promoting': '📣 Your warning is related to promoting other services / platforms.',
            'scam': '💰 Your warning is related to scamming / phishing.',
            'harassment': '👥 Your warning is related to harassment of other users.',
            'doxing': '🔒 Your warning is related to sharing private information without consent.',
            'impersonation': '🎭 Your warning is related to impersonating another user or staff.',
            'disrespect': '😡 Your warning is related to disrespecting other users or staff.',
            'trolling': '🃏 Your warning is related to trolling or disruptive behavior.',
            'hatespeech': '🚫 Your warning is related to using hate speech or discriminatory language.',
            'inappropriatecontent': '🔞 Your warning is related to sharing inappropriate content.',
            'rulesviolation': '⚖️ Your warning is related to violating server rules.',
            'bot abuse': '🤖 Your warning is related to abusing bot commands.',
            'spoilers': '📚 Your warning is related to sharing spoilers without warning.',
            'misinformation': '📰 Your warning is related to spreading misinformation or false news.',
            'offtopic': '📌 Your warning is related to consistently going off-topic in channels.',
            'caps': '⬆️ Your warning is related to excessive use of capital letters (CAPS).',
            'emoji': '😀 Your warning is related to excessive use of emojis.',
            'tagging': '🔖 Your warning is related to unnecessary tagging of users or roles.',
            'language': '🗣️ Your warning is related to using inappropriate or offensive language.',
            'arguing': '👣 Your warning is related to arguing with staff or not following instructions.',
            'drama': '🎭 Your warning is related to creating or escalating drama.',
            'necroposting': '⏳ Your warning is related to necroposting or reviving old, inactive threads.',
            'inactivity': '⏲️ Your warning is related to prolonged inactivity.',
            'uncooperative': '👎 Your warning is related to being uncooperative with other members or staff.'
        }

        embeds = []
        shortcuts_per_page = 5
        for i in range(0, len(shortcuts), shortcuts_per_page):
            embed = discord.Embed(
                title="📚 Warning Reason Shortcuts",
                description="Here are the shortcuts you can use when warning a user:",
                color=discord.Color.random()
            )
            for shortcut, description in list(shortcuts.items())[i:i+shortcuts_per_page]:
                embed.add_field(name=shortcut, value=description, inline=False)
                embed.set_footer(text="Use the reactions to navigate through the pages.")
            embeds.append(embed)

        paginator = Paginator(ctx, embeds)
        await paginator.start()




    ## NOT USED ANYMORE DO TO EVERYTHING BEING ADDED TO THE INFO COMMAND
    # @commands.command(help='<@username or UID>', hidden=True)
    # @commands.has_any_role("Helpers", "Moderator", "Admin")
    # async def checkbans(self, ctx, discord_user: discord.User):
    #     uid = str(discord_user.id)
    #     cursor = self.conn.cursor()
    #     cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
    #     user_row = cursor.fetchone()
    #     if user_row:
    #         user_info = json.loads(user_row[1])
    #         bans = user_info["moderation"].get("banned", [])

    #         if bans:
    #             embed = discord.Embed(
    #                 title=f"Bans for {user_info['info']['username']} (UID: {uid})",
    #                 color=0xFF0000,
    #             )

    #             embed.add_field(name="Username", value=user_info["info"]["username"], inline=False)
    #             for index, ban_info in enumerate(bans, start=1):
    #                 timestamp = ban_info["timestamp"]
    #                 issuer = ban_info["issuer"]
    #                 reason = ban_info["reason"]
    #                 unban_reason = ban_info.get("unban_reason", "N/A")
    #                 embed.add_field(
    #                     name=f"Ban #{index}",
    #                     value=f"Date/Time: {timestamp}\nIssuer: {issuer}\nReason: {reason}\nUnban Reason: {unban_reason}",
    #                     inline=False
    #                 )
    #             await ctx.send(embed=embed)
    #         else:
    #             await ctx.send(f"No bans found for user {uid}.")
    #     else:
    #         await ctx.send("User not found in the database.")

    # @commands.command(aliases=["notes", "checknotes"], help='<@username or UID>', hidden=True)
    # @commands.has_any_role("Helper", "Moderator", "Admin")
    # async def listnotes(self, ctx, user: discord.User):
    #     uid = user.id
    #     cursor = self.conn.cursor()
    #     cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
    #     user = cursor.fetchone()
    #     if user:
    #         user_info = json.loads(user[1])
    #         notes = user_info["moderation"].get("notes", [])
    #         if notes:
    #             embed = discord.Embed(
    #                 title=f"Notes for {user_info['info']['username']} (UID: {uid})",
    #                 color=0x00ff00,
    #             )
    #             embed.add_field(name="Username", value=user_info["info"]["username"], inline=False)
    #             for note in notes:
    #                 embed.add_field(
    #                     name=f"Note #{note['number']} - {note['timestamp']} - {note['author']}:",
    #                     value=note['content'],
    #                     inline=False
    #                 )
    #             await ctx.send(embed=embed)
    #         else:
    #             await ctx.send(f"No notes found for user {uid}.")
    #     else:
    #         await ctx.send("User not found in the database.")

    # @commands.command(aliases=["listkicks", "checkkicks"], help='<@username or UID>', hidden=True)
    # @commands.has_any_role("Helper", "Moderator", "Admin")
    # async def listkickreasons(self, ctx, user: discord.User):
    #     uid = str(user.id)
    #     cursor = self.conn.cursor()
    #     cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
    #     user = cursor.fetchone()
    #     if user:
    #         user_info = json.loads(user[1])
    #         kicks = user_info.get("kick_reason", [])

    #         if kicks:
    #             embed = discord.Embed(
    #                 title=f"Kick Reasons for {user_info['username']} (UID: {uid})",
    #                 color=0x00ff00,
    #             )
    #             embed.add_field(name="Username", value=user_info["username"], inline=False)
    #             for kick in kicks:
    #                 embed.add_field(
    #                     name=f"Kick #{kick['number']} - {kick['timestamp']} - {kick['issuer']}:",
    #                     value=kick['reason'],
    #                     inline=False
    #                 )
    #             await ctx.send(embed=embed)
    #         else:
    #             await ctx.send(f"No kick reasons found for user {uid}.")
    #     else:
    #         await ctx.send("User not found in the database.")

    # @commands.command(aliases=["listwarnings", "listwarns"], help='<@username or UID> <Warning #>', hidden=True)
    # @commands.has_any_role("Helper", "Moderator", "Admin")
    # async def checkwarnings(self, ctx, user: discord.User, warning_number: Union[int, None]):
    #     uid = str(user.id)
    #     if warning_number is None:
    #         await ctx.send("Please provide a warning number after the user ID.")
    #         return

    #     uid = str(user.id)
    #     cursor = self.conn.cursor()
    #     cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (uid,))
    #     user = cursor.fetchone()
    #     if user:
    #         user_info = json.loads(user[1])
    #         warnings = user_info.get("warns", [])

    #         found_warning = None
    #         for warning in warnings:
    #             if warning.get("number") == warning_number:
    #                 found_warning = warning
    #                 break
    #         if found_warning:
    #             timestamp = found_warning.get("timestamp", "N/A")
    #             issuer = found_warning.get("issuer", "N/A")
    #             warning_text = found_warning.get("warning", "N/A")
    #             await ctx.send(f"**Warning #{warning_number} for {user.mention}:**\n"
    #                         f"Time: {timestamp}\n"
    #                         f"Issuer: {issuer}\n"
    #                         f"Warning: {warning_text}")
    #         else:
    #             await ctx.send(f"Warning #{warning_number} not found for this user.")
    #     else:
    #         await ctx.send("User not found in the database.")

def setup(bot):
    bot.add_cog(Moderation(bot))
