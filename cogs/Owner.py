import discord
from discord.ext import commands
import utils.utils as utils
from utils.botdb import CreateUserDatabase
from utils.Paginator import Paginator
import json
import asyncio
import sqlite3
from sqlite3 import Error
from typing import Union
from colorama import Fore, Style
import logging

class Owner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = CreateUserDatabase('Database/DBInfo.db')

    @commands.command(help="Shows bot's latency", hidden=True)
    @commands.is_owner()
    async def botping(self, ctx):
        try:
            BotLatency = self.bot.latency * 1000

            embed = discord.Embed(
                title="Server Ping",
                description=f"Server ping is currently {BotLatency:.2f}ms",
                color=discord.Color.red(),
            )
            avatar_url = (
                ctx.author.avatar.url
                if isinstance(ctx.author.avatar, discord.Asset)
                else "https://www.gravatar.com/avatar/?d=retro&s=32"
            )
            embed.set_thumbnail(url=avatar_url)

            reply = await ctx.message.reply(embed=embed)
            if reply:
                print("Bot ping message sent successfully.")
            else:
                print("Failed to send bot ping message.")
        except Exception as e:
            logging.error(f"An error occurred while trying to get the bot's ping: {e}")

    @commands.command(help="Set the bot's nickname", hidden=True)
    @commands.is_owner()
    async def setbotnickname(self, ctx, *, nickname):
        await ctx.guild.me.edit(nick=nickname)
        await ctx.message.reply(f"Nickname was changed to **{nickname}**")

    @commands.command(help="Set the bot's status", hidden=True)
    @commands.is_owner()
    async def setstatus(self, ctx, status: str, *, message: str):
        if status.lower() == "online":
            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game(name=message))
        elif status.lower() == "idle":
            await self.bot.change_presence(status=discord.Status.idle, activity=discord.Game(name=message))
        elif status.lower() == "dnd":
            await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name=message))
        elif status.lower() == "offline":
            await self.bot.change_presence(status=discord.Status.offline, activity=discord.Game(name=message))
        else:
            await ctx.send("Invalid status. Please choose from: online, idle, dnd, or offline")

    @commands.command(help="Get BOTS UP time", hidden=True)
    @commands.is_owner()
    async def uptime(self, ctx):
        uptime = utils.GetUptime()
        await ctx.message.reply(f"Bot has been up for {uptime}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def forcesavedb(self, ctx):
        self.conn.commit()
        await ctx.message.reply("Database saved successfully!")
        print(f"Forced saved database @ {utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')}")

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

    # Good to use if you are using this after already having alot of members in your server
    @commands.command(hidden=True)
    @commands.is_owner()
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
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("Shutting down...")
        await ctx.bot.logout()

def setup(bot):
    bot.add_cog(Owner(bot))