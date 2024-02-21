import os
import discord
from discord.ext import commands
import random
import requests
import utils
import logging

ValidGames = ['sv', 'swsh', 'pla', 'bdsp']
ImageLink = "https://api.github.com/repos/lGodHatesMel/Pokemon-Data/contents/PokemonImages/Sprites/AlternateArt"

class PKMStuff(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def GetFilePath(self, game, PokemonName):
        """Validate the game and get the file path for the Pokemon sets."""
        game = game.lower()

        if game not in ValidGames:
            raise ValueError(f"Invalid game '{game}'. Valid games are: {', '.join(ValidGames)}")

        PokemonName = PokemonName.lower()
        SetsFolder = os.path.join('sets', game)
        return os.path.join(SetsFolder, f"{PokemonName}.txt")

    @commands.command(help='Get a random Pokémon fact.')
    async def pokefacts(self, ctx):
        try:
            RandomFact = utils.RandomPKMFacts()
            response = requests.get(ImageLink)
            if response.status_code == 200:
                data = response.json()
                image_filenames = [file['name'] for file in data if file['type'] == 'file' and file['name'].endswith('.png')]

                RandomImage = random.choice(image_filenames)
                ImageURL = f"https://raw.githubusercontent.com/lGodHatesMel/Pokemon-Data/main/PokemonImages/Sprites/AlternateArt/{RandomImage}"

                embed = discord.Embed(
                    title="**__Random Pokémon Fact__**",
                    description=RandomFact,
                    color=discord.Color.random()
                )
                embed.set_image(url=ImageURL)
                await ctx.send(embed=embed)
            else:
                await ctx.send("Failed to fetch file list from GitHub.")
        except Exception as e:
            logging.error(e)
            await ctx.send("An error occurred while fetching Pokémon facts.")

    @commands.command(aliases=['showdownset'], help='<Game: sv, swsh, pla, bdsp> <Pokemon Name>')
    async def showdown(self, ctx, game, PokemonName):
        try:
            file_path = self.GetFilePath(game, PokemonName)
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
        except ValueError as e:
            await ctx.send(str(e))
        except Exception as e:
            logging.error(e)
            await ctx.send("An error occurred while fetching Pokémon sets.")

    @commands.command(help='<Game: sv, swsh, pla, bdsp> <PokemonName> <ShowdownSetDetails>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addset(self, ctx, game, PokemonName, *SetDetails):
        try:
            file_path = self.GetFilePath(game, PokemonName)
            FormatedSet = utils.FormatedSetDetails(f"{' '.join(SetDetails)}")

            with open(file_path, 'a') as file:
                file.write(f"\n===\n{FormatedSet}")

            await ctx.send(f"New set added for {PokemonName.capitalize()} [{game.upper()}].")
        except ValueError as e:
            await ctx.send(str(e))
        except Exception as e:
            logging.error(e)
            await ctx.send("An error occurred while adding the set.")

def setup(bot):
    bot.add_cog(PKMStuff(bot))