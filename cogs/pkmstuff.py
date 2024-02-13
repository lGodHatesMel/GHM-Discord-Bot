import os
import discord
from discord.ext import commands
import random
import requests
import io
import utils

class PKMStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['pkf', 'funfact'], help='Get a random Pokémon fact.')
    async def pokefacts(self, ctx):
        try:
            RandomFact = utils.RandomPKMFacts()
            GithubAPILink = "https://api.github.com/repos/lGodHatesMel/Pokemon-Data/contents/PokemonImages/Sprites/AlternateArt"

            embed = discord.Embed(
                title="**__Random Pokémon Fact__**",
                description=RandomFact,
                color=discord.Color.random()
            )

            response = requests.get(GithubAPILink)
            if response.status_code == 200:
                data = response.json()
                image_filenames = [file['name'] for file in data if file['type'] == 'file' and file['name'].endswith('.png')]

                RandomImage = random.choice(image_filenames)
                ImageURL = f"https://raw.githubusercontent.com/lGodHatesMel/Pokemon-Data/main/PokemonImages/Sprites/AlternateArt/{RandomImage}"

                embed.set_image(url=ImageURL)
                await ctx.send(embed=embed)
            else:
                await ctx.send("Failed to fetch file list from GitHub.")
        except Exception as e:
            print(e)
            await ctx.send("An error occurred while fetching Pokémon facts.")

    @commands.command(aliases=['showdownset'], help='[Game: sv, swsh, pla, bdsp] <Pokemon Name>')
    async def showdown(self, ctx, game, PokemonName):
        try:
            game = game.lower()
            ValidGames = ['sv', 'swsh', 'pla', 'bdsp']

            if game not in ValidGames:
                await ctx.send(f"Invalid game '{game}'. Valid games are: {', '.join(ValidGames)}")
                return

            PokemonName = PokemonName.lower()
            SetsFolder = os.path.join('sets', game)
            file_path = os.path.join(SetsFolder, f"{PokemonName}.txt")

            if not os.path.exists(file_path):
                await ctx.send(f"No sets found for {PokemonName} [{game}].")
                return

            with open(file_path, 'r') as file:
                DataSets = file.read().split('===')

            DataSets = [set_data.strip() for set_data in DataSets if set_data.strip()]

            if DataSets:
                RandomSet = random.choice(DataSets)
                embed = discord.Embed(
                    title=f"Random set for {PokemonName.capitalize()} [{game.upper()}]",
                    description=RandomSet,
                    color=discord.Color.blue()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send(f"No sets found for {PokemonName.capitalize()} [{game.upper()}].")
        except Exception as e:
            print(e)
            await ctx.send("An error occurred while fetching Pokémon sets.")

    @commands.command(help='Game: <sv, swsh, pla, bdsp> <Pokemon Name> <ShowdownSet Details>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addset(self, ctx, game, PokemonName, *SetDetails):
        try:
            game = game.lower()
            ValidGames = ['sv', 'swsh', 'pla', 'bdsp']

            if game not in ValidGames:
                await ctx.send(f"Invalid game '{game}'. Valid games are: {', '.join(ValidGames)}")
                return

            PokemonName = PokemonName.lower()
            SetsFolder = os.path.join('sets', game)
            file_path = os.path.join(SetsFolder, f"{PokemonName}.txt")
            FormatedSet = utils.FormatedSetDetails(f"{' '.join(SetDetails)}")

            with open(file_path, 'a') as file:
                file.write(f"\n===\n{FormatedSet}")

            await ctx.send(f"New set added for {PokemonName.capitalize()} [{game.upper()}].")

        except Exception as e:
            print(e)
            await ctx.send("An error occurred while adding the set.")

def setup(bot):
    bot.add_cog(PKMStuff(bot))