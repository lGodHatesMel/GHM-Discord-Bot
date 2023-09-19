import os
import discord
from discord.ext import commands
import random
import json
import datetime

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'DBInfo.json')
        self.load_user_info()

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
            print("User info saved successfully.")  # Add this line to print a success message

    async def get_welcome_channel_id(self):
        # Load your configuration file (config.json)
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
                        "Left": None,  # Initialize as None, to be updated if the user leaves
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
                        "notes": [],  # Initialize notes as an empty list
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
                        "Joined": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,
                        "username": member.name,
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
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
                # Add the user to the database with default information, including "notes" as an empty list and the retrieved username
                self.user_info[str(user_id)] = {
                    "info": {
                        "Joined": datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        "Left": None,  # Initialize as None, to be updated if the user leaves
                        "username": member.name,  # Retrieve the username from the member
                        "notes": [],  # Initialize notes as an empty list
                        "roles": [role.name for role in member.roles],
                        "total_messages": 0,
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
    async def add_note(self, ctx, user_id: int, *, note_content: str):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            # Get the current timestamp
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Add the note to the user's data
            self.user_info[str(user_id)]["info"]["notes"].append({
                "timestamp": timestamp,
                "author": ctx.author.name,  # You can change this to the author's username or ID if needed
                "content": note_content
            })
            self.save_user_info()
            await ctx.send(f"Note added for user {user_id}.")
        else:
            await ctx.send("User not found in the database.")
            
    @commands.command()
    async def check_notes(self, ctx, user_id: int):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
            notes = user_data["info"]["notes"]
            if notes:
                # Format and send the notes as a list
                note_list = [f"{note['timestamp']} - {note['author']}: {note['content']}" for note in notes]
                await ctx.send(f"Notes for user {user_id}:\n" + "\n".join(note_list))
            else:
                await ctx.send("No notes found for this user.")
        else:
            await ctx.send("User not found in the database.")
            
    @commands.command()
    async def delete_note(self, ctx, user_id: int, note_index: int):
        # Check if the user ID exists in the database
        if str(user_id) in self.user_info:
            user_data = self.user_info[str(user_id)]
            notes = user_data["info"]["notes"]
            if notes and 0 <= note_index < len(notes):
                # Check if the note index is valid
                deleted_note = notes.pop(note_index)
                self.save_user_info()
                await ctx.send(f"Deleted note for user {user_id}:\n{deleted_note['timestamp']} - {deleted_note['author']}: {deleted_note['content']}")
            else:
                await ctx.send("Invalid note index or no notes found for this user.")
        else:
            await ctx.send("User not found in the database.")

def setup(bot):
    bot.add_cog(Welcome(bot))