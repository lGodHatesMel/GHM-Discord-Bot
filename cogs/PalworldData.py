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

    # embed_title = "Wiki Link: " + pal_data["name"]
    embed_title = "[Click Here for Wiki Link]"
    embed_url = pal_data["wiki"]
    embed = discord.Embed(title=embed_title, url=embed_url, color=discord.Color.random())

    suitability_info = ""
    for suitability in pal_data["suitability"]:
      if 'emoji' in suitability:
        emoji_name = suitability['emoji']
        emoji = discord.utils.get(self.bot.emojis, name=emoji_name)
        if emoji:
          emoji_with_id = f"<:{emoji.name}:{emoji.id}>"
          suitability_info += f"{suitability['type']} {emoji_with_id} Lvl: {suitability['level']}\n"
        else:
          suitability_info += f"{suitability['type']} Lvl: {suitability['level']}\n"
    embed.add_field(name="Suitability", value=suitability_info, inline=True)

    drops_info = ""
    for drop in pal_data["drops"]:
      drops_info += f"{drop}\n"
    embed.add_field(name="Drops", value=drops_info, inline=True)

    async with aiohttp.ClientSession() as session:
      async with session.get(pal_data["image"]) as resp:
        if resp.status == 200:
          data = io.BytesIO(await resp.read())
          try:
            image_file = discord.File(data, 'image.png')
            embed.set_thumbnail(url=f"attachment://{image_file.filename}")
          except Exception as e:
            print(f"Error creating discord.File: {e}")

      embed.set_thumbnail(url=f"attachment://{image_file.filename}")

    typing_icon = []
    for typing in pal_data["types"]:
      type_image_url = f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Typings/{typing}.png"
      typing_icon.append(type_image_url)

    if typing_icon:
      embed.set_author(name=f"{pal_data['name']} #{pal_data['pal_id']}", icon_url=typing_icon[0])

    map_image = None
    if "pal_id" in pal_data:
      map_url = f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Maps/{pal_data['pal_id']}.png"
      async with aiohttp.ClientSession() as session:
        async with session.get(map_url) as resp:
          if resp.status == 200:
            data = io.BytesIO(await resp.read())
            try:
              map_image = discord.File(data, 'map_image.png')
            except Exception as e:
              print(f"Error creating discord.File: {e}")
              map_image = None

    if map_image is not None:
      embed.set_image(url=f"attachment://{map_image.filename}")

    # embed.add_field(name="Wiki Link", value=pal_data["wiki"], inline=False)
    embed.set_footer(text=pal_data["description"])

    return embed, image_file, map_image

  @commands.command()
  async def palinfo(self, ctx, *pal_name):
    pal_name = ' '.join(pal_name)
    embed, image_file, map_image = await self.create_embed(pal_name)
    if embed:
      files = [f for f in [image_file, map_image] if f is not None]
      await ctx.reply(embed=embed, files=files)
    else:
      await ctx.reply(f"Sorry, I could not find any information about {pal_name}.")

def setup(bot):
  bot.add_cog(PalworldData(bot))