import discord
from discord.ext import commands
import json
import aiohttp
import io
import os
from PIL import Image

class PalworldData(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    data_folder = 'Data'
    self.palworld_file = os.path.join(data_folder, 'palworlddex.json')
    with open(self.palworld_file) as f:
      self.palinfo = json.load(f)
    print(f"Loaded JSON data from {self.palworld_file}")

  async def create_embed(self, pal_name):
    pal_data = None
    for pal in self.palinfo:
      if pal_name.lower() == pal["name"].strip().lower():
        pal_data = pal
        break

    if pal_data is None:
      return None, None

    embed_title = f"{pal_data['name']} #{pal_data['pal_id']}"
    embed = discord.Embed(title=embed_title, color=discord.Color.blue())

    suitability_info = ""
    for suitability in pal_data["suitability"]:
      if 'emoji' in suitability:
        emoji_name = suitability['emoji']
        emoji = discord.utils.get(self.bot.emojis, name=emoji_name)
        if emoji:
          emoji_with_id = f"<:{emoji.name}:{emoji.id}>"
          suitability_info += f"{suitability['type']} {emoji_with_id} Lvl: {suitability['level']}\n"
    embed.add_field(name="Suitability", value=suitability_info, inline=True)

    drops_info = ""
    for drop in pal_data["drops"]:
      drops_info += f"{drop}\n"
    embed.add_field(name="Drops", value=drops_info, inline=True)

    async with aiohttp.ClientSession() as session:
      async with session.get(pal_data["image"]) as resp:
        if resp.status != 200:
          return None, None
        data = io.BytesIO(await resp.read())
        try:
          image_file = discord.File(data, 'image.png')
        except Exception as e:
          print(f"Error creating discord.File: {e}")
          return None, None

    embed.set_thumbnail(url=f"attachment://{image_file.filename}")

    typing_images = []
    for typing in pal_data["types"]:
      type_image_url = f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Typings/{typing}.png"
      typing_images.append(type_image_url)

    if typing_images:
      embed.set_author(name=pal_data['name'], icon_url=typing_images[0])

    embed.add_field(name="Wiki Link", value=pal_data["wiki"], inline=False)
    embed.set_footer(text=pal_data["description"])

    return embed, image_file

  @commands.command()
  async def palinfo(self, ctx, *pal_name):
    pal_name = ' '.join(pal_name)
    embed, image_file = await self.create_embed(pal_name)
    if embed:
      await ctx.reply(embed=embed, file=image_file)
    else:
      await ctx.reply(f"Sorry, I could not find any information about {pal_name}.")

def setup(bot):
  bot.add_cog(PalworldData(bot))