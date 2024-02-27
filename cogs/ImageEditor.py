import discord
from discord.ext import commands
from PIL import Image
import io
from io import BytesIO

class ImageEditor(commands.Cog):
    hidden = True

    def __init__(self, bot):
        self.bot = bot

    async def resizetheimage(self, ctx, size, attachment, save_name):
        try:
            image = Image.open(io.BytesIO(await attachment.read()))
            original_width, original_height = image.size
            new_width = size
            new_height = int((original_height / original_width) * size)
            resized_image = image.resize((new_width, new_height))
            resized_image_data = io.BytesIO()
            resized_image.save(resized_image_data, format='PNG')
            resized_image_data.seek(0)

            await ctx.send(f'Resized image to {size}px:', file=discord.File(resized_image_data, filename=f'{save_name}.png'))
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @commands.command(help="<size> <image url> <save_name>", description="Resizes an image from URL to a specified size.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def resizeurlimage(self, ctx, size: int, url: str, save_name: str):
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
            await ctx.message.reply(file=discord.File(resized_image_data, filename=f'{save_name}.png'))
        except Exception as e:
            await ctx.message.reply(f'An error occurred: {str(e)}')

    @commands.command(help="<size> <save_name>", description="Resizes an attached image to a specified size.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def resizeimage(self, ctx, size: int, save_name: str):
        if len(ctx.message.attachments) == 0:
            await ctx.message.reply('No image attached to the message.')
            return

        attachment = ctx.message.attachments[0]
        await self.resizetheimage(ctx, size, attachment, save_name)

    def merge_images(self, images):
        widths, heights = zip(*(i.size for i in images))
        # Calculate the total width and the maximum height
        total_width = sum(widths)
        max_height = max(heights)
        new_image = Image.new('RGB', (total_width, max_height))
        x_offset = 0
        for image in images:
            new_image.paste(image, (x_offset, 0))
            x_offset += image.size[0]
        return new_image

    @commands.command(help="<width> <height> <save_name> <send_discord_only>", description="Merges multiple attached images into one", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def merge(self, ctx, width: int, height: int, save_name: str, discord_only: bool):
        # Check if the message has attachments
        if ctx.message.attachments:
            images = []
            for attachment in ctx.message.attachments:
                if attachment.content_type.startswith('image/'):
                    image_bytes = await attachment.read()
                    image = Image.open(BytesIO(image_bytes))
                    image = image.resize((width, height))
                    images.append(image)
            # Check if there are at least two images
            if len(images) >= 2:
                merged_image = self.merge_images(images)
                if not discord_only:
                    merged_image.save(f'images/{save_name}.png')  # Save the image to the bot's files
                await ctx.message.reply(file=discord.File(f'images/{save_name}.png'))  # Send the image to the Discord channel
            else:
                await ctx.message.reply('Please attach at least two images to merge.')
        else:
            await ctx.message.reply('To use this command, type !merge width height save_name discord_only and attach two or more images to your message and I will merge them into one image.')

def setup(bot):
    bot.add_cog(ImageEditor(bot))