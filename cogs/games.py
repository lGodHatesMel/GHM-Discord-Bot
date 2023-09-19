import discord
from discord.ext import commands
import random
import os

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="roll", aliases=["dice", "rolldice"], help="Roll a six-sided dice and get a random number between 1 and 6.")
    async def roll_dice(self, ctx, sides: int = 6, num_rolls: int = 1):
        """
        Roll a dice.
        Usage: !roll [sides] [num_rolls]
        """
        if sides < 2 or num_rolls < 1:
            await ctx.send("Invalid input. Please use !roll [sides] [num_rolls].")
            return

        results = []
        for _ in range(num_rolls):
            roll = random.randint(1, sides)
            results.append(roll)

        result_text = ", ".join(map(str, results))
        total = sum(results)

        # Get the path to the dice image in the "images" folder
        image_path = os.path.join("Images", "rb_dice.png")

        # Check if the image file exists
        if not os.path.exists(image_path):
            await ctx.send("Dice image not found.")
            return

        embed = discord.Embed(title="Dice Roll", description=f"You rolled: {result_text}\nTotal: {total}", color=discord.Color.blue())

        # Attach the image to the embed
        with open(image_path, "rb") as image_file:
            image = discord.File(image_file)
            embed.set_image(url="attachment://" + os.path.basename(image_path))

        await ctx.send(embed=embed, file=image)

def setup(bot):
    bot.add_cog(Games(bot))