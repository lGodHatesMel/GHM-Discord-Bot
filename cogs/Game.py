import asyncio
import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
import random
import os

hangmanwords = [
        "python", "discord", "programming", "hangman", "game", "community", "pokemon", "gamefreak", "palworld",
        "nintendo", "playstation", "goosebumps"
]

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    @commands.command(aliases=["dice", "rolldice"], help="<sides> <num_rolls>")
    async def roll(self, ctx, sides: int, num_rolls: int):
        if sides < 2 or num_rolls < 1:
            await ctx.send("Invalid input. Please use !roll <sides> <num_rolls>.")
            return

        results = []
        for _ in range(num_rolls):
            roll = random.randint(1, sides)
            results.append(roll)

        result_text = ", ".join(map(str, results))
        total = sum(results)
        image_path = os.path.join("images", "rb_dice.png")

        if not os.path.exists(image_path):
            await ctx.send("Dice image not found.")
            return

        embed = discord.Embed(title="Dice Roll", color=discord.Color.random())
        embed.set_thumbnail(url=f"attachment://{os.path.basename(image_path)}")
        embed.add_field(name="Result", value=f"You Rolled: **{result_text}**\nTotal: **{total}**", inline=False)

        await ctx.send(embed=embed, file=discord.File(image_path, filename=os.path.basename(image_path)))

    @commands.command(aliases=['gimmighoulcoin', 'gcoin', 'flip'])
    async def flipcoin(self, ctx):
        result = 'Heads' if random.choice([True, False]) else 'Tails'

        heads_image_path = os.path.join('images', 'heads.png')
        tails_image_path = os.path.join('images', 'tails.png')

        if not (os.path.exists(heads_image_path) and os.path.exists(tails_image_path)):
            await ctx.send("Error: Missing coin images.")
            return

        image_path = heads_image_path if result == 'Heads' else tails_image_path
        image = Image.open(image_path)

        image_buffer = io.BytesIO()
        image.save(image_buffer, format='PNG')
        image_buffer.seek(0)

        embed = discord.Embed(title="Coin Flip Result", color=0x00ff00)
        embed.add_field(name="Result", value=f"You flipped {result.lower()}", inline=False)
        embed.set_image(url="attachment://gimmighoul_coin.png")

        await ctx.send(embed=embed, file=discord.File(image_buffer, 'gimmighoul_coin.png'))

    ## Hangman
    @commands.command(pass_context=True)
    async def hangman(self, ctx):
        # Check if already playing
        if ctx.author.id in self.games:
            await ctx.send("You are already playing Hangman! Finish your current game first.")
            return

        word = random.choice(hangmanwords)
        hidden_word = ["_" for _ in word]
        wrong_guesses = []
        max_guesses = 6
        self.games[ctx.author.id] = {"word": word, "hidden_word": hidden_word, "wrong_guesses": wrong_guesses, "max_guesses": max_guesses}

        embed = discord.Embed(title="Hangman has begun!", color=discord.Color.blue())
        embed.add_field(name="Word", value=' '.join(hidden_word), inline=False)
        embed.add_field(name="Wrong guesses", value=wrong_guesses, inline=False)
        embed.add_field(name="Guesses remaining", value=max_guesses, inline=False)
        await ctx.send(embed=embed)

        await self.play_turn(ctx, max_guesses)

    async def play_turn(self, ctx, remaining_guesses):
        def check(message):
            return message.author == ctx.author and message.content.lower() != "end" and len(message.content) == 1 and message.content.isalpha()

        # Initialize embed_msg
        embed_msg = None

        while remaining_guesses > 0 and "_" in self.games[ctx.author.id]["hidden_word"]:
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
                        self.games[ctx.author.id]["hidden_word"][i] = guess
            else:
                self.games[ctx.author.id]["wrong_guesses"].append(guess)
                remaining_guesses -= 1

                # Add spaces between the characters
                spaced_word = ' '.join(self.games[ctx.author.id]['hidden_word'])

                embed = discord.Embed(title="Hangman", color=discord.Color.blue())
                embed.add_field(name="Word", value=spaced_word, inline=False)
                embed.add_field(name="Wrong guesses", value=', '.join(self.games[ctx.author.id]['wrong_guesses']), inline=False)
                embed.add_field(name="Guesses remaining", value=remaining_guesses, inline=False)
                embed_msg = await ctx.send(embed=embed)

        # Game over
        if embed_msg is not None:
            await embed_msg.delete()

        if "_" not in self.games[ctx.author.id]["hidden_word"]:
            embed = discord.Embed(title="Congratulations!", description=f"You guessed the word: {self.games[ctx.author.id]['word']}", color=discord.Color.green())
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(title="Game Over!", description=f"You ran out of guesses! The word was: {self.games[ctx.author.id]['word']}", color=discord.Color.red())
            await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Games(bot))