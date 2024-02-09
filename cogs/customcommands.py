import discord
from discord.ext import commands
import json
import os

class CustomCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.database_folder = 'Database'
        self.commands_file = os.path.join(self.database_folder, 'custom_commands.json')

        if not os.path.exists(self.commands_file):
            with open(self.commands_file, 'w') as file:
                json.dump({}, file)
        self.LoadCustomCommands()

    def LoadCustomCommands(self):
        try:
            with open(self.commands_file, 'r') as file:
                CustomName = json.load(file)

            for CommandName, command_response in CustomName.items():
                async def custom_command(ctx, response=command_response):
                    await ctx.send(response)

                self.bot.add_command(commands.Command(custom_command, name=CommandName))

        except Exception as e:
            print(f'An error occurred while loading custom commands: {str(e)}')

    def RefreshCustomCommands(self):
        with open(self.commands_file, 'r') as file:
            CustomName = json.load(file)

        # Remove existing custom commands from the bot
        for command in self.bot.commands:
            if command.name in CustomName:
                self.bot.remove_command(command.name)

        # Register updated custom commands
        for CommandName, command_response in CustomName.items():
            # Dynamically create a function for each custom command
            async def custom_command(ctx, response=command_response):
                await ctx.send(response)

            self.bot.add_command(commands.Command(custom_command, name=CommandName))

    @commands.command(help='Refresh custom commands from the JSON file', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def refreshcommands(self, ctx):
        try:
            self.RefreshCustomCommands()
            await ctx.send('Custom commands refreshed successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(help='<command_name> <reply_message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addcommand(self, ctx, CommandName, *, command_response):
        try:
            with open(self.commands_file, 'r') as file:
                CustomName = json.load(file)

            CommandName = CommandName.lower()

            if CommandName in CustomName:
                await ctx.send(f'Command "{CommandName}" already exists.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            command_response = command_response.replace('/n', '\n')
            CustomName[CommandName] = command_response

            with open(self.commands_file, 'w') as file:
                json.dump(CustomName, file, indent=4)

            async def custom_command(ctx):
                await ctx.send(command_response)
            self.bot.add_command(commands.Command(custom_command, name=CommandName))

            await ctx.send(f'Command "{CommandName}" added successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(help='<command_name> <reply_message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def editcommand(self, ctx, CommandName, *, new_response):
        try:
            with open(self.commands_file, 'r') as file:
                CustomName = json.load(file)

            CommandName = CommandName.lower()

            if CommandName not in CustomName:
                await ctx.send(f'Command "{CommandName}" does not exist.')
                return

            # Replace '/n' with '\n' to correctly interpret newlines
            new_response = new_response.replace('/n', '\n')
            CustomName[CommandName] = new_response

            with open(self.commands_file, 'w') as file:
                json.dump(CustomName, file, indent=4)

            # Update the existing command with the new response
            async def custom_command(ctx):
                await ctx.send(new_response)
            self.bot.add_command(commands.Command(custom_command, name=CommandName))

            await ctx.send(f'Command "{CommandName}" updated successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(aliases=['delcommand', 'delcmd'], help='<command_name>>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletecommand(self, ctx, CommandName):
        try:
            with open(self.commands_file, 'r') as file:
                CustomName = json.load(file)
            CommandName = CommandName.lower()
            # Check if the command name exists
            if CommandName not in CustomName:
                await ctx.send(f'Command "{CommandName}" does not exist.')
                return

            del CustomName[CommandName]

            with open(self.commands_file, 'w') as file:
                json.dump(CustomName, file, indent=4)

            self.bot.remove_command(CommandName)

            await ctx.send(f'Command "{CommandName}" deleted successfully.')
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')
            
    @commands.command(aliases=['modcommands'], help='Display the staff command list')
    @commands.has_any_role("Moderator", "Admin")
    async def staffcommands(self, ctx):
        embed = discord.Embed(
            title='**__Staff Command List__**',
            description='*Here are the staff commands:*',
            color=discord.Color.random()
        )
        embed.add_field(
            name='User Database:',
            value=(
                "`!adduser <uid>` - Add a user to the database.\n"
                "`!updateinfo <uid> <key> <value>` - Update user information."
            ),
            inline=False
        )
        embed.add_field(
            name='Info:',
            value='`!info <uid>` - Retrieve user information.',
            inline=False
        )
        embed.add_field(
            name='Bans:',
            value=(
                "`!ban <uid> <reason>` - Ban a user.\n"
                "`!unban <uid> <reason>` - Unban a user.\n"
                "`!checkbans <uid>` - Check a user's bans."
            ),
            inline=False
        )
        embed.add_field(
            name='SoftBan:',
            value=(
                "`!softban <uid> <reason>` - SoftBan a user"
            ),
            inline=False
        )
        embed.add_field(
            name='Notes:',
            value=(
                "`!addnote <uid> <message>` - Add a note for a user.\n"
                "`!removenote <uid> <note#> <message>` - Remove a user's note.\n"
                "`!notes <uid> <note#>` - View a user's notes."
            ),
            inline=False
        )
        embed.add_field(
            name='Warnings:',
            value=(
                "`!addwarning <uid> <reason>` - Add a warning for a user.\n"
                "`!removewarning <uid> <warning#> <reason>` - Remove a user's warning.\n"
                "`!checkwarning <uid> <warning#>` - View a user's warnings."
            ),
            inline=False
        )
        embed.add_field(
            name='Kicks:',
            value='`!kick <uid> <reason>` - Kick a user.',
            inline=False
        )
        embed.add_field(
            name='Others:',
            value=(
                "`!botdown <channel> <message>` - Send a bot down message.\n"
                "`!announcement <channel> <message>` - Send an announcement.\n"
                "`!addsticky <channel> <message>` - Add a sticky note.\n"
                "`!removesticky <channel>` - Remove a sticky note.\n"
                "`!addcommand <command_name> <respond_message>` - Add's a custom command.\n"
                "`!togglechannel <channel> <role> <permission_name>` - Permission names: `send_messages` or `read_messages`\n"
                "`!efreshcommands` - Refreshes the custom_commands.json.\n"
                "`!merge <width> <height> <save_name>` - Merges multiple attached images into one.\n"
                "`!poll \"Poll Title\" \"option1\" \"option2\" <add_more_if_needed> \"Your Message Here\"` - Creates a poll.\n"
            ),
            inline=False
        )
        embed.add_field(name='\u200b', value='\u200b', inline=False)
        embed.set_footer(
        text="Note: If you use a command and it says 'User not in database', "
            "use the `!adduser <uid>` command to add them first, "
            "and then use the other command."
    )

        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(CustomCommands(bot))
