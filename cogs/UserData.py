import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
import utils.utils as utils
from utils.botdb import CreateUserDatabase
from utils.Paginator import Paginator
from config import CHANNEL_IDS, GUILDID, ROLEIDS
import json
import sqlite3
from sqlite3 import Error
from typing import Union
from colorama import Fore, Style

class UserData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = CreateUserDatabase('Database/DBInfo.db')
        self.config = {'CHANNEL_IDS': CHANNEL_IDS}

    @cog_ext.cog_subcommand(base="Staff", name="updateuser", description="Update a user's username",
        options=[create_option(name="new_username", description="New username", option_type=3, required=True)], guild_ids=[GUILDID])
    @commands.command(name="updateuser", help='<username> or <UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def updateuser(self, ctx: Union[commands.Context, SlashContext], new_username: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

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

    # @commands.command(help='<user_id> <key> <value>', hidden=True)
    # @commands.has_any_role("Moderator", "Admin")
    # async def updateinfo(self, ctx, uid: int, key: str, *, value: str):
    #     cursor = self.conn.cursor()
    #     cursor.execute("SELECT * FROM UserInfo WHERE uid=?", (str(uid),))
    #     user = cursor.fetchone()
    #     if user:
    #         user_info = json.loads(user[1])
    #         if key in user_info:
    #             user_info[key] = value
    #             cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), str(uid)))
    #             self.conn.commit()
    #             await ctx.send(f"Updated {key} for user {uid} to {value}.")
    #         else:
    #             await ctx.send("Key does not exist.")
    #     else:
    #         await ctx.send("User not found in the database.")

    @cog_ext.cog_subcommand(base="Staff", name="addusertodb", description="Add a user to the database",
        options=[create_option(name="user", description="User to add", option_type=6, required=True)], guild_ids=[GUILDID])
    @commands.command(name="addusertodb", help='<@username or UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addusertodb(self, ctx: Union[commands.Context, SlashContext], user: discord.User):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

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
                config=self.config,
            )
        else:
            await ctx.send(f"User with ID {uid} already exists in the database.")
        print(f"Adding ({member.name} : {uid}) to the Database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

    @cog_ext.cog_subcommand(base="Staff", name="changenickname", description="Change a user's nickname",
        options=[
            create_option(name="member", description="Member to change nickname for", option_type=6, required=True),
            create_option(name="new_name", description="New nickname", option_type=3, required=True)
        ],guild_ids=[GUILDID])
    @commands.command(name="changenickname", help='<@username or UID> <NewName>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def changenickname(self, ctx: Union[commands.Context, SlashContext], member: discord.Member, *, new_name: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        try:
            await member.edit(nick=new_name)
            await ctx.send(f"Nickname changed for {member.mention} to {new_name}.")
        except discord.Forbidden:
            await ctx.send("Failed to change the nickname due to permission settings.")

    @cog_ext.cog_subcommand(base="Staff", name="accountage", description="Get a user's account age",
        options=[create_option(name="member", description="@username or UID", option_type=6, required=True)], guild_ids=[GUILDID])
    @commands.command(name="accountage", help='<@username or UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def accountage(self, ctx: Union[commands.Context, SlashContext], member: discord.Member = None):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

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

    @cog_ext.cog_subcommand(base="Staff", name="info", description="Get a user's info",
        options=[create_option(name="user", description="Username or UID", option_type=6, required=True)], guild_ids=[GUILDID])
    @commands.command(help='<@username or UID>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def info(self, ctx: Union[commands.Context, SlashContext], user: discord.User):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Helper"], ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

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

def setup(bot):
    bot.add_cog(UserData(bot))