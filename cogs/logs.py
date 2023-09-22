import discord
from discord.ext import commands
import json
import utils

with open('config.json', 'r') as config_file:
    config = json.load(config_file)

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_mention(target):
        if isinstance(target, discord.Role) or isinstance(target, discord.User):
            return target.mention
        else:
            return target.name

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.name != after.name:
            await self.log_user_change(after, f"Username changed from {before.name} to {after.name}")

        if before.roles != after.roles:
            added_roles = [role for role in after.roles if role not in before.roles]
            removed_roles = [role for role in before.roles if role not in after.roles]

            if added_roles:
                await self.log_user_change(after, f"Roles added: {', '.join([role.name for role in added_roles])}")
            
            if removed_roles:
                await self.log_user_change(after, f"Roles removed: {', '.join([role.name for role in removed_roles])}")

    async def log_user_change(self, user, change_message):
        member_logs_channel_id = config.get('member_logs_channel_id')

        if member_logs_channel_id:
            mod_logs_channel = user.guild.get_channel(int(member_logs_channel_id))

            if mod_logs_channel:
                embed = discord.Embed(
                    title="User Change Log",
                    description=f"User: {user.mention}",
                    color=discord.Color.green(),
                )

                embed.add_field(name="Change Details", value=change_message, inline=False)
                
                timestamp = utils.get_local_time()
                embed.set_footer(text=f"|| ^UID: {user.id} • {timestamp}^ ||")

                await mod_logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        server_logs_channel_id = self.config.get('server_logs_channel_id')

        if server_logs_channel_id:
            server_logs_channel = channel.guild.get_channel(int(server_logs_channel_id))

            if server_logs_channel:
                embed = discord.Embed(
                    title="Text Channel Created",
                    description=f"Channel: {channel.mention}",
                    color=discord.Color.green(),
                )
                timestamp = utils.get_local_time()
                embed.set_footer(text=f"Timestamp: {timestamp} | Channel ID: {channel.id}")
                await server_logs_channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        server_logs_channel_id = config.get('server_logs_channel_id')

        if server_logs_channel_id:
            server_logs_channel = after.guild.get_channel(int(server_logs_channel_id))

            if server_logs_channel:
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
                    embed.add_field(name="Change Details", value=change_message, inline=False)

                    timestamp = utils.get_local_time()
                    embed.set_footer(text=f"||Channel ID: {after.id} • {timestamp}||")

                    await server_logs_channel.send(embed=embed)

def setup(bot):
    bot.add_cog(Logs(bot))