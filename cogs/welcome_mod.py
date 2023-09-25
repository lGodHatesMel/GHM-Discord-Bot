import os
import discord
from discord.ext import commands
import random
import json
import asyncio
import utils
import secrets
import string
from typing import Union

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class WelcomeMod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}
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
        filtered_user_info = {user_id: data for user_id, data in self.user_info.items() if data["info"]}

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
            user_id = str(after.id)

            # Check if the user exists in the database
            if user_id in self.user_info:
                # Update the user's roles in the database
                self.user_info[user_id]["info"]["roles"] = [role.name for role in after.roles]
                self.save_user_info()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            user_id = str(message.author.id)

            # Check if the message is in a channel with a sticky note
            if message.channel in self.sticky_messages:
                # Get the original sticky message
                original_sticky_msg = self.sticky_messages[message.channel]
                # Add a delay before deleting the old sticky
                await asyncio.sleep(3)
                # Delete the old sticky message
                await original_sticky_msg.delete()
                # Check if the original sticky message content is not empty
                if original_sticky_msg.embeds and original_sticky_msg.embeds[0].description:
                    # Create a new embedded sticky note with the original content
                    new_embed = discord.Embed(
                        title="STICKY NOTE",
                        description=original_sticky_msg.embeds[0].description,
                        color=discord.Color.red()
                    )
                    # Send the new embedded sticky note
                    new_sticky_msg = await message.channel.send(embed=new_embed)
                    # Update the reference to the sticky message
                    self.sticky_messages[message.channel] = new_sticky_msg

            if user_id in self.user_info:
                self.user_info[user_id]["info"]["total_messages"] += 1
                self.save_user_info()

    @commands.command(help='Replies with Pong if bot is up', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def ping(self, ctx):
        await ctx.send('Pong')

    @commands.command(help='<username> or <UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateuser(self, ctx, new_username: str):
        user_id = str(ctx.author.id)
        if user_id in self.user_info:
            self.user_info[user_id]["info"]["username"] = new_username
            self.save_user_info()
            await ctx.send(f"Updated username to {new_username}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.Cog.listener()
    async def on_user_update(self, before, after):
        if before.avatar_url != after.avatar_url:
            # If the user's avatar URL has changed
            user_id = str(after.id)

            # Check if the user exists in the database
            if user_id in self.user_info:
                # Update the user's avatar URL in the database
                self.user_info[user_id]["info"]["avatar_url"] = str(after.avatar_url)
                self.save_user_info()

    @commands.Cog.listener()
    async def on_member_join(self, member):
        # Add a debug message to check if the event is triggered
        print(f"DEBUG: on_member_join event triggered for {member.name} ({member.id})")

        # Retrieve the welcome_channel_id
        self.welcome_channel_id = await self.get_welcome_channel_id()

        if self.welcome_channel_id:
            channel = self.bot.get_channel(self.welcome_channel_id)
            if channel:
                server = member.guild
                member_count = sum(1 for member in server.members if not member.bot)
                member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"

                # Generate a random color in hexadecimal notation
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

                user_id = str(member.id)

                # Check if the user already exists in the database
                if user_id in self.user_info:
                    # Update the "Left" field to None when a user rejoins
                    self.user_info[user_id]["info"]["Left"] = None
                else:
                    # If the user doesn't exist, create a new entry in the database
                    self.user_info[user_id] = {
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

                # Check if the user is in the banned list and their ban has not been lifted
                if user_id in self.user_info and self.user_info[user_id]["info"]["banned"]:
                    for ban_info in self.user_info[user_id]["info"]["banned"]:
                        if ban_info.get("lifted") is None:
                            # Send a message to the mod log indicating the user is still banned
                            await utils.log_mod_action(server, 'Ban', member, f"User is still banned: {ban_info['reason']}", config=config)

    # @commands.command()
    # async def test_welcome(self, ctx):
    #     if self.welcome_channel_id:
    #         server = ctx.guild
    #         member_count = sum(1 for member in server.members if not member.bot)
    #         member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"
            
    #         # Generate a random color in hexadecimal notation
    #         random_color = random.randint(0, 0xFFFFFF)
                
    #         welcome = {
    #             "title": "Welcome!",
    #             "description": f"Welcome to GodHatesMe Pokemon Centre {ctx.author.mention}, you are our {member_number}!\n\n"
    #                         f"Don't forget to read <#956760032232484884> and to get your Roles go to <#956769501607755806>!",
    #             "color": random_color,
    #         }

    #         embed = discord.Embed(title=welcome["title"], description=welcome["description"], color=welcome["color"])
    #         embed.set_thumbnail(url=ctx.author.avatar_url)
    #         embed.set_footer(text=ctx.author.name)
    #         await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Get the leave time as a datetime object
        leave_time = utils.get_local_time()
        
        # Convert the datetime object to a formatted string
        leave_time_str = leave_time.strftime('%Y-%m-%d %H:%M:%S')
        
        # Update the user info with the leave time
        user_id = str(member.id)
        if user_id in self.user_info:
            self.user_info[user_id]["info"]["Left"] = leave_time_str
            self.save_user_info()

    @commands.command(help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def info(self, ctx, user_id: int):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
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

            # Check if the user has warnings
            if "warns" in user_data["info"] and user_data["info"]["warns"]:
                total_warnings = len(user_data["info"]["warns"])
                embed.add_field(name="Warnings", value=total_warnings, inline=True)

            # Check if the user has kicks_amount
            if "kicks_amount" in user_data["info"]:
                total_kicks = user_data["info"]["kicks_amount"]
                embed.add_field(name="Kicks", value=total_kicks, inline=True)

            # Check if the user has notes
            if "notes" in user_data["info"] and user_data["info"]["notes"]:
                total_notes = len(user_data["info"]["notes"])
                embed.add_field(name="Notes", value=total_notes, inline=True)
                
            # Check if the user has bans
            if "banned" in user_data["info"] and user_data["info"]["banned"]:
                embed.add_field(name="Banned", value="Yes", inline=True)
            else:
                embed.add_field(name="Banned", value="No", inline=True)

            await ctx.send(embed=embed)
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<user_id> <key> <value>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateinfo(self, ctx, user_id: int, key: str, *, value: str):
        # Update user information (for testing purposes)
        if str(user_id) in self.user_info and key in self.user_info[str(user_id)]["info"]:
            self.user_info[str(user_id)]["info"][key] = value
            self.save_user_info()
            await ctx.send(f"Updated {key} for user {user_id} to {value}.")
        else:
            await ctx.send("User not found in the database or key does not exist.")

    # @commands.command()
    # async def simulate_join(self, ctx, user_id: int):
    #     # Simulate a user join (for testing purposes)
    #     if str(user_id) not in self.user_info:
    #         member = ctx.guild.get_member(user_id)
    #         if member:
    #             self.user_info[str(user_id)] = {
    #                 "info": {
    #                     "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
    #                     "Left": None,
    #                     "username": member.name,
    #                     "roles": [role.name for role in member.roles],
    #                     "total_messages": 0,
    #                     "warns": [],
    #                     "notes": [],
    #                     "banned": [],
    #                     "kick_reason": [],
    #                     "kicks_amount": 0,
    #                     "avatar_url": str(member.avatar_url),
    #                 }
    #             }
    #             self.save_user_info()
    #             await ctx.send(f"Simulated join for user {user_id}.")
    #         else:
    #             await ctx.send("User not found in the server.")
    #     else:
    #         await ctx.send("User already exists in the database.")
    
    # @commands.command()
    # async def simulate_leave(self, ctx, user_id: int):
    #     # Simulate a user leave (for testing purposes)
    #     if str(user_id) in self.user_info:
    #         leave_time = utils.get_local_time()
    #         self.user_info[str(user_id)]["info"]["Left"] = leave_time.strftime('%Y-%m-%d %H:%M:%S')
    #         self.save_user_info()
    #         await ctx.send(f"Simulated leave for user {user_id}.")
    #     else:
    #         await ctx.send("User not found in the database.")

    @commands.command(aliases=['adduser', 'addtodb'], help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addusertodb(self, ctx, user_id: int):
        # Check if the user ID exists in the database; if not, add them to the database
        if str(user_id) not in self.user_info:
            # Attempt to fetch the member from the server
            member = ctx.guild.get_member(user_id)

            if member:
                self.user_info[str(user_id)] = {
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
                await ctx.send(f"User with ID `{user_id}` (username: `{member.name}`) added to the database.")

                await utils.log_mod_action(ctx.guild, 'Database', member, f"User added to the database by {ctx.author.name}", config=config)
            else:
                await ctx.send("User not found in the server.")
        else:
            await ctx.send(f"User with ID {user_id} already exists in the database.")

    @commands.command(help='<UID> <Note>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addnote(self, ctx, user: discord.User, *, note_content: str):
        user_id = str(user.id)

        # Check if the user ID exists in the database; if not, add them to the database
        if user_id not in self.user_info:
            member = ctx.guild.get_member(user.id)
            if member:
                self.user_info[user_id] = {
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
        user_data = self.user_info[user_id]
        notes = user_data["info"]["notes"]
        timestamp = utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z")

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
        
        await utils.log_mod_action(ctx.guild, 'Note', user, f"Note added by {ctx.author.name}\n\n Note: {note_content}", config=config)

    @commands.command(aliases=["removenote"], help='<UID> <Note #>', hidden=True)
    @commands.has_any_role("Admin")
    async def delnote(self, ctx, user_id: int, note_number: int):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
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
                await ctx.send(f"🗑 **Note Removed**: {ctx.author.name} removed a note for {user_id}\n(#{note_number}) - {deleted_content}")
                await utils.log_mod_action(ctx.guild, 'Note', ctx.author, f"**Note Removed**: {ctx.author.name} removed a note for {user_id}\n(#{note_number}) - {deleted_content}", config=config)
            else:
                await ctx.send(f"Note #{note_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=["notes", "checknotes"], help='<UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def listnotes(self, ctx, user_id: int):
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
            notes = user_data["info"]["notes"]

            if notes:
                embed = discord.Embed(
                    title=f"Notes for {user_data['info']['username']} (UID: {user_id})",
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
                await ctx.send(f"No notes found for user {user_id}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=['warn'], help='<UID> <Reason>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addwarning(self, ctx, member: discord.Member, *, warning: str):
        # Check if the user exists in the database
        user_id = str(member.id)

        if user_id in self.user_info:
            user_data = self.user_info[user_id]
            warnings = user_data["info"].get("warns", [])
            warning_number = len(warnings) + 1
            timestamp = utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z")
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
                "timestamp": utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z"),
                "author": author,
                "warning": warning,
                "issuer": ctx.author.name  # Add the issuer here
            }

            warnings.append(new_warning)

            await utils.log_mod_action(ctx.guild, 'Warning', member, warning, warning_number, ctx.author.name, config=config)

            # Check if this is the 3rd warning
            if warning_number == 3:

                await member.send("You were kicked because of this warning. You can join again right away. Reaching 5 warnings will result in an automatic ban. Permanent invite link: https://discord.gg/SrREp2BbkS.")
                await member.kick(reason="3rd Warning")
                await ctx.send(f"{member.mention} has been kicked due to their 3rd warning.")
                await utils.log_mod_action(ctx.guild, 'Kick', member, f"3rd Warning: {warning}", warning_number, ctx.author.name, config=config)

                user_data["info"]["kicks_amount"] = user_data["info"].get("kicks_amount", 0) + 1

            # Check if this is the 5th warning
            if warning_number == 5:
                
                ban_info = {
                    "timestamp": utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z"),
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

                await utils.log_mod_action(ctx.guild, 'Ban', member, f"5th Warning: {warning}", warning_number, ctx.author.name, config=config)

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

        user_id = str(user.id)

        # Check if the user ID exists in the database
        if user_id in self.user_info:
            user_data = self.user_info[user_id]
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
        user_id = str(user.id)

        # Check if the user ID exists in the database
        if user_id in self.user_info:
            user_data = self.user_info[user_id]
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

                await utils.log_mod_action(ctx.guild, 'Warning', user, warning, warning_number, ctx.author, config=config)

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
        user_id = str(member.id)

        if user_id in self.user_info:
            # Get the user's data from the database
            user_data = self.user_info[user_id]

            # Increment the kicks_amount count
            user_data["info"]["kicks_amount"] = user_data["info"].get("kicks_amount", 0) + 1

            # Add kick reason to the user's data with a "number" field
            kick_info = {
                "number": 1,
                "timestamp": utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z"),
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
                await utils.log_mod_action(ctx.guild, 'Kick', member, reason, issuer=ctx.author, config=config)
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

        user_id = str(user.id)
        user_with_uid = f"{user.name} - ({user_id})"

        if user_id in self.user_info:
            user_data = self.user_info[user_id]

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

            # Generate a random ban ID with 6 digits
            ban_id = ''.join(secrets.choice(string.digits) for _ in range(6))

            # Add ban information to the user's data
            ban_info = {
                "timestamp": utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z"),
                "issuer": ctx.author.name,
                "reason": reason,
                "lifted": None,
                "ban_id": ban_id  # Add a unique identifier for the ban
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
            embed.add_field(name="UID", value=user_id, inline=True)
            embed.add_field(name="Ban ID", value=ban_id, inline=True)
            embed.add_field(name="Timestamp", value=utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z"), inline=True)

            await utils.log_mod_action(ctx.guild, 'Ban', user, reason, ctx.author, config=config, embed=embed)

            await ctx.send(f"{user_with_uid} has been banned for the following reason: {reason}")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <ban_id>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def checkbans(self, ctx, user: discord.User):
        user_id = str(user.id)

        if user_id in self.user_info:
            user_data = self.user_info[user_id]
            bans = user_data["info"].get("banned", [])

            if bans:
                embed = discord.Embed(
                    title=f"Bans for {user_data['info']['username']} (UID: {user_id})",
                    color=0xFF0000,
                )

                embed.add_field(name="Username", value=user_data["info"]["username"], inline=False)

                for index, ban_info in enumerate(bans, start=1):
                    timestamp = ban_info["timestamp"]
                    issuer = ban_info["issuer"]
                    reason = ban_info["reason"]
                    lifted = ban_info["lifted"] or "Not Lifted"
                    ban_id = ban_info.get("ban_id", "N/A")
                    unban_reason = ban_info.get("unban_reason", "N/A")

                    embed.add_field(
                        name=f"Ban #{index}",
                        value=f"Ban ID: {ban_id}\nDate/Time: {timestamp}\nIssuer: {issuer}\nReason: {reason}\nLifted: {lifted}\nUnban Reason: {unban_reason}",
                        inline=False
                    )

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No bans found for user {user_id}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(help='<UID> <ban_id> <unban_reason>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def unban(self, ctx, user: discord.User, ban_id: str, *, unban_reason: str = None):
        user_id = str(user.id)

        if user_id in self.user_info:
            user_data = self.user_info[user_id]
            bans = user_data["info"].get("banned", [])

            for ban_info in bans:
                if ban_info.get("ban_id") == ban_id:
                    if ban_info.get("lifted"):
                        await ctx.send(f"The ban with ID {ban_id} for {user.mention} has already been lifted.")
                        return

                    ban_info["lifted"] = utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z")
                    ban_info["unban_reason"] = unban_reason

                    self.save_user_info()

                    # Unban the user
                    await ctx.guild.unban(user)

                    # Create an embed for the mod logs
                    embed = discord.Embed(
                        title="Unban",
                        color=discord.Color.green(),
                    )
                    embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                    embed.add_field(name="User", value=user.mention, inline=False)
                    embed.add_field(name="Ban ID", value=ban_id, inline=False)
                    embed.add_field(name="Unban Reason", value=unban_reason or "N/A", inline=False)
                    embed.add_field(name="Timestamp", value=utils.get_local_time().strftime("%Y-%m-%d %I:%M:%S %p %Z"), inline=False)

                    await utils.log_mod_action(ctx.guild, 'Unban', user, unban_reason, ctx.author, config=config, embed=embed)

                    await ctx.send(f"{user.mention} has been unbanned. Ban ID: {ban_id}")
                    return

            await ctx.send(f"No ban with ID {ban_id} found for {user.mention}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command(aliases=['bd', 'down'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')
        author = ctx.message.author
        command = ctx.command.name
        print(f"{current_time} - {author.name} used the *{command}* command.")

    @commands.command(aliases=['announce', 'am'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def announcement(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Announcement:**\n{message}")
        await ctx.send(f"Announcement sent to {channel.mention}.")

    @commands.command(name='addsticky', aliases=['as'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def sticky_note(self, ctx, channel: discord.TextChannel, *, message):
        # Format the message content inside code blocks (```)
        formatted_message = f'```{message}```'

        embed = discord.Embed(
            title="STICKY NOTE",
            description=formatted_message,
            color=discord.Color.red()
        )

        sticky_msg = await channel.send(embed=embed)
        self.sticky_messages[channel.id] = sticky_msg  # Use channel.id as the key

        await ctx.send(f"Sticky note added to {channel.mention}.")

    @commands.command(name='removesticky', aliases=['rs', 'delsticky'], help='<#Channel>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def remove_sticky(self, ctx, channel: discord.TextChannel):

        if channel.id in self.sticky_messages:  # Check for channel.id in the dictionary
            sticky_msg = self.sticky_messages.pop(channel.id)
            await sticky_msg.delete()
            await ctx.send(f"Sticky note removed from {channel.mention}.")
        else:
            await ctx.send(f"No sticky note found in {channel.mention}.")

def setup(bot):
    bot.add_cog(WelcomeMod(bot))