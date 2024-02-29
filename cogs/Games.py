import asyncio
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import random
import os

hangmanwords = [
    # Random Words
    "discord","hangman", "games", "community","goosebumps",  "keyboard", "monitor", "python", "javascript", "database",
    "laptop", "internet", "algorithm", "software", "hardware",
    # Games
    "minecraft", "fortnite", "zelda", "mario", "cyberpunk", "overwatch", "skyrim", "roblox", "valorant", "amongus",
    "nintendo", "playstation",  "pokemon", "gamefreak", "palworld", "uncharted", "leagueoflegends", "apexlegends",
    "tetris", "pacman", "bioshock", "fallout", "witcher",
    # Sports
    "football", "basketball", "baseball", "soccer", "tennis", "cricket", "hockey", "golf", "volleyball", "rugby",
    "badminton", "squash", "billiards", "bowling", "wrestling", "athletics", "cycling", "swimming", "boxing", "karate",
    # Anime
    "naruto", "onepiece", "bleach", "deathnote", "attackontitan", "dragonball", "myheroacademia", "tokyoghoul",
    "demonslayer", "hunterxhunter", "onepunchman", "fullmetalalchemist", "cowboybebop", "evangelion", "gintama",
    "bleach", "fairytail", "gundam", "sailormoon",
    # Movies
    "inception", "titanic", "avatar", "joker", "avengers", "frozen", "lionking", "starwars", "harrypotter", "jurassicpark",
    # Music
    "beatles", "elvis", "madonna", "rihanna", "eminem", "beyonce", "drake", "edsheeran", "taylorswift", "billieeilish",
    # Geography
    "africa", "antarctica", "asia", "europe", "australia", "america", "ocean", "mountain", "river", "desert",
]

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.command(aliases=["dice", "rolldice"], help="<sides> <# of rolls>")
    async def roll(self, ctx, sides: int, num_rolls: int):
        if sides < 2 or num_rolls < 1:
            await ctx.message.reply("Invalid input. Please use !roll <sides> <num_rolls>.")
            return

        results = []
        for _ in range(num_rolls):
            roll = random.randint(1, sides)
            results.append(roll)

        result_text = ", ".join(map(str, results))
        total = sum(results)
        image_path = os.path.join("images", "rb_dice.png")

        if not os.path.exists(image_path):
            await ctx.message.reply("Dice image not found.")
            return

        embed = discord.Embed(title="Dice Roll", color=discord.Color.random())
        embed.set_thumbnail(url=f"attachment://{os.path.basename(image_path)}")
        embed.add_field(name="Result", value=f"You Rolled: **{result_text}**\nTotal: **{total}**", inline=False)

        await ctx.message.reply(embed=embed, file=discord.File(image_path, filename=os.path.basename(image_path)))

    @commands.command(aliases=['gimmighoulcoin', 'gcoin', 'flip'])
    async def flipcoin(self, ctx):
        result = 'Heads' if random.choice([True, False]) else 'Tails'

        heads_image_path = os.path.join('images', 'heads.png')
        tails_image_path = os.path.join('images', 'tails.png')

        if not (os.path.exists(heads_image_path) and os.path.exists(tails_image_path)):
            await ctx.message.reply("Error: Missing coin images.")
            return

        image_path = heads_image_path if result == 'Heads' else tails_image_path
        image = Image.open(image_path)

        image_buffer = io.BytesIO()
        image.save(image_buffer, format='PNG')
        image_buffer.seek(0)

        embed = discord.Embed(title="Coin Flip Result", color=0x00ff00)
        embed.add_field(name="Result", value=f"You flipped {result.lower()}", inline=False)
        embed.set_image(url="attachment://gimmighoul_coin.png")

        await ctx.message.reply(embed=embed, file=discord.File(image_buffer, 'gimmighoul_coin.png'))

    ## Hangman
    @commands.command(pass_context=True)
    async def hangman(self, ctx):
        # Check if already playing
        if ctx.author.id in self.games:
            await ctx.send("You are already playing Hangman! Finish your current game first.")
            return

        word = random.choice(hangmanwords)
        HiddenWord = ["_" for _ in word]
        WrongGuesses = []
        MaxGuesses = 8
        self.games[ctx.author.id] = {"word": word, "HiddenWord": HiddenWord, "WrongGuesses": WrongGuesses, "MaxGuesses": MaxGuesses}

        SpaceOutWord = ' '.join(self.games[ctx.author.id]['HiddenWord'])
        embed = discord.Embed(title=f"{ctx.author.name}'s Hangman game has begun!", color=discord.Color.blue())
        embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
        embed.add_field(name="Word", value=SpaceOutWord, inline=False)
        embed.add_field(name="Wrong guesses", value=WrongGuesses, inline=False)
        embed.add_field(name="Number of letters", value=len(word), inline=False)
        embed.set_footer(text=f"Guesses remaining: {MaxGuesses}")
        await ctx.send(embed=embed)
        await self.PlayHangman(ctx, MaxGuesses)

    async def PlayHangman(self, ctx, RemainingGuesses):
        def check(message):
            return message.author == ctx.author and message.content.lower() != "end" and len(message.content) == 1 and message.content.isalpha()

        embed_msg = None

        while RemainingGuesses > 0 and "_" in self.games[ctx.author.id]["HiddenWord"]:
            guess = await ctx.send("Guess a letter: ", delete_after=True)
            try:
                guess = await self.bot.wait_for("message", check=check, timeout=60)
                guess = guess.content.lower()
            except asyncio.TimeoutError:
                await ctx.send("Guess timed out! Type `end` to quit.", delete_after=True)
                return

            if guess == "end":
                break

            # Check guess
            if guess in self.games[ctx.author.id]["word"]:
                for i, letter in enumerate(self.games[ctx.author.id]["word"]):
                    if letter == guess:
                        self.games[ctx.author.id]["HiddenWord"][i] = guess
            else:
                self.games[ctx.author.id]["WrongGuesses"].append(guess)
                RemainingGuesses -= 1

            SpaceOutWord = ' '.join(self.games[ctx.author.id]['HiddenWord'])
            embed = discord.Embed(title=f"{ctx.author.name}'s Hangman game", color=discord.Color.blue())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            embed.add_field(name="Word", value=SpaceOutWord, inline=False)
            embed.add_field(name="Wrong guesses", value=', '.join(self.games[ctx.author.id]['WrongGuesses']), inline=False)
            embed.set_footer(text=f"Guesses remaining: {RemainingGuesses}")
            embed_msg = await ctx.send(embed=embed)

        # Game over
        if embed_msg is not None:
            await embed_msg.delete()

        if "_" not in self.games[ctx.author.id]["HiddenWord"]:
            embed = discord.Embed(title="Congratulations!", description=f"{ctx.author.name}, you guessed the word: {self.games[ctx.author.id]['word']}", color=discord.Color.green())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Game Over!", description=f"{ctx.author.name}, you ran out of guesses! The word was: {self.games[ctx.author.id]['word']}", color=discord.Color.red())
            embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
            await ctx.send(embed=embed)

        del self.games[ctx.author.id]

def setup(bot):
    bot.add_cog(Games(bot))