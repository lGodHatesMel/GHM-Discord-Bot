import discord
from discord.ext import commands
import json
import os

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.commands_file = os.path.join(self.database_folder, 'custom_commands.json')

        # Check if the custom_commands.json file exists, and create it if not
        if not os.path.exists(self.commands_file):
            with open(self.commands_file, 'w') as file:
                json.dump({}, file)

        # Load custom commands when the bot starts
        self.load_custom_commands()

    def load_custom_commands(self):
        try:
            # Load existing custom commands from JSON
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            # Register each custom command with the bot
            for command_name, command_response in custom_commands.items():
                # Create a new custom command function
                async def custom_command(ctx):
                    await ctx.send(command_response)

                # Register the custom command with the bot
                self.bot.add_command(commands.Command(custom_command, name=command_name))

        except Exception as e:
            print(f'An error occurred while loading custom commands: {str(e)}')

    @commands.command(help='<CommandName> <Reply Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addcommand(self, ctx, command_name, *, command_response):
        try:
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            command_name = command_name.lower()

            if command_name in custom_commands:
                await ctx.send(f'Command "{command_name}" already exists.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            command_response = command_response.replace('/n', '\n')

            custom_commands[command_name] = command_response

            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            async def custom_command(ctx):
                await ctx.send(command_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))

            await ctx.send(f'Command "{command_name}" added successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(help='<CommandName> <Reply Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def editcommand(self, ctx, command_name, *, new_response):
        try:
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            command_name = command_name.lower()

            if command_name not in custom_commands:
                await ctx.send(f'Command "{command_name}" does not exist.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            new_response = new_response.replace('/n', '\n')

            custom_commands[command_name] = new_response

            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            # Update the existing command with the new response
            async def custom_command(ctx):
                await ctx.send(new_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))

            await ctx.send(f'Command "{command_name}" updated successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(aliases=['delcommand', 'delcmd'], help='<CommandName>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletecommand(self, ctx, command_name):
        try:
            # Load existing custom commands from JSON
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            # Convert the command_name to lowercase
            command_name = command_name.lower()

            # Check if the command name exists
            if command_name not in custom_commands:
                await ctx.send(f'Command "{command_name}" does not exist.')
                return

            del custom_commands[command_name]

            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            self.bot.remove_command(command_name)

            await ctx.send(f'Command "{command_name}" deleted successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

def setup(bot):
    bot.add_cog(CustomCommands(bot))
