import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
import os
import random
import requests
import utils.utils as utils
from config import GUILDID, ROLEIDS
from typing import Union
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

    @cog_ext.cog_slash(name="pokefacts", description="Get a random Pokémon fact.", guild_ids=[GUILDID], options=[])
    @commands.command(name="pokefacts", help='Get a random Pokémon fact.')
    async def pokefacts(self, ctx: Union[commands.Context, SlashContext]):
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

    @cog_ext.cog_slash(name="showdown", description="<Game: sv, swsh, pla, bdsp> <Pokemon Name>",
        options=[
            create_option(name="game", description="Game", option_type=3, required=True),
            create_option(name="pokemon_name", description="Pokemon Name", option_type=3, required=True)
        ], guild_ids=[GUILDID]
    )
    @commands.command(name="showdown", aliases=['showdownset'], help='<Game: sv, swsh, pla, bdsp> <Pokemon Name>')
    async def showdown(self, ctx: Union[commands.Context, SlashContext], game: str, PokemonName: str):
        try:
            file_path = self.GetFilePath(game, PokemonName)
            if not os.path.exists(file_path):
                await ctx.message.reply(f"No sets found for {PokemonName} [{game}].")
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
                await ctx.message.reply(embed=embed)
            else:
                await ctx.message.reply(f"No sets found for {PokemonName.capitalize()} [{game.upper()}].")
        except ValueError as e:
            await ctx.message.reply(str(e))
        except Exception as e:
            logging.error(e)
            await ctx.message.reply("An error occurred while fetching Pokémon sets.")

    @cog_ext.cog_subcommand(base="Staff", name="addset", description="Game: <sv, swsh, pla, bdsp> <PokemonName> <ShowdownSetDetails>",
        options=[
            create_option(name="game", description="Game: <sv, swsh, pla, bdsp>", option_type=3, required=True),
            create_option(name="pokemon_name", description="Pokemon Name", option_type=3, required=True),
            create_option(name="set_details", description="Showdown Set Details", option_type=3, required=True)
        ], guild_ids=[GUILDID]
    )
    @commands.command(name="addset", help='Game: <sv, swsh, pla, bdsp> <PokemonName> <ShowdownSetDetails>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addset(self, ctx: Union[commands.Context, SlashContext], game: str, PokemonName: str, *SetDetails: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Helper"], ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        try:
            file_path = self.GetFilePath(game, PokemonName)
            FormatedSet = utils.FormatedSetDetails(f"{' '.join(SetDetails)}")
            with open(file_path, 'a') as file:
                file.write(f"\n===\n{FormatedSet}")
            await ctx.message.reply(f"New set added for {PokemonName.capitalize()} [{game.upper()}].")
        except ValueError as e:
            await ctx.message.reply(str(e))
        except Exception as e:
            logging.error(e)
            await ctx.message.reply("An error occurred while adding the set.")

def setup(bot):
    bot.add_cog(PKMStuff(bot))