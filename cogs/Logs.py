import discord
from discord.ext import commands
import json
import utils

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

    async def LogUserChange(self, user, change_message):
        MemberLogChannelId = self.config['channel_ids'].get('MemberLogs', None)

        if MemberLogChannelId:
            ModLogsChannelID = user.guild.get_channel(int(MemberLogChannelId))

            if ModLogsChannelID:
                embed = discord.Embed(
                    title="User Change Log",
                    description=f"User: {user.mention}",
                    color=discord.Color.green(),
                )

                embed.add_field(name="Change Details", value=change_message, inline=False)

                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')
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
                    description=f"Channel: {channel.mention}",
                    color=discord.Color.green(),
                )
                timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')
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

                # Check for changes in permissions (overwrites)
                for target, overwrite in after.overwrites.items():
                    if target not in before.overwrites or before.overwrites[target] != overwrite:
                        # Get permission names and their status only if changed
                        permission_changes = []
                        for perm, value in overwrite:
                            if target not in before.overwrites or getattr(overwrite, perm) != getattr(before.overwrites[target], perm):
                                emoji = ":white_check_mark:" if value else ":x:"
                                permission_changes.append(f"{perm} ➜ {emoji}")

                        if permission_changes:
                            permission_changes_str = '\n'.join(permission_changes)
                            changes.append(f"Role/User:{target.mention}\n\n{permission_changes_str}")

                change_message = "\n\n".join(changes)

                if change_message:
                    while len(change_message) > 1024:
                        index = change_message.rfind('\n\n', 0, 1024)
                        embed.add_field(name="Change Details", value=change_message[:index], inline=False)
                        change_message = change_message[index+2:]

                    embed.add_field(name="Change Details", value=change_message, inline=False)

                    timestamp = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')
                    embed.set_footer(text=f"Channel ID: {after.id} • {timestamp}")

                    await ServerLogsChannel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logs(bot))