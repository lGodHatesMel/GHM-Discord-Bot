import os
import discord
from discord.ext import commands
import json
import utils

intents = discord.Intents.default()
intents.members = True
intents.presences = True

bot = commands.Bot(command_prefix="!", case_insensitive=True, intents=intents, owner_ids=[613167456814628884])

def load_or_create_config(bot):
    if hasattr(bot, 'config'):
        return bot.config

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
            "server_logs_channel_id": None
        }
        with open('config.json', 'w') as config_file:
            json.dump(default_config, config_file, indent=4)
        print("A new config.json file has been created with default values.")

    with open('config.json', 'r') as config_file:
        config = json.load(config_file)
        bot.config = config

        if config['welcome_channel_id'] is None:
            config['welcome_channel_id'] = int(input("Enter the welcome channel ID: "))
            with open('config.json', 'w') as config_file:
                json.dump(config, config_file, indent=4)
                print("welcome_channel_id has been set in config.json")

        if config['faq_channel_id'] is None:
            config['faq_channel_id'] = int(input("Enter the FAQ channel ID: "))
            with open('config.json', 'w') as config_file:
                json.dump(config, config_file, indent=4)
                print("⚠ WARNING: 'faq_channel_id' is not set in config.json.")

        return config

config = load_or_create_config(bot)

# Dynamically load all .py files in the cogs directory
for filename in os.listdir('cogs'):
    if filename.endswith('.py'):
        try:
            extension = f'cogs.{filename[:-3]}'  # Remove the .py extension and prepend 'cogs.'
            bot.load_extension(extension)
            print(f'Loaded extension: {extension}')
        except Exception as e:
            print(f'Failed to load extension {extension}: {str(e)}')

@bot.event
async def on_ready():
    print(f'===========================================================')
    print(f'Bot Name: {bot.user.name}')
    print(f'Discord Server Joined: {bot.guilds[0].name}')
    print(f'Bot UID: {bot.user.id}')
    print(f'===========================================================')

    print(f'Enabled Intents:')
    for intent, enabled in bot.intents:
        print(f'{intent}: {"Enabled" if enabled else "Disabled"}')
    print(f'===========================================================')

    # Check if the bot is a member of any servers
    if len(bot.guilds) > 0:
        joined_server = bot.guilds[0]  # Assuming the bot is only in one server
        joined_time = utils.get_local_time()
        print(f'Joined Server at: {joined_time}')
    print(f'===========================================================')
    
    await bot.change_presence(status=discord.Status.online, activity=discord.Game("OOHHH YEEAAAHHHH!!!"))

bot.run(config['token'])