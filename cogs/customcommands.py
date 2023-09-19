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

    @commands.command(name='addcommand')
    async def add_custom_command(self, ctx, command_name, *, command_response):
        try:
            # Load existing custom commands from JSON
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            # Convert the command_name to lowercase
            command_name = command_name.lower()

            # Check if the command name already exists
            if command_name in custom_commands:
                await ctx.send(f'Command "{command_name}" already exists.')
                return

            # Add the new custom command
            custom_commands[command_name] = command_response

            # Save the updated custom commands to JSON
            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            # Register the new custom command with the bot
            async def custom_command(ctx):
                await ctx.send(command_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))

            await ctx.send(f'Command "{command_name}" added successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name='editcommand')
    async def edit_custom_command(self, ctx, command_name, *, new_response):
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

            # Update the custom command response
            custom_commands[command_name] = new_response

            # Save the updated custom commands to JSON
            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            # Update the custom command function
            async def custom_command(ctx):
                await ctx.send(new_response)
            self.bot.add_command(commands.Command(custom_command, name=command_name))

            await ctx.send(f'Command "{command_name}" updated successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name='delcommand')
    async def delete_custom_command(self, ctx, command_name):
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

            # Remove the custom command
            del custom_commands[command_name]

            # Save the updated custom commands to JSON
            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            # Unregister the custom command from the bot
            self.bot.remove_command(command_name)

            await ctx.send(f'Command "{command_name}" deleted successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

def setup(bot):
    bot.add_cog(CustomCommands(bot))
