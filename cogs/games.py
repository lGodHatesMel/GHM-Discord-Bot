import discord
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont
import io
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

        await ctx.send(file=discord.File(image_buffer, f'gimmighoul_coin_{result.lower()}.png'))

def setup(bot):
    bot.add_cog(Games(bot))