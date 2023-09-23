import asyncio
import discord
from discord.ext import commands
import json
import os
import datetime
from utils import get_local_time  # You need to import the get_local_time function from your 'utils' module.

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}  # Store sticky messages for each channel
        self.data_folder = 'Database'
        self.warnings_file = os.path.join(self.data_folder, 'DBInfo.json')
        self.mod_logs = config.get('mod_logs')
        self.load_warnings()

    def load_warnings(self):
        if not os.path.exists(self.warnings_file):
            self.user_info = {}
            self.save_warnings()  # Create the user info file if it doesn't exist
        else:
            with open(self.warnings_file, "r") as f:
                try:
                    self.user_info = json.load(f)
                except json.JSONDecodeError:
                    self.user_info = {}  # Handle JSON decoding error

    def save_warnings(self):
        with open(self.warnings_file, "w") as f:
            json.dump(self.user_info, f, indent=4)

    async def remove_warning(self, ctx, member, idx):
        user_id = str(member.id)

        if user_id not in self.user_data:
            return -1  # User has no warnings

        warns = self.user_data[user_id].get("warns", [])

        if not warns:
            return -1  # User has no warnings

        if idx <= 0:
            return -3  # Warn index below 1
        if idx > len(warns):
            return -2  # Warn index is higher than warn count

        removed_warn = warns.pop(idx - 1)
        self.save_warnings()

        return discord.Embed(
            title="Warning Removed",
            description=f"**Removed by:** {ctx.author.mention}\n"
                        f"**User:** {member.mention}\n"
                        f"**Issuer:** {member.name}\n"
                        f"**Reason:** {removed_warn['reason']}",
            color=discord.Color.green(),
        )

    @commands.command(name="listwarns")
    @commands.has_any_role("Moderator", "Admin")
    async def listwarns(self, ctx, user: discord.User = None):
        """Lists warnings for a user"""
        if user is None or user == ctx.author:
            user = ctx.author

        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_author(name=f"Warns for {user.name}", icon_url=user.avatar_url)

        if str(user.id) in self.user_data:
            warns = self.user_data[str(user.id)].get("warns", [])
            if len(warns) == 0:
                embed.description = "There are none!"
                embed.color = discord.Color.green()
            else:
                for idx, warn in enumerate(warns):
                    embed.add_field(
                        name="{}: {}".format(idx + 1, warn["timestamp"]),
                        value="Issuer: {}\nReason: {}".format(warn["issuer_name"], warn["reason"])
                    )
        else:
            embed.description = "There are none!"
            embed.color = discord.Color.green()

        await ctx.send(embed=embed)

    @commands.command(name="warn")
    @commands.has_any_role("Moderator", "Admin")
    async def warn(self, ctx, member: discord.Member, *, reason=""):
        """Warn a user. Staff only."""
        issuer = ctx.message.author
        for role_name in ["Moderator", "Admin"]:
            required_role = discord.utils.get(ctx.guild.roles, name=role_name)
            if required_role and required_role in member.roles:
                await ctx.send("You cannot warn another staffer!")
                return

        warn_count = len(self.user_data.get(str(member.id), {}).get("warns", []))
        msg = "You were warned on GodHatesMe Pokemon Centre Server."
        if reason:
            msg += f" The given reason was: {reason}"

        if warn_count >= 5:
            msg += "\n\nYou were automatically banned due to five or more warnings."
            try:
                try:
                    await member.send(msg)
                except discord.errors.Forbidden:
                    pass
                await member.ban(reason=reason, delete_message_days=0)
            except Exception:
                await ctx.send("No permission to ban the warned member")
        elif warn_count >= 3:
            msg += "\n\nYou were kicked because of this warning. You can join again right away. Reaching 5 warnings will result in an automatic ban. Permanent invite link: https://discord.gg/SrREp2BbkS."
            try:
                try:
                    await member.send(msg)
                except discord.errors.Forbidden:
                    pass
                await member.kick(reason="Three or Four Warnings")
            except Exception:
                await ctx.send("No permission to kick the warned member")
        else:
            if warn_count == 2:
                msg += " __The next warn will automatically kick.__"
            
            # Customize the message based on other conditions, for example:
            if "bad_word" in reason.lower():
                msg += " Your warning contains offensive language."
            elif "spam" in reason.lower():
                msg += " Your warning is related to spamming."

            try:
                await member.send(msg)
            except discord.errors.Forbidden:
                pass

        # Add the warning to the database
        self.add_warning(member, reason, issuer)

        msg = f"⚠️ **Warned**: {issuer.name} warned {member.mention} (warn #{warn_count}) | {member}"
        if reason:
            msg += f" The given reason is: {reason}"

        await ctx.send(msg)
        await self.bot.get_channel(self.mod_logs).send(msg)

    def add_warning(self, member, reason, issuer):
        warn_data = {
            "timestamp": get_local_time(),
            "issuer_name": member.name,
            "reason": reason,
        }
        user_id = str(member.id)

        if user_id not in self.user_info:
            self.user_info[user_id] = {"info": {"warns": []}}

        self.user_info[user_id]["info"]["warns"].append(warn_data)
        self.save_warnings()

    @commands.command(name="clearwarns")
    @commands.has_any_role("Admin")
    async def clearwarns(self, ctx, member: discord.Member):
        """Clears warns of a specific member"""
        warnings_file = os.path.join(self.data_folder, 'warnings.json')
        with open(warnings_file, "r") as f:
            user_data = json.load(f)
        
        if str(member.id) not in user_data:
            await ctx.send("{} has no warns!".format(member.mention))
            return
        
        warn_count = len(user_data[str(member.id)].get("warns", []))
        
        if warn_count == 0:
            await ctx.send("{} has no warns!".format(member.mention))
            return
        
        user_data[str(member.id)]["warns"] = []
        
        with open(warnings_file, "w") as f:
            json.dump(user_data, f, indent=4)
        
        await ctx.send("{} no longer has any warns!".format(member.mention))
        msg = "🗑 **Cleared warns**: {} cleared {} warns from {} | {}".format(ctx.author.name, warn_count, member.mention, str(member))
        await ctx.send(msg)
        await self.bot.get_channel(self.mod_logs).send(msg)
    
    @commands.command(name="delwarn")
    @commands.has_any_role("Admin")
    async def delwarn(self, ctx, member: discord.Member, idx: int):
        """Remove a specific warning from a user. Staff only."""
        returnvalue = await self.remove_warning(ctx, member, idx)
        warnings_file = os.path.join(self.data_folder, 'warnings.json')
        with open(warnings_file, "r") as f:
            rsts = json.load(f)
            warn_count = len(rsts.get(str(member.id), {}).get("warns", []))
        if isinstance(returnvalue, int):
            if returnvalue == -1:
                await ctx.send("{} has no warns!".format(member.mention))
            elif returnvalue == -2:
                await ctx.send("Warn index is higher than warn count ({})!".format(warn_count))
            elif returnvalue == -3:
                await ctx.send("Warn index below 1!")
            return
        else:
            msg = "🗑 **Deleted warn**: {} removed warn {} from {} | {}".format(ctx.message.author.name, idx, member.mention, str(member))
            await ctx.send(msg)
            await self.bot.get_channel(self.mod_logs).send(msg, embed=returnvalue)

    # Modify the remove_warning method to accept ctx as a parameter
    async def remove_warning(self, ctx, member, idx):
        user_id = str(member.id)

        if user_id not in self.user_data:
            return -1  # User has no warnings

        warns = self.user_data[user_id].get("warns", [])

        if not warns:
            return -1  # User has no warnings

        if idx <= 0:
            return -3  # Warn index below 1
        if idx > len(warns):
            return -2  # Warn index is higher than warn count

        removed_warn = warns.pop(idx - 1)
        self.save_warnings()

        return discord.Embed(
            title="Warning Removed",
            description=f"**Removed by:** {ctx.author.mention}\n"
                        f"**User:** {member.mention}\n"
                        f"**Issuer:** {member.name}\n"
                        f"**Reason:** {removed_warn['reason']}",
            color=discord.Color.green(),
        )
    
    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick_user(self, ctx, user_id: int, *, reason="No reason provided"):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.kick(user, reason=reason)
            await ctx.send(f"{user.name}#{user.discriminator} has been kicked for: {reason}")
            self.add_kick(user, reason, ctx.author)
        except discord.NotFound:
            await ctx.send("User not found.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to kick users.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban_user(self, ctx, user_id: int, *, reason="No reason provided"):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.ban(user, reason=reason)
            await ctx.send(f"{user.name}#{user.discriminator} has been banned for: {reason}")
            self.add_ban(user, reason, ctx.author)
        except discord.NotFound:
            await ctx.send("User not found.")
        except discord.Forbidden:
            await ctx.send("I don't have permission to ban users.")
        except Exception as e:
            await ctx.send(f"An error occurred: {str(e)}")

    def add_kick(self, member, reason, issuer):
        kick_data = {
            "timestamp": get_local_time(),
            "issuer_name": member.name,
            "reason": reason,
        }
        user_id = str(member.id)

        if user_id not in self.user_data:
            self.user_data[user_id] = {"warns": [], "kicks": [], "bans": [], "notes": []}

        self.user_data[user_id]["kicks"].append(kick_data)
        self.save_warnings()

    def add_ban(self, member, reason, issuer):
        ban_data = {
            "timestamp": get_local_time(),
            "issuer_name": member.name,
            "reason": reason,
        }
        user_id = str(member.id)

        if user_id not in self.user_data:
            self.user_data[user_id] = {"warns": [], "kicks": [], "bans": [], "notes": []}

        self.user_data[user_id]["bans"].append(ban_data)
        self.save_warnings()

    @commands.command(name="addnote")
    async def add_note(self, ctx, member: discord.Member, *, note="No note provided"):
        issuer = ctx.message.author
        user_id = str(member.id)
        
        # Check if the user exists in the database
        if user_id in self.user_data:
            # Create a new note data
            note_data = {
                "timestamp": get_local_time(),
                "issuer_name": issuer.name,
                "note": note,
            }

            # Append the note to the user's notes in the database
            self.user_data[user_id]["info"]["notes"].append(note_data)
            self.save_user_info()  # Save the updated user data

            await ctx.send(f"📝 **Note Added**: {issuer.name} added a note for {member.mention} | {member}")
        else:
            await ctx.send(f"User {member.mention} not found in the database.")

    @commands.command(name="delnote")
    @commands.has_any_role("Admin")
    async def del_note(self, ctx, member: discord.Member, note_id: int):
        user_id = str(member.id)
        
        # Check if the user exists in the database and has notes
        if user_id in self.user_data and "notes" in self.user_data[user_id]["info"]:
            notes = self.user_data[user_id]["info"]["notes"]
            
            if note_id <= 0 or note_id > len(notes):
                await ctx.send("Invalid note ID.")
                return

            removed_note = notes.pop(note_id - 1)
            self.save_user_info()  # Save the updated user data

            await ctx.send(f"🗑 **Note Removed**: {ctx.author.name} removed a note for {member.mention}\n{removed_note['timestamp']}\n{removed_note['note']}")
        else:
            await ctx.send(f"User {member.mention} not found in the database or has no notes.")

    @commands.command(name="checknotes")
    async def check_notes(self, ctx, member: discord.Member):
        user_id = str(member.id)

        # Check if the user exists in the database and has notes
        if user_id in self.user_data and "notes" in self.user_data[user_id]["info"]:
            notes = self.user_data[user_id]["info"]["notes"]

            if notes:
                embed = discord.Embed(title=f"Notes for {member}", color=discord.Color.blue())
                for idx, note in enumerate(notes):
                    embed.add_field(name=f"Note #{idx + 1}", value=f"Added by: {note['issuer_name']}\n{note['timestamp']}\n{note['note']}", inline=False)
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No notes found for {member.mention}.")
        else:
            await ctx.send(f"User {member.mention} not found in the database or has no notes.")

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
        embed = discord.Embed(
            title="STICKY NOTE",
            description=message,
            color=discord.Color.blue()
        )

        sticky_msg = await channel.send(embed=embed)
        self.sticky_messages[channel] = sticky_msg

        await ctx.send(f"Sticky note added to {channel.mention}.")

    @commands.command(name='removesticky', aliases=['rs'], help='[#Channel]')
    @commands.has_any_role("Admin")
    async def remove_sticky(self, ctx, channel: discord.TextChannel):

        if channel in self.sticky_messages:
            sticky_msg = self.sticky_messages.pop(channel)
            await sticky_msg.delete()
            await ctx.send(f"Sticky note removed from {channel.mention}.")
        else:
            await ctx.send(f"No sticky note found in {channel.mention}.")

    @commands.Cog.listener()
    async def on_message(self, message):
        # Check if the message is not from the bot itself and it's in a channel with a sticky note
        if not message.author.bot and message.channel in self.sticky_messages:
            # Get the original sticky message
            original_sticky_msg = self.sticky_messages[message.channel]
            # Add Delay before deleting old sticky and reposting new one
            await asyncio.sleep(3)
            # Delete the old sticky message
            await original_sticky_msg.delete()
            # Send the new sticky message with the latest message content
            new_sticky_msg = await message.channel.send(f"{original_sticky_msg.content}")
            # Update the reference to the sticky message
            self.sticky_messages[message.channel] = new_sticky_msg

    ## End - Announcements | Sticky Notes

def setup(bot):
    bot.add_cog(Moderation(bot))
