import os
import discord
from discord.ext import commands
import json
import utils

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
            "countdown_channel_id": None,
            "target_timestamp": None,
            "welcome_channel_id": None,
            "rules_channel_id": None,
            "faq_channel_id": None,
            "message_logger_channel_id": None,
            "role_channel_id": None,
            "mod_logs_channel_id": None,
            "member_logs_channel_id": None,
            "server_logs_channel_id": None,
            "owner_id": 123456789012345678
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

bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents, owner_ids=config['owner_id'])

for filename in os.listdir('cogs'):
    if filename.endswith('.py'):
        try:
            extension = f'cogs.{filename[:-3]}'
            bot.load_extension(extension)
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}: {str(e)}')

@bot.event
async def on_ready():
    joined_time = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')
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

    await bot.change_presence(status=discord.Status.online, activity=discord.Game("OOHHH YEEAAAHHHH!!!"))

if __name__ == "__main__":
    try:
        bot.run(config['token'])
    except discord.LoginFailure:
        print("Error: Invalid bot token. Check your token configuration.")
    except discord.HTTPException as e:
        print(f"Error: Discord HTTP error - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")