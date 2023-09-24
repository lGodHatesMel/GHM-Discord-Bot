import discord
from discord.ext import commands
import random
import os

class Games(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

        # Get the path to the dice image in the "images" folder
        image_path = os.path.join("images", "rb_dice.png")

        # Check if the image file exists
        if not os.path.exists(image_path):
            await ctx.send("Dice image not found.")
            return

        embed = discord.Embed(title="Dice Roll", color=discord.Color.blue())

        # Set the image in the embed
        with open(image_path, "rb") as image_file:
            file = discord.File(image_file, filename=os.path.basename(image_path))
            embed.set_image(url=f"attachment://{os.path.basename(image_path)}")

        embed.add_field(name="Result", value=f"You rolled: {result_text}\nTotal: {total}", inline=False)

        await ctx.send(embed=embed, file=file)
        
    # @commands.command(aliases=["dice", "rolldice"], help="<1-6> <num_rolls>")
    # async def roll(self, ctx, sides: int, num_rolls: int):
    #     if sides != 6 or num_rolls > 6 or num_rolls < 1:
    #         await ctx.send("Invalid input. Please use !roll (1-6) (1-6)")
    #         return

    #     results = []
    #     for _ in range(num_rolls):
    #         roll = random.randint(1, sides)
    #         results.append(roll)

    #     total = sum(results)
    #     result_text = ", ".join([f":dice-{roll}:" for roll in results])

    #     embed = discord.Embed(
    #         title="Dice Roll",
    #         description=f"You rolled: {result_text}\nTotal: {total}",
    #         color=discord.Color.blue(),
    #     )

    #     await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Games(bot))