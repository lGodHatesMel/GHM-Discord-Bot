import os
import discord
from discord.ext import commands
import datetime
import random
import utils


class POKEMON_COMMANDS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pokefacts', aliases=['pkf', 'funfact'], help='Get a random Pokémon fact.')
    async def pokefacts(self, ctx):
        # Select a random Pokémon fact from the list
        random_fact = utils.get_random_pokemon_fact()
        # Send the fact as a message
        await ctx.send(f'**Random Pokémon Fact:**\n{random_fact}')

    # @commands.command(name='requestlist', aliases=['rl'], help='Gives link for Special Request List.')
    # async def requestlist_link(self, ctx):
    #     requestlist_url = "https://docs.google.com/spreadsheets/d/1eP8sh8rtrB_1QY4Ti5muOf4uRXKzbF4fbU_58XiCoEs/edit?usp=sharing"
    #     await ctx.send(f"Heres a link to the special request list:\n{requestlist_url}")

    #     current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     author = ctx.message.author
    #     command = ctx.command.name
    #     print(f"{current_time} - {author.name} used the *{command}* command.")

    # @commands.command(name='raidsheet', aliases=['raidpokemon'], help='Gives link for all possible Raid Pokemon.')
    # async def raidsheet_link(self, ctx):
    #     raidsheet_url = "https://drive.google.com/drive/folders/1dWCQnNXs8JvCWh99PjU8s39aaa2m9l9N"
    #     await ctx.send(f"Here is the Raid Docs for all the possible raids you can pick from:\n{raidsheet_url}\n\nNote: You need the ID. So for example for the top right raid you would do `2addraid ID`")

    #     current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     author = ctx.message.author
    #     command = ctx.command.name
    #     print(f"{current_time} - {author.name} used the *{command}* command.")

    # @commands.command(name='tradecommands', help='Gives a list of trade commands')
    # async def tradecommands(self, ctx):
    #     trade_commands = "Here are the trade commands for the bots:"
    #     await ctx.send(f"{trade_commands}\nPokemon Scarlet Violet - `!svtrade`\nPokemon Sword Shield - `!swshtrade`\nPokemon Legends: Arceus - `!platrade`")

    #     current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     author = ctx.message.author
    #     command = ctx.command.name
    #     print(f"{current_time} - {author.name} used the *{command}* command.")

    @commands.command(aliases=['showdownset'], help='Usage: !showdown [Game: sv, swsh, pla, bdsp] <Pokemon Name>')
    async def showdown(self, ctx, game, pokemon_name):
        try:
            # Convert game and valid_games to lowercase
            game = game.lower()
            valid_games = ['sv', 'swsh', 'pla', 'bdsp']

            # Validate game to prevent directory traversal
            if game not in valid_games:
                await ctx.send(f"Invalid game '{game}'. Valid games are: {', '.join(valid_games)}")
                return

            # Convert Pokémon name to lowercase
            pokemon_name = pokemon_name.lower()

            # Get the path to the sets folder and the specific file
            sets_folder = os.path.join('sets', game)
            file_path = os.path.join(sets_folder, f"{pokemon_name}.txt")

            # Check if the file exists
            if not os.path.exists(file_path):
                await ctx.send(f"No sets found for {pokemon_name} [{game}].")
                return

            # Read sets from the file
            with open(file_path, 'r') as file:
                sets_data = file.read().split('===')

            # Filter out empty strings
            sets_data = [set_data.strip() for set_data in sets_data if set_data.strip()]

            if sets_data:
                random_set = random.choice(sets_data)
                await ctx.send(f"\n**Random set for {pokemon_name.capitalize()} [{game.upper()}]:**\n{random_set}\n")
            else:
                await ctx.send(f"No sets found for {pokemon_name.capitalize()} [{game.upper()}].")
        except Exception as e:
            print(e)
            await ctx.send("An error occurred while fetching Pokémon sets.")

    @commands.command(help='Game: <sv, swsh, pla, bdsp> <Pokemon Name> <ShowdownSet Details>')
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addset(self, ctx, game, pokemon_name, *set_details):
        try:
            # Convert game and valid_games to lowercase
            game = game.lower()
            valid_games = ['sv', 'swsh', 'pla', 'bdsp']

            # Validate game to prevent directory traversal
            if game not in valid_games:
                await ctx.send(f"Invalid game '{game}'. Valid games are: {', '.join(valid_games)}")
                return

            # Convert Pokémon name to lowercase
            pokemon_name = pokemon_name.lower()

            # Get the path to the sets folder and the specific file
            sets_folder = os.path.join('sets', game)
            file_path = os.path.join(sets_folder, f"{pokemon_name}.txt")

            formatted_set = utils.format_set_details(f"{' '.join(set_details)}")

            with open(file_path, 'a') as file:
                file.write(f"\n===\n{formatted_set}")

            await ctx.send(f"New set added for {pokemon_name.capitalize()} [{game.upper()}].")

        except Exception as e:
            print(e)
            await ctx.send("An error occurred while adding the set.")

def setup(bot):
    bot.add_cog(POKEMON_COMMANDS(bot))
