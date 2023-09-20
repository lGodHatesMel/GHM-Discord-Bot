import os
import discord
from discord.ext import commands
import random
import json
import datetime
import asyncio

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'DBInfo.json')
        self.load_user_info()
        self.welcome_channel_id = None

    def load_user_info(self):
        if not os.path.exists(self.database_folder):
            os.makedirs(self.database_folder)

        if not os.path.exists(self.database_file):
            self.user_info = {}
        else:
            with open(self.database_file, 'r') as f:
                self.user_info = json.load(f)

    def save_user_info(self):
        with open(self.database_file, 'w') as f:
            json.dump(self.user_info, f, indent=4)
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

    @commands.command()
    async def update_username(self, ctx, new_username: str):
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

                # Log user's join date and additional info in the database
                self.user_info[str(member.id)] = {
                    "info": {
                        "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "warns": [],
                        "notes": [],
                        "avatar_url": str(member.avatar_url),
                    }
                }
                self.save_user_info()

    @commands.command()
    async def test_welcome(self, ctx):
        if self.welcome_channel_id:
            server = ctx.guild
            member_count = sum(1 for member in server.members if not member.bot)
            member_number = f"{member_count}{'th' if 11 <= member_count % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(member_count % 10, 'th')} member"
            
            # Generate a random color in hexadecimal notation
            random_color = random.randint(0, 0xFFFFFF)
                
            welcome = {
                "title": "Welcome!",
                "description": f"Welcome to GodHatesMe Pokemon Centre {ctx.author.mention}, you are our {member_number}!\n\n"
                               f"Don't forget to read <#956760032232484884> and to get your Roles go to <#956769501607755806>!",
                "color": random_color,
            }

            embed = discord.Embed(title=welcome["title"], description=welcome["description"], color=welcome["color"])
            embed.set_thumbnail(url=ctx.author.avatar_url)
            embed.set_footer(text=ctx.author.name)
            await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        # Log user's leave date in the database when they leave the server
        if str(member.id) in self.user_info:
            self.user_info[str(member.id)]["info"]["Left"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_user_info()

    @commands.command()
    async def info(self, ctx, user_id: int):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
            join_date = user_data["info"]["Joined"]
            leave_date = user_data["info"]["Left"] if "Left" in user_data["info"] else "N/A"
            
            embed = discord.Embed(
                title="User Info",
                color=0x00ff00,
                description=f"**Join Date:** {join_date}\n**Leave Date:** {leave_date}"
            )

            # Add additional info to the embed
            embed.add_field(name="Username", value=user_data["info"]["username"])
            embed.add_field(name="Roles", value=", ".join(user_data["info"]["roles"]))
            embed.add_field(name="Total Messages", value=user_data["info"]["total_messages"])
            embed.add_field(name="Avatar URL", value=user_data["info"]["avatar_url"])
            
            await ctx.send(embed=embed)
        else:
            await ctx.send("User not found in the database.")

    @commands.command()
    async def update_info(self, ctx, user_id: int, key: str, *, value: str):
        # Update user information (for testing purposes)
        if str(user_id) in self.user_info and key in self.user_info[str(user_id)]["info"]:
            self.user_info[str(user_id)]["info"][key] = value
            self.save_user_info()
            await ctx.send(f"Updated {key} for user {user_id} to {value}.")
        else:
            await ctx.send("User not found in the database or key does not exist.")

    @commands.command()
    async def simulate_join(self, ctx, user_id: int):
        # Simulate a user join (for testing purposes)
        if str(user_id) not in self.user_info:
            member = ctx.guild.get_member(user_id)
            if member:
                self.user_info[str(user_id)] = {
                    "info": {
                        "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "warns": [],
                        "notes": [],
                        "avatar_url": str(member.avatar_url),
                    }
                }
                self.save_user_info()
                await ctx.send(f"Simulated join for user {user_id}.")
            else:
                await ctx.send("User not found in the server.")
        else:
            await ctx.send("User already exists in the database.")
    
    @commands.command()
    async def simulate_leave(self, ctx, user_id: int):
        # Simulate a user leave (for testing purposes)
        if str(user_id) in self.user_info:
            self.user_info[str(user_id)]["info"]["Left"] = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_user_info()
            await ctx.send(f"Simulated leave for user {user_id}.")
        else:
            await ctx.send("User not found in the database.")
    
    @commands.command()
    async def adduserdb(self, ctx, user_id: int):
        # Check if the user ID exists in the database
        if str(user_id) not in self.user_info:
            # Attempt to fetch the member from the server
            member = ctx.guild.get_member(user_id)

            if member:
                self.user_info[str(user_id)] = {
                    "info": {
                        "Joined": member.joined_at.strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "warns": [],
                        "notes": [],
                        "avatar_url": str(member.avatar_url),
                    }
                }
                self.save_user_info()
                await ctx.send(f"User with ID {user_id} (username: {member.name}) added to the database.")
            else:
                await ctx.send("User not found in the server.")
        else:
            await ctx.send(f"User with ID {user_id} already exists in the database.")

    @commands.command()
    @commands.has_any_role("Moderator", "Admin")
    async def addnote(self, ctx, user_id: int, *, note_content: str):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
            notes = user_data["info"]["notes"]

            # Get the current timestamp
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

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
            await ctx.send(f"Note added for user {user_id} with note #{note_number}.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command()
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
                notes.remove(found_note)
                self.save_user_info()
                await ctx.send(f"Deleted note #{note_number} for user {user_id}.")
            else:
                await ctx.send(f"Note #{note_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    @commands.command()
    @commands.has_any_role("Moderator", "Admin")
    async def notes(self, ctx, user_id: int):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
            notes = user_data["info"]["notes"]

            if notes:
                # Create an embed to display user information and notes
                embed = discord.Embed(
                    title=f"Notes for {user_data['info']['username']} (UID: {user_id})",
                    color=0x00ff00,
                )

                # Add user information to the embed
                embed.add_field(name="Username", value=user_data["info"]["username"], inline=False)
                #embed.add_field(name="Warnings", value=user_data["info"]["total_warnings"], inline=False)

                # Format and add the notes as fields in the embed
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

    ## Start - Announcement | Sticky Notes
    @commands.command(name='botdown', aliases=['bd', 'down'], help='[#Channel] [Message]')
    @commands.has_any_role("Admin")
    async def botdown_command(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        author = ctx.message.author
        command = ctx.command.name
        print(f"{current_time} - {author.name} used the *{command}* command.")

    @commands.command(name='announcement', aliases=['announce', 'am'], help='[#Channel] [Message]')
    @commands.has_any_role("Admin")
    async def announcement(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Announcement:**\n{message}")
        await ctx.send(f"Announcement sent to {channel.mention}.")

    @commands.command(name='addsticky', aliases=['as'], help='[#Channel] [Message]')
    @commands.has_any_role("Admin")
    async def sticky_note(self, ctx, channel: discord.TextChannel, *, message):
        # Format the message content inside code blocks (```)
        formatted_message = f'```{message}```'

        embed = discord.Embed(
            title="STICKY NOTE",
            description=formatted_message,  # Use the formatted message here
            color=discord.Color.red()
        )

        sticky_msg = await channel.send(embed=embed)
        self.sticky_messages[channel] = sticky_msg

        await ctx.send(f"Sticky note added to {channel.mention}.")

    @commands.command(name='removesticky', aliases=['rs', 'delsticky'], help='[#Channel]')
    @commands.has_any_role("Admin")
    async def remove_sticky(self, ctx, channel: discord.TextChannel):

        if channel in self.sticky_messages:
            sticky_msg = self.sticky_messages.pop(channel)
            await sticky_msg.delete()
            await ctx.send(f"Sticky note removed from {channel.mention}.")
        else:
            await ctx.send(f"No sticky note found in {channel.mention}.")
    ## End - Announcements | Sticky Notes

def setup(bot):
    bot.add_cog(Welcome(bot))