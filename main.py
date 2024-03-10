#from bot import bot
from config import TOKEN, IGNORE_SCRIPTS, STREAM_NAME, STREAM_URL, PREFIX, ROLEIDS, GUILDID
import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.error import CheckFailure as SlashCheckFailure
import utils.utils as utils
from utils.Paginator import Paginator
import os
import traceback
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# class EmbedHelpCommand(commands.HelpCommand):
#     def __init__(self):
#         super().__init__()
#     def get_command_signature(self, command):
#         if command.help:
#             return '`!{} {}`'.format(command.qualified_name, command.help)
#         else:
#             return '`!{}`'.format(command.qualified_name)

#     async def send_bot_help(self, mapping):
#         ExcludeCommands = ['staffcommands', 'commands', 'help', 'ping', 'botping']
#         embeds = []
#         current_embed = discord.Embed(color=discord.Color.random())
#         current_count = 0
#         for cog, commands in mapping.items():
#             if getattr(cog, "hidden", False):
#                 continue
#             commands = [c for c in commands if not c.hidden and c.name not in ExcludeCommands]
#             if commands:
#                 cog_name = getattr(cog, "qualified_name", "Other Commands")
#                 field_value = ""
#                 for command in commands:
#                     signature = self.get_command_signature(command)
#                     field_value += signature + "\n"
#                     current_count += 1
#                     if current_count == 9:
#                         current_embed.add_field(name=f"{cog_name}", value=field_value, inline=True)
#                         current_embed.title = f"**Server Commands - Page {len(embeds) + 1}**"
#                         embeds.append(current_embed)
#                         current_embed = discord.Embed(color=discord.Color.random())
#                         current_count = 0
#                         field_value = ""
#                 if field_value:
#                     current_embed.add_field(name=f"{cog_name}", value=field_value, inline=True)
#                 current_embed.set_footer(text="Use the reactions to navigate between pages.")
#         if len(current_embed.fields) > 0:
#             current_embed.set_footer(text="Use the reactions to navigate between pages.")
#             current_embed.title = f"**Server Commands - Page {len(embeds) + 1}**"
#             embeds.append(current_embed)
#         paginator = Paginator(self.context, embeds)
#         await paginator.start()

## Bot Setup
bot = commands.Bot(
    command_prefix=PREFIX,
    case_insensitive=True,
    intents = discord.Intents.all(),
    owner_ids=[ROLEIDS["OWNERID"]],
    # help_command=EmbedHelpCommand(),
    description="Custom bot for our Discord server."
)
slash = SlashCommand(bot, sync_commands=True)


# @bot.command(name='commands')
# async def _commands(ctx, *args):
#     try:
#         await ctx.send_help(*args)
#     except Exception as e:
#         logging.error(f"An error occurred while sending help: {e}")


## Run scripts from folders
folders = ['cogs']
for folder in folders:
    for filename in os.listdir(folder):
        if filename.endswith('.py'):
            script_name = filename[:-3]
            if script_name in IGNORE_SCRIPTS:
                logging.info(f'Ignored extension: {folder}.{script_name}')
                continue
            try:
                extension = f'{folder}.{script_name}'
                bot.load_extension(extension)
                logging.info(f'Loaded extension: {extension}')
            except Exception as e:
                logging.error(f'Failed to load extension {extension}: {str(e)}')


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
    print('Enabled Intents:')
    intents = [
        'messages', 'reactions', 'members', 'guilds', 'emojis', 'integrations', 
        'webhooks', 'invites', 'voice_states', 'presences', 'guild_messages', 
        'dm_messages', 'guild_reactions', 'dm_reactions', 'guild_typing', 'dm_typing'
    ]
    for intent in intents:
        enabled = getattr(bot.intents, intent)
        print(f'{intent}: {"Enabled" if enabled else "Disabled"}')
    # print(bot.intents)
    print(f'=====================================================')
    print(f'Number of slash commands: {len(slash.commands)}')
    print('Slash commands:')
    for i, (command_name, command) in enumerate(slash.commands.items(), start=1):
        print(f'{i}. {command_name}')
    await bot.change_presence(status=discord.Status.online, activity=discord.Streaming(name=STREAM_NAME, url=STREAM_URL))

@bot.event
async def on_disconnect():
    print("Bot has disconnected.")
    await slash.remove_all_commands(guild_id=GUILDID)

@bot.event
async def on_command_error(ctx, error):
    error = getattr(error, 'original', error)
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingPermissions) or isinstance(error, commands.MissingAnyRole):
        await ctx.send('You do not have the correct permissions or roles to run this command.')
    elif isinstance(error, commands.NotOwner):
        await ctx.send('Only the owner of this bot can run this command.')
    elif isinstance(error, commands.CheckFailure) or isinstance(error, SlashCheckFailure):
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
        logging.error(f'Error: {error}\n{tb_text}')
        await ctx.send("An unexpected error occurred. Please try again later.")


## Run the bot
if __name__ == "__main__":
    try:
        bot.run(TOKEN)
    except discord.LoginFailure:
        logging.error("Error: Invalid bot token. Check your token configuration.")
    except discord.HTTPException as e:
        logging.error(f"Error: Discord HTTP error - {e}")
    except discord.PrivilegedIntentsRequired:
        logging.error("Error: The bot is missing one or more of the privileged intents.")
    except discord.ConnectionClosed as e:
        logging.error(f"Error: The gateway connection is closed. Reason: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")