import discord
from discord.ext import commands
import json
import os

#script_directory = os.path.dirname('GHM-Discord-Bot')
#custom_commands_file = os.path.join(script_directory, 'Database', 'custom_commands.json')

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.commands_file = os.path.join(self.database_folder, 'custom_commands.json')
        #self.commands_file = custom_commands_file

        # Check if the custom_commands.json file exists, and create it if not
        if not os.path.exists(self.commands_file):
            with open(self.commands_file, 'w') as file:
                json.dump({}, file)

    @commands.command(name='addcommand')
    async def add_custom_command(self, ctx, command_name, *, command_response):
        try:
            # Load existing custom commands from JSON
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            # Check if the command name already exists
            if command_name in custom_commands:
                await ctx.send(f'Command "{command_name}" already exists.')
                return

            # Add the new custom command
            custom_commands[command_name] = command_response

            # Save the updated custom commands to JSON
            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            await ctx.send(f'Command "{command_name}" added successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name='editcommand')
    async def edit_custom_command(self, ctx, command_name, *, new_response):
        try:
            # Load existing custom commands from JSON
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            # Check if the command name exists
            if command_name not in custom_commands:
                await ctx.send(f'Command "{command_name}" does not exist.')
                return

            # Update the custom command response
            custom_commands[command_name] = new_response

            # Save the updated custom commands to JSON
            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            await ctx.send(f'Command "{command_name}" updated successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(name='delcommand')
    async def delete_custom_command(self, ctx, command_name):
        try:
            # Load existing custom commands from JSON
            with open(self.commands_file, 'r') as file:
                custom_commands = json.load(file)

            # Check if the command name exists
            if command_name not in custom_commands:
                await ctx.send(f'Command "{command_name}" does not exist.')
                return

            # Remove the custom command
            del custom_commands[command_name]

            # Save the updated custom commands to JSON
            with open(self.commands_file, 'w') as file:
                json.dump(custom_commands, file, indent=4)

            await ctx.send(f'Command "{command_name}" deleted successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

def setup(bot):
    bot.add_cog(CustomCommands(bot))