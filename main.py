import os
# os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
import discord
from discord import Embed
from discord.ext import commands
import json
import utils
import traceback
# import logging
# logging.basicConfig(level=logging.INFO)


## Intents
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.dm_messages = True
#intents.dm_reactions = True
# intents.typing = True


## Custom Help Command
class EmbedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()

    def get_command_signature(self, command):
        if command.help:
            return '`!{} {}`'.format(command.qualified_name, command.help)
        else:
            return '`!{}`'.format(command.qualified_name)

    async def send_bot_help(self, mapping):
        with open('config.json') as f:
            config = json.load(f)

        ExcludeCommands = ['staffcommands', 'commands', 'help', 'ping', 'botping']

        embed = Embed(title="Server Bot Commands", color=discord.Color.blue())
        for cog, commands in mapping.items():
            if getattr(cog, "hidden", False):
                continue
            commands = [c for c in commands if not c.hidden and c.name not in ExcludeCommands]
            command_signatures = [self.get_command_signature(c) for c in commands]
            if command_signatures:
                cog_name = getattr(cog, "qualified_name", "Other Commands")
                signatures = "\n".join(command_signatures)
                # Split signatures into chunks of 1024 characters or less
                for i in range(0, len(signatures), 1024):
                    chunk = signatures[i:i+1024]
                    embed.add_field(name=f"{cog_name}", value=chunk, inline=False)

        logo_url = config['logo_url']
        embed.set_thumbnail(url=logo_url)
        channel = self.get_destination()
        await channel.send(embed=embed)


## Bot Setup
try:
    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        if config['owner_id'] is None:
            config['owner_id'] = int(input("Enter your owner ID: "))
            with open('config.json', 'w') as config_file:
                json.dump(config, config_file, indent=4)
                print("owner_id has been set in config.json.")
except FileNotFoundError:
    print("Error: config.json file not found. Make sure the file exists.")
    exit(1)
except json.JSONDecodeError:
    print("Error: Failed to parse config.json. Check the file's format.")
    exit(1)
except Exception as e:
    print(f"An unexpected error occurred: {e}")
    exit(1)

bot = commands.Bot(
    command_prefix=config['prefix'],
    case_insensitive=True,
    intents=intents,
    owner_ids=[config['owner_id']],
    help_command=EmbedHelpCommand(),
    description="Custom bot for our Discord server."
)
bot.config = config


## Commands
@bot.command(name='commands')
async def _commands(ctx, *args):
    await ctx.send_help(*args)


## Load Cogs
folders = ['cogs']
for folder in folders:
    for filename in os.listdir(folder):
        if filename.endswith('.py'):
            try:
                extension = f'{folder}.{filename[:-3]}'
                bot.load_extension(extension)
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {str(e)}')


## Events
@bot.event
async def on_ready():
    joined_time = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
    print(f'=====================================================')
    print(f'===   Bot Name: {bot.user.name}')
    print(f'===   Discord Server: {bot.guilds[0].name}')
    print(f'===   Bot UID: {bot.user.id}')
    print(f'===   Joined Server at: {joined_time}')
    print(f'=====================================================')

    print(f'Enabled Intents:')
    for intent, enabled in bot.intents:
        print(f'{intent}: {"Enabled" if enabled else "Disabled"}')
    print(f'=====================================================')

    stream_name = config['stream_name']
    stream_url = config['stream_url']
    await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(name=stream_name, url=stream_url))

@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, 'original', error)

    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingAnyRole):
        await ctx.send('You do not have the correct permissions or roles to run this command.')
    elif isinstance(error, commands.NotOwner):
        await ctx.send('Only the owner of this bot can run this command.')
    elif isinstance(error, commands.CheckFailure):
        await ctx.send(f"{ctx.message.author.mention} You don't have permission to use this command.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{ctx.message.author.mention} You are missing required arguments.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("⚠ I don't have the permissions to do this.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"{ctx.message.author.mention} One or more arguments are invalid.")
    else:
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_text = ''.join(tb_lines)
        print(f'Error: {error}\n{tb_text}')

# @bot.event
# async def on_typing(channel, user, when):
#     print(f"{user.name} started typing in {channel.name} at {when}")


## Run the bot
if __name__ == "__main__":
    try:
        bot.run(config['token'])
    except discord.LoginFailure:
        print("Error: Invalid bot token. Check your token configuration.")
    except discord.HTTPException as e:
        print(f"Error: Discord HTTP error - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")