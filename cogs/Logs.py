import discord
from discord.ext import commands
import json
import utils.utils as utils
from utils.utils import custom_emojis

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config.json', 'r') as config_file:
            self.config = json.load(config_file)

    @staticmethod
    def get_mention(target):
        if isinstance(target, discord.Role) or isinstance(target, discord.User):
            return target.mention
        else:
            return target.name

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.name != after.name:
            await self.LogUserChange(after, f"Username changed from {before.name} to {after.name}")

        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles:
                await self.LogUserChange(after, f"Roles added: {', '.join([role.name for role in added_roles])}")
            if removed_roles:
                await self.LogUserChange(after, f"Roles removed: {', '.join([role.name for role in removed_roles])}")

        if before.premium_since is None and after.premium_since is not None:
            channel_id = self.bot.config["channel_ids"]["ServerAnnocementChannel"]
            channel = self.bot.get_channel(channel_id)
            embed = discord.Embed(title=f"{custom_emojis['nitroboost']} New Server Boost! {custom_emojis['nitroboost']}", description=f"{emojis['tada']} Thank you {after.mention} for boosting the server! {custom_emojis['tada']}", color=discord.Color.purple())
            embed.set_author(name=str(after), icon_url=after.avatar_url)
            await channel.send(embed=embed)

    async def LogUserChange(self, user, change_message):
        MemberLogChannelId = self.config['channel_ids'].get('MemberLogs', None)

        if MemberLogChannelId:
            ModLogsChannelID = user.guild.get_channel(int(MemberLogChannelId))

            if ModLogsChannelID:
                embed = discord.Embed(
                    title="User Changes",
                    description=f"User: {user.mention}",
                    color=discord.Color.green(),
                )

                embed.set_author(name=f"{user.name}", icon_url=user.avatar_url)

                change_message = change_message.replace("Roles added: ", "Roles Added:\n")
                change_message = change_message.replace("Roles removed: ", "Roles Removed:\n")
                change_message = change_message.replace(", ", "\n")

                embed.add_field(name="**Updated Details**", value=change_message, inline=False)

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                embed.set_footer(text=f"UID: {user.id} • {timestamp}")

                await ModLogsChannelID.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        ServerLogsChannelID = self.config['channel_ids'].get('ServerLogs', None)

        if ServerLogsChannelID:
            ServerLogsChannel = channel.guild.get_channel(int(ServerLogsChannelID))

            if ServerLogsChannel:
                embed = discord.Embed(
                    title="Text Channel Created",
                    description=f"Name: {channel.name}\nCategory: {channel.category}",
                    color=discord.Color.green(),
                )

                changes = []
                # Add the permission overwrites for each role or user
                for target, overwrite in channel.overwrites.items():
                    target_type = "Role" if isinstance(target, discord.Role) else "User"
                    target_mention = "@everyone" if str(target) == "@everyone" else target.mention
                    changes.append(f"{target_type} override for {target_mention}")

                    # Iterate over all permissions
                    for perm in discord.Permissions.ALL_PERMISSIONS:
                        if perm in overwrite:
                            emoji = ":white_check_mark:" if overwrite[perm] else ":x:"
                            changes.append(f"{perm.replace('_', ' ').title()}: {emoji}")

                change_message = "\n".join(changes)
                if change_message:
                    while len(change_message) > 1024:
                        index = change_message.rfind('\n', 0, 1024)
                        embed.add_field(name="**Permission Details**", value=change_message[:index], inline=False)
                        change_message = change_message[index+1:]
                    embed.add_field(name="**Permission Details**", value=change_message, inline=False)

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                embed.set_footer(text=f"Channel ID: {channel.id} • {timestamp}")
                await ServerLogsChannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        ServerLogsChannelID = self.config['channel_ids'].get('ServerLogs', None)

        if ServerLogsChannelID:
            ServerLogsChannel = after.guild.get_channel(int(ServerLogsChannelID))

            if ServerLogsChannel:
                embed = discord.Embed(
                    title="Text Channel Updated",
                    description=f"Overwrites in {after.mention} updated",
                    color=discord.Color.blue(),
                )

                changes = []
                for target, overwrite in after.overwrites.items():
                    if target not in before.overwrites or before.overwrites[target] != overwrite:
                        # Check if the target is a role or a user
                        target_type = "Role" if isinstance(target, discord.Role) else "User"
                        target_mention = "@everyone" if str(target) == "@everyone" else target.mention
                        changes.append(f"{target_type} override for {target_mention}")

                        # Iterate over the permissions in the overwrite
                        for perm, value in overwrite:
                            emoji = ":white_check_mark:" if value else ":x:"
                            changes.append(f"{perm.replace('_', ' ').title()}: {emoji}")

                change_message = "\n".join(changes)
                if change_message:
                    while len(change_message) > 1024:
                        index = change_message.rfind('\n', 0, 1024)
                        embed.add_field(name="**Changed Details**", value=change_message[:index], inline=False)
                        change_message = change_message[index+1:]

                    embed.add_field(name="**Changed Details**", value=change_message, inline=False)
                    timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                    embed.set_footer(text=f"Channel ID: {after.id} • {timestamp}")
                    await ServerLogsChannel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        ServerLogsChannelID = self.config['channel_ids'].get('ServerLogs', None)

        if ServerLogsChannelID:
            ServerLogsChannel = channel.guild.get_channel(int(ServerLogsChannelID))

            if ServerLogsChannel:
                # Fetch the audit logs
                audit_logs = await channel.guild.audit_logs(limit=1, action=discord.AuditLogAction.channel_delete).flatten()
                # The user who deleted the channel is the user who triggered the latest 'channel_delete' audit log entry
                deleter = audit_logs[0].user.name if audit_logs else "Unknown"

                embed = discord.Embed(
                    title="Text Channel Deleted",
                    description=f"Name: {channel.name}\n\nCategory: {channel.category}\n\nDeleted by: {deleter}",
                    color=discord.Color.red(),
                )

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
                embed.set_footer(text=f"Channel ID: {channel.id} • {timestamp}")
                await ServerLogsChannel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logs(bot))