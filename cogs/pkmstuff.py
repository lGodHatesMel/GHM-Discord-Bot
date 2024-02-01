import os
import discord
from discord.ext import commands
import random
import requests
import io
import utils

class POKEMON_COMMANDS(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pokefacts', aliases=['pkf', 'funfact'], help='Get a random Pokémon fact.')
    async def pokefacts(self, ctx):
        try:
            random_fact = utils.get_random_pokemon_fact()
            github_api_link = "https://api.github.com/repos/lGodHatesMel/Pokemon-Data/contents/PokemonImages/Sprites/AlternateArt"

            embed = discord.Embed(
                title="**__Random Pokémon Fact__**",
                description=random_fact,
                color=discord.Color.random()
            )

            response = requests.get(github_api_link)
            if response.status_code == 200:
                data = response.json()
                image_filenames = [file['name'] for file in data if file['type'] == 'file' and file['name'].endswith('.png')]

                random_image_filename = random.choice(image_filenames)
                image_url = f"https://raw.githubusercontent.com/lGodHatesMel/Pokemon-Data/main/PokemonImages/Sprites/AlternateArt/{random_image_filename}"

                embed.set_image(url=image_url)
                await ctx.send(embed=embed)
            else:
                await ctx.send("Failed to fetch file list from GitHub.")
        except Exception as e:
            print(e)
            await ctx.send("An error occurred while fetching Pokémon facts.")

    @commands.command(aliases=['showdownset'], help='Usage: !showdown [Game: sv, swsh, pla, bdsp] <Pokemon Name>')
    async def showdown(self, ctx, game, pokemon_name):
        try:
            game = game.lower()
            valid_games = ['sv', 'swsh', 'pla', 'bdsp']

            if game not in valid_games:
                await ctx.send(f"Invalid game '{game}'. Valid games are: {', '.join(valid_games)}")
                return

            pokemon_name = pokemon_name.lower()
            sets_folder = os.path.join('sets', game)
            file_path = os.path.join(sets_folder, f"{pokemon_name}.txt")

            if not os.path.exists(file_path):
                await ctx.send(f"No sets found for {pokemon_name} [{game}].")
                return

            with open(file_path, 'r') as file:
                sets_data = file.read().split('===')

            sets_data = [set_data.strip() for set_data in sets_data if set_data.strip()]

            if sets_data:
                random_set = random.choice(sets_data)
                embed = discord.Embed(
                    title=f"Random set for {pokemon_name.capitalize()} [{game.upper()}]",
                    description=random_set,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No sets found for {pokemon_name.capitalize()} [{game.upper()}].")
        except Exception as e:
            print(e)
            await ctx.send("An error occurred while fetching Pokémon sets.")

    @commands.command(help='Game: <sv, swsh, pla, bdsp> <Pokemon Name> <ShowdownSet Details>')
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addset(self, ctx, game, pokemon_name, *set_details):
        try:
            game = game.lower()
            valid_games = ['sv', 'swsh', 'pla', 'bdsp']

            if game not in valid_games:
                await ctx.send(f"Invalid game '{game}'. Valid games are: {', '.join(valid_games)}")
                return

            pokemon_name = pokemon_name.lower()
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