import discord
from discord.ext import commands
import os
import sqlite3
import asyncio
from utils.Paginator import Paginator

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'custom_commands.db')
        self.table_name = 'custom_commands'

        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute(f'''create table if not exists {self.table_name}
                (command_name text primary key,
                command_response text)''')
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
                    await ctx.message.reply(response)
                self.bot.add_command(commands.Command(custom_command, name=CommandName))
        except Exception as e:
            print(f'An error occurred while loading custom commands: {str(e)}')

    def RefreshCustomCommands(self):
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute(f'select * from {self.table_name}')
        CustomName = c.fetchall()
        conn.close()

        # Remove existing custom commands from the bot
        for command in self.bot.commands:
            if command.name in CustomName:
                self.bot.remove_command(command.name)

        # Register updated custom commands
        for CommandName, command_response in CustomName:
            async def custom_command(ctx, response=command_response):
                await ctx.message.reply(response)
            self.bot.add_command(commands.Command(custom_command, name=CommandName))

    @commands.command(help='Refresh custom commands', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def refreshcommands(self, ctx):
        try:
            self.RefreshCustomCommands()
            await ctx.message.reply('Custom commands refreshed successfully.')
        except Exception as e:
            await ctx.message.reply(f'An error occurred: {str(e)}')

    @commands.command(help='<command_name> <reply_message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addcommand(self, ctx, CommandName, *, command_response):
        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()

            CommandName = CommandName.lower()

            c.execute(f'select * from {self.table_name} where command_name = ?', (CommandName,))
            result = c.fetchone()

            if result is not None:
                await ctx.message.reply(f'Command "{CommandName}" already exists.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            command_response = command_response.replace('/n', '\n')

            c.execute(f'insert into {self.table_name} values (?, ?)', (CommandName, command_response))
            conn.commit()
            conn.close()

            async def custom_command(ctx):
                await ctx.semessage.replynd(command_response)
            self.bot.add_command(commands.Command(custom_command, name=CommandName))

            await ctx.message.reply(f'Command "{CommandName}" added successfully.')
        except Exception as e:
            await ctx.message.reply(f'An error occurred: {str(e)}')

    @commands.command(help='<command_name> <reply_message>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def editcommand(self, ctx, CommandName, *, new_response):
        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()

            CommandName = CommandName.lower()
            c.execute(f'select * from {self.table_name} where command_name = ?', (CommandName,))
            result = c.fetchone()

            if result is None:
                await ctx.message.reply(f'Command "{CommandName}" does not exist.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            new_response = new_response.replace('/n', '\n')
            c.execute(f'update {self.table_name} set command_response = ? where command_name = ?', (new_response, CommandName))
            conn.commit()
            conn.close()

            async def custom_command(ctx):
                await ctx.message.reply(new_response)
            self.bot.add_command(commands.Command(custom_command, name=CommandName))

            await ctx.message.reply(f'Command "{CommandName}" updated successfully.')
        except Exception as e:
            await ctx.message.reply(f'An error occurred: {str(e)}')

    @commands.command(help='<command_name>>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletecommand(self, ctx, CommandName):
        try:
            conn = sqlite3.connect(self.database_file)
            c = conn.cursor()
            CommandName = CommandName.lower()
            # Check if the command name exists in the table
            c.execute(f'select * from {self.table_name} where command_name = ?', (CommandName,))
            result = c.fetchone()

            if result is None:
                await ctx.send(f'Command "{CommandName}" does not exist.')
                return

            c.execute(f'delete from {self.table_name} where command_name = ?', (CommandName,))
            conn.commit()
            conn.close()

            self.bot.remove_command(CommandName)

            await ctx.message.reply(f'Command "{CommandName}" deleted successfully.')
        except Exception as e:
            await ctx.message.reply(f'An error occurred: {str(e)}')

    @commands.command(help="Shows the staff commands", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def staffcommands(self, ctx):
        bot_commands = self.bot.commands
        hidden_commands = [command for command in bot_commands if command.hidden and not any(check.__qualname__ == 'is_owner.<locals>.predicate' for check in command.checks)]

        embeds = self.create_embeds(hidden_commands)
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    def create_embeds(self, commands):
        """Creates embeds for the given commands."""
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

    @commands.command(hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addlink(self, ctx, link):
        with open('Data/AllowedLinks.txt', 'a') as file:
            file.write(link + '\n')
        await ctx.message.reply(f'Added {link} to the list of allowed links.')

    @commands.command(hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def showlinks(self, ctx):
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
