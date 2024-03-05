import os
import traceback
from bot import bot
from config import IgnoreScripts, stream_name, stream_url, token
import discord
from discord.ext import commands
import utils.utils as utils

## Run scripts from folders
folders = ['cogs']
for folder in folders:
    for filename in os.listdir(folder):
        if filename.endswith('.py'):
            script_name = filename[:-3]
            if script_name in IgnoreScripts:
                print(f'Ignored extension: {folder}.{script_name}')
                continue
            try:
                extension = f'{folder}.{script_name}'
                bot.load_extension(extension)
                print(f'Loaded extension: {extension}')
            except Exception as e:
                print(f'Failed to load extension {extension}: {str(e)}')
                traceback.print_exc()

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
    for intent, enabled in bot.intents.to_dict().items():
        print(f'{intent}: {"Enabled" if enabled else "Disabled"}')
    print(f'=====================================================')
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
        await ctx.send("An unexpected error occurred. Please try again later.")

## Run the bot
if __name__ == "__main__":
    try:
        bot.run(token)
    except discord.LoginFailure:
        print("Error: Invalid bot token. Check your token configuration.")
    except discord.HTTPException as e:
        print(f"Error: Discord HTTP error - {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")