import discord
from discord.ext import commands

class RoleChannelToggle(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='toggle')
    async def toggle_role_permission(self, ctx, action, role: discord.Role, channel: discord.TextChannel):
        # Check if the user issuing the command has the necessary permissions (e.g., manage_roles)
        if ctx.author.guild_permissions.manage_roles:
            if action.lower() == 'channel':
                overwrites = channel.overwrites_for(role)

                # Toggle the 'send_messages' permission for the role in the channel
                if overwrites.send_messages is None or not overwrites.send_messages:
                    overwrites.send_messages = True
                    await channel.set_permissions(role, overwrite=overwrites)
                    await ctx.send(f"Role {role.name} can now send messages in {channel.name}.")
                else:
                    overwrites.send_messages = False
                    await channel.set_permissions(role, overwrite=overwrites)
                    await ctx.send(f"Role {role.name} can no longer send messages in {channel.name}.")
        else:
            await ctx.send("You don't have the necessary permissions to use this command.")

def setup(bot):
    bot.add_cog(RoleChannelToggle(bot))
