import discord
from discord.ext import commands
import utils.utils as utils
from utils.botdb import CreateUserDatabase
from utils.Paginator import Paginator
from config import CHANNELIDS
import json
import asyncio
import sqlite3
from sqlite3 import Error
from typing import Union
from colorama import Fore, Style


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = CreateUserDatabase('Database/DBInfo.db')
        self.config = {'CHANNELIDS': CHANNELIDS}

    def __del__(self):
        self.conn.close()

    ## NOTES
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
            f"Note:\n{note_content}",
            issuer=ctx.author,
            config=self.config,
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
                    config=self.config,
                )
            else:
                await ctx.send(f"Note #{note_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    ## WARNINGS
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
                config=self.config,
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
                    config=self.config,
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
                    config=self.config,
                )

            warnings.append(new_warning)
            user_info["moderation"]["warns"] = warnings
            try:
                cursor.execute("UPDATE UserInfo SET info=? WHERE uid=?", (json.dumps(user_info), uid))
                self.conn.commit()
            except Exception as e:
                print(f"{Fore.RED}Error updating database: {e}{Style.RESET_ALL}")
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
                    config=self.config,
                )
            else:
                await ctx.send(f"Warning #{warning_number} not found for this user.")
        else:
            await ctx.send("User not found in the database.")

    ## KICKS
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
                kick_message = f"You have been kicked from {ctx.guild.name} for the following reason:\n\n{reason}\n\nYou may join back but please learn from your mistakes. Permanent invite link: https://discord.gg/SrREp2BbkS"
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
                    config=self.config,
                )
            except discord.Forbidden:
                await ctx.send(f"Failed to kick {user.mention} due to permission settings.")
            except Exception as e:
                await ctx.send(f"An error occurred while kicking {user.mention}: {e}")
        else:
            await ctx.send("User not found in the database.")

    ## BANS
    @commands.command(help='<@username or UID> <Reason>', hidden=True)
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, discord_user: discord.User, *, reason: str = None):
        uid = str(discord_user.id)
        if reason is None:
            await ctx.send("Please provide a reason for the ban.")
            return

        # if 'cheating' in reason:
        #     reason += " The ban reason involves cheating or exploiting game mechanics."
        if 'harassment' in reason:
            reason += " The ban reason involves harassment of other members."
        elif 'impersonation' in reason:
            reason += " The ban reason involves impersonating other members or staff."
        elif 'nsfw' in reason:
            reason += " The ban reason involves sharing NSFW content."
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
                config=self.config,
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
                        config=self.config,
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
                    config=self.config,
                )
                await ctx.send(f"{member.mention} has been soft-banned.")
            except discord.Forbidden:
                await ctx.send("Failed to send a DM to the user or perform the soft ban due to permission settings.")
        else:
            await ctx.send("User not found in the database.")

    ## DM BOT
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
            print(f"{Fore.GREEN}At {timestamp} {ctx.author} sent a DM to {user.name}. \nMessage content: '{{{message}}}'{Style.RESET_ALL}")
            await utils.LogAction(
                guild=ctx.guild,
                channel_name='DMLogs',
                action=f'BOT DM',
                target=user,
                reason=f"**Message Sent:**\n{message}",
                issuer=ctx.author,
                config=self.config
            )
        except discord.Forbidden:
            await ctx.message.reply("I'm not able to DM that user.")

    ## COMMANDS INFO
    @commands.command(help='Displays a list of ban reason', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def banshortcuts(self, ctx):
        shortcuts = {
            # 'cheating': '🎮 The ban reason involves cheating or exploiting game mechanics.',
            'harassment': '👥 The ban reason involves harassment of other members.',
            'impersonation': '🎭 The ban reason involves impersonating other members or staff.',
            'nsfw': '🔞 The ban reason involves sharing NSFW content.',
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

    @commands.command(help='Display Server Info', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def serverinfo(self, ctx):
        guild = ctx.guild
        embed = discord.Embed(
            title=f"{guild.name} Server Information",
            color=discord.Color.random()
        )
        embed.set_thumbnail(url=guild.icon_url)
        if guild.banner_url:
            embed.set_image(url=guild.banner_url)
        embed.add_field(name="Server Name", value=guild.name, inline=False)
        embed.add_field(name="Server ID", value=guild.id, inline=False)
        embed.add_field(name="Owner", value=guild.owner.name, inline=True)
        embed.add_field(name="Server Creation Date", value=guild.created_at.astimezone(utils.GetLocalTime().tzinfo).strftime('%m-%d-%y'), inline=False)
        embed.add_field(name="Members", value=guild.member_count, inline=False)
        embed.add_field(name="Roles", value=len(guild.roles), inline=True)
        embed.add_field(name="Channels", value=len(guild.channels), inline=True)
        embed.add_field(name="Emojis", value=len(guild.emojis), inline=False)
        embed.add_field(name="Boost Level", value=guild.premium_tier, inline=True)
        embed.add_field(name="Boosts", value=guild.premium_subscription_count, inline=True)
        # embed.add_field(name="Verification Level", value=str(guild.verification_level), inline=False)
        # embed.add_field(name="Default Role", value=guild.default_role, inline=True)
        if guild.afk_channel:
            embed.add_field(name="AFK Channel", value=guild.afk_channel.name, inline=False)
            embed.add_field(name="AFK Timeout", value=f"{guild.afk_timeout//60} minutes", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Moderation(bot))
