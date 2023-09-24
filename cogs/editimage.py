import discord
from discord.ext import commands
from PIL import Image
import io

class ImageEditor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def resizetheimage(self, ctx, size: int, attachment):
        try:
            image = Image.open(io.BytesIO(await attachment.read()))

            original_width, original_height = image.size
            new_width = size
            new_height = int((original_height / original_width) * size)
            resized_image = image.resize((new_width, new_height))

            resized_image_data = io.BytesIO()
            resized_image.save(resized_image_data, format='PNG')
            resized_image_data.seek(0)

            await ctx.send(f'Resized image to {size}px:', file=discord.File(resized_image_data, filename='resized_image.png'))

        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(help="<size> <image url>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def resizeurlimage(self, ctx, size: int, url: str):
        try:
            response = await self.bot.session.get(url)
            img_data = await response.read()
            image = Image.open(io.BytesIO(img_data))

            original_width, original_height = image.size
            new_width = size
            new_height = int((original_height / original_width) * size)
            resized_image = image.resize((new_width, new_height))

            resized_image_data = io.BytesIO()
            resized_image.save(resized_image_data, format='PNG')
            resized_image_data.seek(0)

            await ctx.send(file=discord.File(resized_image_data, filename='resized_image.png'))

        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')
    
    @commands.command(help="<size> <attach image>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def resizeimage(self, ctx, size: int):
        if len(ctx.message.attachments) == 0:
            await ctx.send('No image attached to the message.')
            return

        attachment = ctx.message.attachments[0]
        await self.resizetheimage(ctx, size, attachment)

def setup(bot):
    bot.add_cog(ImageEditor(bot))