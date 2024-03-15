import discord
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.model import SlashCommandOptionType
import sqlite3
from discord.ext import commands
import os
import sqlite3
from utils.Paginator import Paginator
from utils.botdb import CreateCustomCommandsDatabase
from config import GUILDID, ROLEIDS


class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'custom_commands.db')
        self.table_name = 'custom_commands'

        conn = sqlite3.connect(self.database_file)
        cursor = conn.cursor()
        CreateCustomCommandsDatabase(cursor, self.table_name)
        conn.commit()
        conn.close()

        self.LoadCustomCommands()

    def LoadCustomCommands(self):
        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()
            c.execute(f'select * from {self.table_name}')
            CustomName = c.fetchall()
            conn.close()

            # Register the custom commands to the bot
            for CommandName, command_response in CustomName:
                async def custom_command(ctx, response=command_response):
                    await ctx.send(response)
                self.bot.add_command(commands.Command(custom_command, name=CommandName))
        except Exception as e:
            print(f'An error occurred while loading custom commands: {str(e)}')

    def RefreshCustomCommands(self):
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute(f'select * from {self.table_name}')
        rows = c.fetchall()
        for row in rows:
            command_name, command_response = row
            if self.bot.get_command(command_name):
                continue  # Skip this command if it already exists
            async def custom_command(ctx):
                await ctx.send(command_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))
        conn.close()

    @cog_ext.cog_slash(name="refreshcommands", description="(STAFF) Refresh custom commands", guild_ids=[GUILDID])
    async def _refreshcommands(self, ctx: SlashContext):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        try:
            self.RefreshCustomCommands()
            await ctx.send('Custom commands refreshed successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @cog_ext.cog_slash(name="showcustomcommands", description="Show all custom commands", guild_ids=[GUILDID])
    async def showcustomcommands(self, ctx: SlashContext):
        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()
            c.execute(f'select * from {self.table_name}')
            result = c.fetchall()
            if result is None:
                await ctx.send(f'No custom commands found.', hidden=True)
                return

            embeds = []
            for i in range(0, len(result), 5):
                embed = Embed(title="Custom Commands", description="Use these commands with /custom command_name", color=0x00ff00)
                for row in result[i:i+5]:
                    embed.add_field(name=row[0], value=row[1], inline=False)
                    embed.set_footer(text="Use the reactions to navigate between pages.")
                embeds.append(embed)

            paginator = Paginator(ctx, embeds)
            await paginator.start()
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}', hidden=True)

    @cog_ext.cog_slash(name="custom", description="Use a custom command",
        options=[
            create_option(
                name="command_name", description="Use /showcustomcommands to see all available commands.",
                option_type=SlashCommandOptionType.STRING, required=True)], guild_ids=[GUILDID]
            )
    async def _custom(self, ctx: SlashContext, command_name: str):
        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()

            command_name = command_name.lower()
            c.execute(f'select * from {self.table_name} where command_name = ?', (command_name,))
            result = c.fetchone()

            if result is None:
                await ctx.send(f'Command "{command_name}" does not exist.', hidden=True)
                return

            command_response = result[1]
            await ctx.send(command_response)
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}', hidden=True)

    @cog_ext.cog_slash(name="addcommand", description="(STAFF) Add a custom command", guild_ids=[GUILDID],
        options=[
            create_option(
                name="command_name",
                description="Name of the command",
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name="command_response",
                description="Response of the command",
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ])
    async def addcommand(self, ctx: SlashContext, command_name: str, command_response: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()
            command_name = command_name.lower()
            c.execute(f'select * from {self.table_name} where command_name = ?', (command_name,))
            result = c.fetchone()

            if result is not None:
                await ctx.send(f'Command "{command_name}" already exists.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            command_response = command_response.replace('/n', '\n')
            c.execute(f'insert into {self.table_name} values (?, ?)', (command_name, command_response))
            conn.commit()
            conn.close()

            async def custom_command(ctx):
                await ctx.send(command_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))

            await ctx.send(f'Command "{command_name}" added successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @cog_ext.cog_slash(name="editcommand", description="(STAFF) Edit a custom command", guild_ids=[GUILDID],
        options=[
            create_option(
                name="command_name",
                description="Name of the command",
                option_type=SlashCommandOptionType.STRING,
                required=True
            ),
            create_option(
                name="new_response",
                description="New response of the command",
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ])
    async def editcommand(self, ctx: SlashContext, command_name: str, new_response: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()

            command_name = command_name.lower()
            c.execute(f'select * from {self.table_name} where command_name = ?', (command_name,))
            result = c.fetchone()

            if result is None:
                await ctx.send(f'Command "{command_name}" does not exist.')
                return

            new_response = new_response.replace('/n', '\n')
            c.execute(f'update {self.table_name} set command_response = ? where command_name = ?', (new_response, command_name))
            conn.commit()
            conn.close()

            self.bot.remove_command(command_name)

            async def custom_command(ctx):
                await ctx.send(new_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))

            await ctx.send(f'Command "{command_name}" updated successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @cog_ext.cog_slash(name="deletecommand", description="(STAFF) Delete a custom command", guild_ids=[GUILDID],
        options=[
            create_option(
                name="command_name",
                description="Name of the command",
                option_type=SlashCommandOptionType.STRING,
                required=True
            )
        ])
    async def deletecommand(self, ctx: SlashContext, command_name: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()
            command_name = command_name.lower()
            c.execute(f'select * from {self.table_name} where command_name = ?', (command_name,))
            result = c.fetchone()

            if result is None:
                await ctx.send(f'Command "{command_name}" does not exist.')
                return

            c.execute(f'delete from {self.table_name} where command_name = ?', (command_name,))
            conn.commit()
            conn.close()

            self.bot.remove_command(command_name)

            await ctx.send(f'Command "{command_name}" deleted successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(help="Shows the staff commands", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def staffcommands(self, ctx):
        bot_commands = self.bot.commands
        hidden_commands = [command for command in bot_commands if command.hidden and not any(check.__qualname__ == 'is_owner.<locals>.predicate' for check in command.checks)]

        embeds = self.create_embeds(hidden_commands)
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    def create_embeds(self, commands):
        embeds = []
        total_pages = (len(commands) + 24) // 25
        embed = discord.Embed(title="__**Staff Commands**__", description="*These are the available staff commands.*", color=discord.Color.green())
        no_help_commands = []

        for command in commands:
            if command.help is not None:
                embed.add_field(name=f"`{command.name}`", value=f"`{command.help}`", inline=True)
            else:
                no_help_commands.append(command)

            if len(embed.fields) == 25:
                embed.title = f"**Staff Commands - Page {len(embeds) + 1} of {total_pages}**"
                embed.set_footer(text="Use the reactions to navigate between pages.")
                embeds.append(embed)
                embed = discord.Embed(title="**Staff Commands**", color=discord.Color.random())

        for command in no_help_commands:
            if len(embed.fields) == 25:
                embed.title = f"**Staff Commands - Page {len(embeds) + 1} of {total_pages}**"
                embeds.append(embed)
                embed = discord.Embed(title="**Staff Commands**", color=discord.Color.random())
            embed.add_field(name=f"`{command.name}`", value="", inline=True)

        embed.title = f"**Staff Commands - Page {len(embeds) + 1} of {total_pages}**"
        embed.set_footer(text="Use the reactions to navigate between pages.")
        embeds.append(embed)
        return embeds

    @cog_ext.cog_slash(name="addlink", description="(STAFF) Adds a new allowed link",
        options=[create_option(name="link", description="The link to add", option_type=3, required=True)], guild_ids=[GUILDID])
    async def addlink(self, ctx: SlashContext, link: str):
        AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
        if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
            await ctx.send('You do not have permission to use this command.')
            return

        with open('Data/AllowedLinks.txt', 'a') as file:
            file.write(link + '\n')
        await ctx.send(f'Added {link} to the list of allowed links.')

    @cog_ext.cog_slash(name="showlinks", description="(STAFF) Shows all allowed links", guild_ids=[GUILDID], options=[])
    async def showlinks(self, ctx: SlashContext):
        AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
        if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
            await ctx.send('You do not have permission to use this command.')
            return

        if os.path.exists('Data/AllowedLinks.txt'):
            with open('Data/AllowedLinks.txt', 'r') as file:
                links = [line.strip() for line in file.readlines()]
        else:
            links = []

        chunks = [links[i:i + 10] for i in range(0, len(links), 10)]
        embeds = []
        for i, chunk in enumerate(chunks):
            description = "\n".join(f"{idx + 1}. {link}" for idx, link in enumerate(chunk))
            embed = discord.Embed(
                title=f"🔗 Allowed Links - Page {i + 1} 🔗",
                description=description,
                color=discord.Color.blue()
            )
            embed.set_author(name="God's Eye", icon_url=ctx.guild.me.avatar_url)
            embed.set_footer(text="Use the reactions to navigate between pages.")
            embeds.append(embed)

        paginator = Paginator(ctx, embeds)
        await paginator.start()

def setup(bot):
    bot.add_cog(CustomCommands(bot))
