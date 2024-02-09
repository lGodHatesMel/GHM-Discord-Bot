import asyncio
import datetime
import os
import discord
from discord.ext import commands
import random
import json
import utils
from typing import Union

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class WelcomeMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'DBInfo.json')
        self.user_info = self.load_user_info()
        self.welcome_channel_id = None

    def load_user_info(self):
        if not os.path.exists(self.database_folder):
            os.makedirs(self.database_folder)

        if not os.path.exists(self.database_file):
            self.user_info = {}
        else:
            try:
                with open(self.database_file, 'r') as f:
                    self.user_info = json.load(f)
            except json.JSONDecodeError:
                # Handle JSON decoding error (e.g., if the file is empty or corrupted)
                self.user_info = {}

        return self.user_info

    def save_user_info(self):
        import json
        import datetime

        # Filter out users with empty data before saving to the database
        filtered_user_info = {uid: data for uid, data in self.user_info.items() if data["info"]}

        with open(self.database_file, 'w') as f:
            json.dump(
                filtered_user_info,
                f,
                indent=4,
                default=lambda o: o.isoformat() if isinstance(o, datetime.datetime) else None,
            )
            print("User info saved successfully.")

    async def get_welcome_channel_id(self):
        with open('config.json', 'r') as config_file:
            config_data = json.load(config_file)
        return config_data.get('welcome_channel_id')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.roles != after.roles:
            # If the roles of a member have changed
            uid = str(after.id)

            # Check if the user exists in the database
            if uid in self.user_info:
                # Update the user's roles in the database
                self.user_info[uid]["info"]["roles"] = [role.name for role in after.roles]
                self.save_user_info()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            uid = str(message.author.id)
            
            if uid in self.user_info:
                self.user_info[uid]["info"]["total_messages"] += 1
                self.save_user_info()

    @commands.command(help='Replies with Pong if bot is up', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def ping(self, ctx):
        await ctx.send('Pong')

    @commands.command(help='<username> or <UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateuser(self, ctx, new_username: str):
        uid = str(ctx.author.id)
        if uid in self.user_info:
            self.user_info[uid]["info"]["username"] = new_username
            self.save_user_info()
            await ctx.send(f"Updated username to {new_username}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url:
            # If the user's avatar URL has changed
            uid = str(after.id)
            # Check if the user exists in the database
            if uid in self.user_info:
                # Update the user's avatar URL in the database
                self.user_info[uid]["info"]["avatar_url"] = str(after.avatar_url)
                self.save_user_info()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f"DEBUG: on_member_join event triggered for {member.name} ({member.id})")

        self.welcome_channel_id = await self.get_welcome_channel_id()

        if self.welcome_channel_id:
            channel = self.bot.get_channel(self.welcome_channel_id)
            if channel:
                server = member.guild
                member_count = sum(1 for member in server.members if not member.bot)
                member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"
                random_color = random.randint(0, 0xFFFFFF)

                welcome = {
                    "title": "Welcome!",
                    "description": f"Welcome to GodHatesMe Pokemon Centre {member.mention}, you are our {member_number}!\n\n"
                                f"Don't forget to read <#956760032232484884> and to get your Roles go to <#956769501607755806>!",
                    "color": random_color,
                }

                embed = discord.Embed(**welcome)
                embed.set_thumbnail(url=member.avatar_url)
                embed.set_footer(text=member.name)

                await channel.send(embed=embed)
                print(f"{member.name} joined the server as the {member_number}.")

                uid = str(member.id)

                # Check if the user already exists in the database
                if uid in self.user_info:
                    # Update the "Left" field to None when a user rejoins
                    self.user_info[uid]["info"]["Left"] = None
                else:
                    # If the user doesn't exist, create a new entry in the database
                    self.user_info[uid] = {
                        "info": {
                            "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                            "Account_Created": member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            "Left": None,
                            "username": member.name,
                            "roles": [role.name for role in member.roles],
                            "total_messages": 0,
                            "warns": [],
                            "notes": [],
                            "banned": [],
                            "kick_reason": [],
                            "kicks_amount": 0,
                            "avatar_url": str(member.avatar_url),
                        },
                        # "coindata": {
                        #     "right_count": 0, 
                        #     "wrong_count": 0, 
                        #     "total_coins": 0
                        # }
                    }
                self.save_user_info()

                if uid in self.user_info and self.user_info[uid]["info"]["banned"]:
                    for ban_info in self.user_info[uid]["info"]["banned"]:
                        if ban_info.get("lifted") is None:
                            await utils.LogModAction(server, 'Ban', member, f"User is still banned: {ban_info['reason']}", config=config)

    # Good to use if you are using this after already having alot of members in your server
    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def addalltodb(self, ctx):
        guild = ctx.guild

        for member in guild.members:
            uid = str(member.id)

            # Check if the user already exists in the database
            if uid not in self.user_info:
                # If the user doesn't exist, create a new entry in the database
                self.user_info[uid] = {
                    "info": {
                        "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Account_Created": member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "warns": [],
                        "notes": [],
                        "banned": [],
                        "kick_reason": [],
                        "kicks_amount": 0,
                        "avatar_url": str(member.avatar_url),
                    },
                    # "coindata": {"right_count": 0, "wrong_count": 0, "total_coins": 0},
                }

        self.save_user_info()

        await ctx.send("Database updated with all server members!")
    
    @commands.Cog.listener()
    async def on_member_remove(self, member):
        print(f"DEBUG: on_member_remove event triggered for {member.name} ({member.id})")

        self.goodbye_channel_id = await self.get_goodbye_channel_id()

        if self.goodbye_channel_id:
            channel = self.bot.get_channel(self.goodbye_channel_id)
            if channel:
                server = member.guild
                member_count = sum(1 for member in server.members if not member.bot)
                member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"
                random_color = random.randint(0, 0xFFFFFF)

                goodbye = {
                    "title": "Goodbye!",
                    "description": f"We are sad to see you go, {member.mention}. You were our {member_number}.\n\n"
                                f"We hope you enjoyed your stay at GodHatesMe Pokemon Centre!",
                    "color": random_color,
                }

                embed = discord.Embed(**goodbye)
                embed.set_thumbnail(url=member.avatar_url)
                embed.set_footer(text=member.name)

                await channel.send(embed=embed)
                print(f"{member.name} left the server as the {member_number}.")

                uid = str(member.id)

                # Check if the user exists in the database
                if uid in self.user_info:
                    self.user_info[uid]["info"]["Left"] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                else:
                    # If the user doesn't exist, create a new entry in the database
                    self.user_info[uid] = {
                        "info": {
                            "Joined": None,
                            "Account_Created": member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                            "Left": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            "username": member.name,
                            "roles": [role.name for role in member.roles],
                            "total_messages": 0,
                            "warns": [],
                            "notes": [],
                            "banned": [],
                            "kick_reason": [],
                            "kicks_amount": 0,
                            "avatar_url": str(member.avatar_url),
                        }
                    }
                self.save_user_info()

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)  # Only allow administrators to use this command
    async def forcesavedb(self, ctx):
        # Replace the following line with the actual logic to save your database
        # For example, if your save function is self.save_user_info(), call it here
        self.save_user_info()

        await ctx.send("Database saved successfully!")

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        leave_time = utils.GetLocalTime()
        leave_time_str = leave_time.strftime('%Y-%m-%d %H:%M:%S')

        uid = str(member.id)
        if uid in self.user_info:
            self.user_info[uid]["info"]["Left"] = leave_time_str
            self.save_user_info()

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def info(self, ctx, uid: int):
        if str(uid) in self.user_info:
            user_data = self.user_info[str(uid)]
            join_date = user_data["info"]["Joined"]
            leave_date = user_data["info"]["Left"] if "Left" in user_data["info"] else "N/A"

            embed = discord.Embed(
                title=f"User Info for {user_data['info']['username']}",
                color=0x00ff00
            )

            embed.set_thumbnail(url=user_data["info"]["avatar_url"])

            embed.add_field(name="Join Date", value=join_date, inline=True)
            embed.add_field(name="Leave Date", value=leave_date, inline=True)

            roles = ", ".join(user_data["info"]["roles"])
            embed.add_field(name="Roles", value=roles, inline=False)

            total_messages = user_data["info"]["total_messages"]
            embed.add_field(name="Total Messages", value=total_messages, inline=True)

            if "warns" in user_data["info"] and user_data["info"]["warns"]:
                total_warnings = len(user_data["info"]["warns"])
                embed.add_field(name="Warnings", value=total_warnings, inline=True)

            if "kicks_amount" in user_data["info"]:
                total_kicks = user_data["info"]["kicks_amount"]
                embed.add_field(name="Kicks", value=total_kicks, inline=True)

            if "notes" in user_data["info"] and user_data["info"]["notes"]:
                total_notes = len(user_data["info"]["notes"])
                embed.add_field(name="Notes", value=total_notes, inline=True)
                
            if "banned" in user_data["info"] and user_data["info"]["banned"]:
                embed.add_field(name="Banned", value="Yes", inline=True)
            else:
                embed.add_field(name="Banned", value="No", inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<user_id> <key> <value>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateinfo(self, ctx, uid: int, key: str, *, value: str):
        # Update user information (for testing purposes)
        if str(uid) in self.user_info and key in self.user_info[str(uid)]["info"]:
            self.user_info[str(uid)]["info"][key] = value
            self.save_user_info()
            await ctx.send(f"Updated {key} for user {uid} to {value}.")
        else:
            await ctx.send("User not found in the database or key does not exist.")

    @commands.command(aliases=['adduser', 'addtodb'], help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addusertodb(self, ctx, uid: int):
        # Check if the user ID exists in the database; if not, add them to the database
        if str(uid) not in self.user_info:
            # Attempt to fetch the member from the server
            member = ctx.guild.get_member(uid)

            if member:
                self.user_info[str(uid)] = {
                    "info": {
                        "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Account_Created": member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "warns": [],
                        "notes": [],
                        "banned": [],
                        "kick_reason": [],
                        "kicks_amount": 0,
                        "avatar_url": str(member.avatar_url),
                    }
                }
                self.save_user_info()
                await ctx.send(f"User with ID `{uid}` (username: `{member.name}`) added to the database.")

                await utils.LogModAction(ctx.guild, 'Database', member, f"User added to the database by {ctx.author.name}", config=config)
            else:
                await ctx.send("User not found in the server.")
        else:
            await ctx.send(f"User with ID {uid} already exists in the database.")

    @commands.command(help='<UID> <Note>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addnote(self, ctx, user: discord.User, *, note_content: str):
        uid = str(user.id)

        # Check if the user ID exists in the database; if not, add them to the database
        if uid not in self.user_info:
            member = ctx.guild.get_member(user.id)
            if member:
                self.user_info[uid] = {
                    "info": {
                        "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Account_Created": member.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "warns": [],
                        "notes": [],
                        "banned": [],
                        "kick_reason": [],
                        "kicks_amount": 0,
                        "avatar_url": str(member.avatar_url),
                    }
                }
                self.save_user_info()
            else:
                await ctx.send("User not found in the server.")
                return

        # Continue with adding the note
        user_data = self.user_info[uid]
        notes = user_data["info"]["notes"]
        timestamp = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')
        # Check if there are existing notes
        note_number = 1
        for note in notes:
            if note.get("number"):
                note_number = note["number"] + 1

        # Add the note to the user's data
        notes.append({
            "number": note_number,
            "timestamp": timestamp,
            "author": ctx.author.name,
            "content": note_content
        })

        self.save_user_info()
        await ctx.send(f"📝 **Note Added**: {ctx.author.name} added a note for {user.mention} (#{note_number})")
        
        await utils.LogModAction(ctx.guild, 'Note', user, f"Note added by {ctx.author.name}\n\n Note: {note_content}", config=config)

    @commands.command(aliases=["removenote", "deletenote"], help='<UID> <Note #>', hidden=True)
    @commands.has_any_role("Admin")
    async def delnote(self, ctx, uid: int, note_number: int):
        # Check if the user ID exists in the database
        if str(uid) in self.user_info:
            user_data = self.user_info[str(uid)]
            notes = user_data["info"]["notes"]

            # Find the note with the specified number
            found_note = None
            for note in notes:
                if note.get("number") == note_number:
                    found_note = note
                    break

            if found_note:
                deleted_content = found_note.get("content", "")
                notes.remove(found_note)
                self.save_user_info()
                await ctx.send(f"🗑 **Note Removed**: {ctx.author.name} removed a note for {uid}\n(#{note_number}) - {deleted_content}")
                await utils.LogModAction(ctx.guild, 'Note', ctx.author, f"**Note Removed**: {ctx.author.name} removed a note for {uid}\n(#{note_number}) - {deleted_content}", config=config)
            else:
                await ctx.send(f"Note #{note_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["notes", "checknotes"], help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def listnotes(self, ctx, uid: int):
        if str(uid) in self.user_info:
            user_data = self.user_info[str(uid)]
            notes = user_data["info"]["notes"]

            if notes:
                embed = discord.Embed(
                    title=f"Notes for {user_data['info']['username']} (UID: {uid})",
                    color=0x00ff00,
                )

                embed.add_field(name="Username", value=user_data["info"]["username"], inline=False)

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

        if uid in self.user_info:
            user_data = self.user_info[uid]
            warnings = user_data["info"].get("warns", [])
            warning_number = len(warnings) + 1
            timestamp = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')
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

            await utils.LogModAction(ctx.guild, 'Warning', member, warning, warning_number, ctx.author.name, config=config)

            # Check if this is the 3rd warning
            if warning_number == 3:

                await member.send("You were kicked because of this warning. You can join again right away. Reaching 5 warnings will result in an automatic ban. Permanent invite link: https://discord.gg/SrREp2BbkS.")
                await member.kick(reason="3rd Warning")
                await ctx.send(f"{member.mention} has been kicked due to their 3rd warning.")
                await utils.LogModAction(ctx.guild, 'Kick', member, f"3rd Warning: {warning}", warning_number, ctx.author.name, config=config)

                user_data["info"]["kicks_amount"] = user_data["info"].get("kicks_amount", 0) + 1

            # Check if this is the 5th warning
            if warning_number == 5:
                
                ban_info = {
                    "timestamp": timestamp,
                    "issuer": "Shiny Ditto Bot",
                    "reason": "Banned due to their 5th warning",
                    "lifted": None, 
                }

                # Append the ban info to the list of bans in the user's data
                bans = user_data["info"].get("banned", [])
                bans.append(ban_info)
                user_data["info"]["banned"] = bans

                await member.send("You have received your 5th warning and have been banned from the server.")
                await ctx.guild.ban(member, reason="5th Warning")
                await ctx.send(f"{member.mention} has been banned due to their 5th warning.")

                await utils.LogModAction(ctx.guild, 'Ban', member, f"5th Warning: {warning}", warning_number, ctx.author.name, config=config)

            user_data["info"]["warns"] = warnings

            self.save_user_info()
            await ctx.send(f"⚠️ **Warned**: {ctx.author.mention} warned {member.mention} (warn #{warning_number})\n**Warning Message**:\n{warning}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["listwarnings", "listwarns"], help='<UID> <Warning #>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def checkwarning(self, ctx, user: discord.User, warning_number: Union[int, None]):
        # Check if the warning_number argument is None (not provided)
        if warning_number is None:
            await ctx.send("Please provide a warning number after the user ID.")
            return

        uid = str(user.id)

        # Check if the user ID exists in the database
        if uid in self.user_info:
            user_data = self.user_info[uid]
            warnings = user_data["info"]["warns"]

            # Find the warning with the specified number
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
                            f"Timestamp: {timestamp}\n"
                            f"Issuer: {issuer}\n"
                            f"Warning: {warning_text}")
            else:
                await ctx.send(f"Warning #{warning_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["deletewarning", "removewarning"], help='<UID> <Warning #>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def delwarning(self, ctx, user: discord.User, warning_number: int):
        uid = str(user.id)

        # Check if the user ID exists in the database
        if uid in self.user_info:
            user_data = self.user_info[uid]
            warnings = user_data["info"]["warns"]

            # Find the warning with the specified number
            found_warning = None
            for warning in warnings:
                if warning.get("number") == warning_number:
                    found_warning = warning
                    break

            if found_warning:
                deleted_content = found_warning.get("warning", "")
                warnings.remove(found_warning)
                self.save_user_info()
                await ctx.send(f"Deleted warning #{warning_number} for {user.mention}: {deleted_content}")

                await utils.LogModAction(ctx.guild, 'Warning', user, warning, warning_number, ctx.author, config=config)
            else:
                await ctx.send(f"Warning #{warning_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <Reason>')
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: Union[discord.Member, int], *, reason: str):
        if isinstance(member, int):
            # If member is an integer, assume it's a User ID
            try:
                # Attempt to get the member using the User ID
                member = await ctx.guild.fetch_member(member)
            except discord.NotFound:
                await ctx.send("User not found in this server.")
                return

        # Check if the user exists in the database
        uid = str(member.id)

        if uid in self.user_info:
            # Get the user's data from the database
            user_data = self.user_info[uid]
            # Increment the kicks_amount count
            user_data["info"]["kicks_amount"] = user_data["info"].get("kicks_amount", 0) + 1

            timestamp = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')

            kick_info = {
                "number": 1,
                "timestamp": timestamp,
                "issuer": ctx.author.name,
                "reason": reason
            }

            kicks = user_data["info"].get("kick_reason", [])

            # Find the highest "number" value in existing kick reasons and increment it
            existing_numbers = [kick.get("number", 0) for kick in kicks]
            if existing_numbers:
                kick_info["number"] = max(existing_numbers) + 1

            kicks.append(kick_info)
            user_data["info"]["kick_reason"] = kicks

            # Save the updated user data
            self.save_user_info()

            # Send a kick message to the user
            try:
                kick_message = f"You are about to be kicked from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou may join back but please learn from your mistakes. Permanent invite link: https://discord.gg/SrREp2BbkS"
                await member.send(kick_message)
            except discord.Forbidden:
                # The user has DMs disabled, or the bot doesn't have permission to send DMs
                await ctx.send(f"Failed to send a kick message to {member.mention} due to permission or privacy settings.")
            except Exception as e:
                # Handle other exceptions if necessary
                await ctx.send(f"An error occurred while sending a kick message to {member.mention}: {e}")

            # Attempt to kick the user
            try:
                await member.kick(reason=reason)
                # Send a reply in the channel confirming the kick
                await ctx.send(f"{member.mention} has been kicked for the following reason: {reason}")

                # Log the action in the mod logs, including the kick reason
                await utils.LogModAction(ctx.guild, 'Kick', member, reason, issuer=ctx.author, config=config)
            except discord.Forbidden:
                # The bot doesn't have permission to kick members
                await ctx.send(f"Failed to kick {member.mention} due to permission settings.")
            except Exception as e:
                # Handle other exceptions if necessary
                await ctx.send(f"An error occurred while kicking {member.mention}: {e}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <Reason>')
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.User, *, reason: str = None):
        if reason is None:
            await ctx.send("Please provide a reason for the ban.")
            return

        uid = str(user.id)
        user_with_uid = f"{user.name} - UID: {uid}"

        if uid in self.user_info:
            user_data = self.user_info[uid]
            # Send a DM to the user before banning
            try:
                ban_message = f"You have been banned from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou can appeal this ban by creating a ticket in the ban appeal discord server. Permanent invite link: https://discord.gg/CBuJgaWkrr"
                await user.send(ban_message)
            except discord.Forbidden:
                # The user has DMs disabled, or the bot doesn't have permission to send DMs
                await ctx.send(f"Failed to send a ban message to {user_with_uid} due to permission or privacy settings.")
                return
            except Exception as e:
                # Handle other exceptions if necessary
                await ctx.send(f"An error occurred while sending a ban message to {user_with_uid}: {e}")
                return

            timestamp = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')

            ban_info = {
                "timestamp": timestamp,
                "issuer": ctx.author.name,
                "reason": reason,
                "lifted": None,
            }

            # Append the ban info to the list of bans in the user's data
            bans = user_data["info"].get("banned", [])
            bans.append(ban_info)
            user_data["info"]["banned"] = bans

            # Save the user info
            self.save_user_info()

            # Ban the user after sending the DM
            await ctx.guild.ban(user, reason=reason)

            # Create an embed for the mod logs
            embed = discord.Embed(
                title="Ban",
                color=discord.Color.red(),
            )
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="User", value=user_with_uid, inline=False)
            embed.add_field(name="Reason", value=reason, inline=False)
            embed.add_field(name="Timestamp", value=datetime.datetime.now(), inline=True)

            await utils.LogModAction(ctx.guild, 'Ban', user, reason, ctx.author, user_data=user_data, config=config, embed=embed)

            await ctx.send(f"{user_with_uid} has been banned for the following reason: {reason}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def checkbans(self, ctx, user: discord.User):
        uid = str(user.id)

        if uid in self.user_info:
            user_data = self.user_info[uid]
            bans = user_data["info"].get("banned", [])

            if bans:
                embed = discord.Embed(
                    title=f"Bans for {user_data['info']['username']} (UID: {uid})",
                    color=0xFF0000,
                )

                embed.add_field(name="Username", value=user_data["info"]["username"], inline=False)

                for index, ban_info in enumerate(bans, start=1):
                    timestamp = ban_info["timestamp"]
                    issuer = ban_info["issuer"]
                    reason = ban_info["reason"]
                    lifted = ban_info["lifted"] or "Not Lifted"
                    unban_reason = ban_info.get("unban_reason", "N/A")

                    embed.add_field(
                        name=f"Ban #{index}",
                        value=f"Date/Time: {timestamp}\nIssuer: {issuer}\nReason: {reason}\nLifted: {lifted}\nUnban Reason: {unban_reason}",
                        inline=False
                    )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No bans found for user {uid}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <unban_reason>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def unban(self, ctx, user: discord.User, *, unban_reason: str = None):
        uid = str(user.id)

        if uid in self.user_info:
            user_data = self.user_info[uid]
            bans = user_data["info"].get("banned", [])

            for ban_info in bans:
                if not ban_info.get("lifted"):
                    ban_info["lifted"] = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')
                    ban_info["unban_reason"] = unban_reason

                    self.save_user_info()

                    await ctx.guild.unban(user)

                    embed = discord.Embed(
                        title="Unban",
                        color=discord.Color.green(),
                    )
                    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    embed.add_field(name="User", value=user.mention, inline=False)
                    embed.add_field(name="Unban Reason", value=unban_reason or "N/A", inline=False)
                    embed.add_field(name="Timestamp", value=datetime.datetime.now(), inline=False)

                    await utils.LogModAction(ctx.guild, 'Unban', user, unban_reason, ctx.author, config=config, embed=embed)

                    await ctx.send(f"{user.mention} has been unbanned.")
                    return

            await ctx.send(f"No active ban found for {user.mention}.")
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

        if uid in self.user_info:
            user_data = self.user_info[uid]

            try:
                # Send a DM to the user before banning
                ban_message = f"You have been Soft-Banned from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou may join back but please learn from your mistakes. Permanent invite link: https://discord.gg/SrREp2BbkS"
                await member.send(ban_message)
                # Ban the member
                await member.ban(reason=reason)
                # Wait for a short duration to allow the ban to take effect
                await asyncio.sleep(2)
                # Unban the member
                await member.unban(reason="Soft ban")

                timestamp = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')

                ban_info = {
                    "timestamp": timestamp,
                    "issuer": ctx.author.name,
                    "reason": reason,
                    "lifted": True,
                }

                user_data["info"].setdefault("banned", []).append(ban_info)

                self.save_user_info()

                await utils.LogModAction(ctx.guild, 'SoftBanned', member, reason, issuer=ctx.author, config=config)

                await ctx.send(f"{member.mention} has been soft-banned.")
            except discord.Forbidden:
                await ctx.send("Failed to send a DM to the user or perform the soft ban due to permission settings.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def togglechannel(self, ctx, channel: discord.TextChannel, role: discord.Role, permission_name: str):
        if permission_name not in ('send_messages', 'read_messages'):
            await ctx.send("Invalid permission name. Use 'send_messages' or 'read_messages'.")
            return

        permissions = channel.overwrites_for(role)

        if getattr(permissions, permission_name):
            setattr(permissions, permission_name, False)
        else:
            setattr(permissions, permission_name, True)

        await channel.set_permissions(role, overwrite=permissions)

        if getattr(permissions, permission_name):
            await ctx.send(f"Permission '{permission_name}' for role '{role.name}' in channel '{channel.name}' has been enabled.")
        else:
            await ctx.send(f"Permission '{permission_name}' for role '{role.name}' in channel '{channel.name}' has been disabled.")

    @togglechannel.error
    async def togglechannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")

def setup(bot):
    bot.add_cog(WelcomeMod(bot))