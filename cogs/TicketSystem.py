import discord
from discord import Embed
from discord.ext import commands
import json

class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open('config.json') as f:
            self.config = json.load(f)
        self.ticket_category_id = self.config['category_ids']['Tickets']
        if self.ticket_category_id is None:
            raise ValueError("Ticket category ID is not set in config.json")
        self.ticket_message_id = None
        self.ticket_types = {
            "🎫": "General Support",
            "🐛": "Bug Support",
            "🗒️": "Staff Application"
        }

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        role_names = ["Admin", "Moderator"]
        for role in channel.guild.roles:
            if role.name in role_names:
                permissions = role.permissions
                for perm, value in permissions:
                    print(f"{perm}: {value}")

    @commands.Cog.listener()
    async def on_ready(self):
        channel_id = self.config['channel_ids']['TicketChannel']
        if channel_id is None:
            raise ValueError("Ticket channel ID is not set in config.json")
        channel = self.bot.get_channel(channel_id)
        embed = Embed(title="Ticket Creation", description="React to create a ticket!", color=0x00ff00)
        embed.add_field(name="🎫", value="General Support", inline=False)
        embed.add_field(name="🐛", value="Bug Support", inline=False)
        embed.add_field(name="🗒️", value="Staff Application", inline=False)
        message = await channel.send(embed=embed)
        self.ticket_message_id = message.id
        for emoji in self.ticket_types.keys():
            await message.add_reaction(emoji)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, emoji):
        if emoji.message_id == self.ticket_message_id and str(emoji.emoji) in self.ticket_types:
            user = self.bot.get_user(emoji.user_id)
            if user.bot:
                return
            guild = self.bot.get_guild(emoji.guild_id)
            category = discord.utils.get(guild.categories, id=self.ticket_category_id)
            ticket_type = self.ticket_types[str(emoji.emoji)]
            channel = await guild.create_text_channel(f'{ticket_type}-{emoji.user_id}', category=category)
            embed = Embed(title=f"Ticket for {ticket_type}", description=f"Created by <@{emoji.user_id}>. Type your question here.", color=0x00ff00)
            message = await channel.send(embed=embed)
            await message.add_reaction('🔒')

            self.ticket_messages[message.id] = emoji.user_id
        elif str(emoji.emoji) == '🔒':
            user = self.bot.get_user(emoji.user_id)
            if user.bot:
                return
            guild = self.bot.get_guild(emoji.guild_id)
            member = guild.get_member(emoji.user_id)
            role_names = ["Admin", "Moderator"]
            if any(role.name in role_names for role in member.roles):
                channel = self.bot.get_channel(emoji.channel_id)
                await channel.delete()

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, emoji):
        if emoji.message_id in self.ticket_messages and str(emoji.emoji) == '🔒':
            user = self.bot.get_user(emoji.user_id)
            if user.bot:
                return
            guild = self.bot.get_guild(emoji.guild_id)
            member = guild.get_member(emoji.user_id)
            role_names = ["Admin", "Moderator"]
            if any(role.name in role_names for role in member.roles):
                channel = self.bot.get_channel(emoji.channel_id)
                await channel.delete()

    @commands.command(help="Close the ticket channel", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def close(self, ctx):
        if ctx.channel.category_id == self.ticket_category_id and ctx.channel.name.endswith(str(ctx.author.id)):
            await ctx.channel.delete()

def setup(bot):
    bot.add_cog(Tickets(bot))