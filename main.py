import os
import discord
from discord import Embed
from discord.ext import commands
import json
import utils
import traceback

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

        embed = Embed(title="Server Bot Commands", color=discord.Color.blue())
        for cog, commands in mapping.items():
            if getattr(cog, "hidden", False):
                continue
            commands = [c for c in commands if not c.hidden]
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


intents = discord.Intents.default()
intents.members = True
intents.presences = True

def load_or_create_config():
    if os.path.exists('config.json'):
        print("config.json already exists.")
    else:
        default_config = {
            "token": "YOUR_TOKEN_HERE",
            "prefix": "!",
            "enable_countdown": False,
            "token_refresher_enabled": False,
            "countdown_channel_id": None,
            "target_timestamp": None,
            "welcome_channel_id": None,
            "rules_channel_id": None,
            "faq_channel_id": None,
            "info_channel_id": None,
            "message_logger_channel_id": None,
            "role_channel_id": None,
            "mod_logs_channel_id": None,
            "member_logs_channel_id": None,
            "server_logs_channel_id": None,
            "owner_id": "YOUR_OWNER_ID",
            "twitch_username": "YOUR_TWITCH_USERNAME",
            "twitch_client_id": "YOUR_TWITCH_CLIENT_ID",
            "youtube_channel_id": "YOUR_YOUTUBE_CHANNEL_ID",
            "youtube_channel_name": "YOUR_YOUTUBE_CHANNEL_NAME",
            "youtube_api_key": "YOUR_YOUTUBE_API_KEY",
            "stream_channel_id": "YOUR_DISCORD_CHANNEL_ID",
        }
        with open('config.json', 'w') as config_file:
            json.dump(default_config, config_file, indent=4)
        print("A new config.json file has been created with default values.")

    try:
        with open('config.json', 'r') as config_file:
            config = json.load(config_file)
            if config['owner_id'] is None:
                config['owner_id'] = int(input("Enter your owner ID: "))
                with open('config.json', 'w') as config_file:
                    json.dump(config, config_file, indent=4)
                    print("owner_id has been set in config.json.")
            return config
    except FileNotFoundError:
        print("Error: config.json file not found. Make sure the file exists.")
        exit(1)
    except json.JSONDecodeError:
        print("Error: Failed to parse config.json. Check the file's format.")
        exit(1)
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        exit(1)

config = load_or_create_config()

bot = commands.Bot(command_prefix=config['prefix'], case_insensitive=True, intents=intents, owner_ids=[config['owner_id']], help_command=EmbedHelpCommand())
bot.config = config

@bot.command(name='commands')
async def _commands(ctx, *args):
    await bot.get_command('help')(ctx, *args)

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

@bot.event
async def on_ready():
    joined_time = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')
    print(f'=======================================================')
    print(f'===   Bot Name: {bot.user.name}')
    print(f'===   Discord Server: {bot.guilds[0].name}')
    print(f'===   Bot UID: {bot.user.id}')
    print(f'===   Joined Server at: {joined_time}')
    print(f'=======================================================')

    print(f'Enabled Intents:')
    for intent, enabled in bot.intents:
        print(f'{intent}: {"Enabled" if enabled else "Disabled"}')
    print(f'===========================================================')

    stream_name = config['stream_name']
    stream_url = config['stream_url']
    await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(name=stream_name, url=stream_url))

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingAnyRole):
        await ctx.send('You do not have the correct permissions or roles to run this command.')
    elif isinstance(error, commands.NotOwner):
        await ctx.send('Only the owner of this bot can run this command.')
    else:
        tb_lines = traceback.format_exception(type(error), error, error.__traceback__)
        tb_text = ''.join(tb_lines)
        print(f'Error: {error}\n{tb_text}')

if __name__ == "__main__":
    try:
        bot.run(config['token'])
    except discord.LoginFailure:
        print("Error: Invalid bot token. Check your token configuration.")
    except discord.HTTPException as e:
        print(f"Error: Discord HTTP error - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
