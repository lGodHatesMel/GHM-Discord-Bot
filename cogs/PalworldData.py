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

    self.paldex_file = os.path.join(data_folder, 'PalworldDex.json')
    with open(self.paldex_file) as f:
      self.palinfo = json.load(f)
    print(f"Loaded JSON data from {self.paldex_file}")

    self.palitems_file = os.path.join(data_folder, 'PalworldItems.json')
    with open(self.palitems_file) as f:
      self.palitems = json.load(f)
    print(f"Loaded JSON data from {self.palitems_file}")

    self.palgear_file = os.path.join(data_folder, 'PalworldGear.json')
    with open(self.palgear_file) as f:
      self.palgear = json.load(f)
    print(f"Loaded JSON data from {self.palgear_file}")

    # self.palpassiveskills_file = os.path.join(data_folder, 'PalworldPassiveSkills.json')
    # with open(self.palpassiveskills_file) as f:
    #   self.palpassiveskills = json.load(f)
    # print(f"Loaded JSON data from {self.palpassiveskills_file}")

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
    
    if "stats" in pal_data:
      stats = pal_data["stats"]
      stats_info = (
        f"HP: {stats['hp']}  -  Food: {stats['food']}  -  Stamina: {stats['stamina']}\n"
        f"Defense: {stats['defense']}  -  Support: {stats['support']}\n"
        f"(Attack)\n"
        f"Melee: {stats['attack']['melee']}  -  Range: {stats['attack']['ranged']}\n"
        f"(Speed)\n"
        f"Ride: {stats['speed']['ride']}  -  Run: {stats['speed']['run']}  -  Walk: {stats['speed']['walk']}"
      )
      embed.add_field(name="Stats", value=stats_info, inline=False)

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
              img = Image.open(data)
              img = img.resize((298, 200)) # width, Height
              resized_data = io.BytesIO()
              img.save(resized_data, format='PNG')
              resized_data.seek(0)
              map_image = discord.File(resized_data, 'map_image.png')
            except Exception as e:
              print(f"Error creating discord.File: {e}")
              map_image = None

    if map_image is not None:
      embed.set_image(url=f"attachment://{map_image.filename}")
    embed.set_footer(text=pal_data["description"])
    return embed, image_file, map_image

  @commands.command(help="<pal name>")
  async def palinfo(self, ctx, *pal_name):
    pal_name = ' '.join(pal_name)
    embed, image_file, map_image = await self.create_embed(pal_name)
    if embed:
      files = [f for f in [image_file, map_image] if f is not None]
      await ctx.reply(embed=embed, files=files)
    else:
      await ctx.reply(f"Sorry, I could not find any information about {pal_name}.")

  @commands.command(help="<item name>")
  async def palitem(self, ctx, *, item_name: str):
    for item in self.palitems:
      if item_name.lower() == item['name'].lower():
        embed = discord.Embed(title=item['name'], color=discord.Color.random())
        embed.set_thumbnail(url=f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Items/{item['image']}")
        embed.add_field(name="Type", value=item['type'], inline=True)
        embed.add_field(name="Gold", value=item['gold'], inline=True)
        embed.add_field(name="Weight", value=item['weight'], inline=True)
        await ctx.send(embed=embed)
        return
    await ctx.send(f"Item '{item_name}' not found.")

  @commands.command(help="<type name>")
  async def palitemtype(self, ctx, *, type_name: str):
    MatchItems = [item['name'] for item in self.palitems if type_name.lower() == item['type'].lower()]

    if MatchItems:
      embed = discord.Embed(title=f"Items of type '{type_name}'", color=discord.Color.random())
      Item_str = "\n".join(MatchItems)
      for i in range(0, len(Item_str), 1024):
        chunk = Item_str[i:i+1024]
        embed.add_field(name=f"Items (part {i//1024 + 1})", value=chunk, inline=False)
      await ctx.send(embed=embed)
    else:
      await ctx.send(f"No items of type '{type_name}' found.")

  @commands.command(help="Displays all gear data")
  async def palgear(self, ctx):
    embed = discord.Embed(title="Palworld Gear", color=discord.Color.random())
    for gear in self.palgear:
      gear_info = ""
      for rarity in ['common', 'uncommon', 'rare', 'epic', 'legendary']:
        if rarity in gear['status']:
          gear_info += f"{rarity.capitalize()}: HP {gear['status'][rarity]['hp']}, Defense {gear['status'][rarity]['defense']}\n"
      if gear_info:
        for i in range(0, len(gear_info), 1024):
          chunk = gear_info[i:i+1024]
          embed.add_field(name=gear['name'], value=chunk, inline=False)
    await ctx.send(embed=embed)

def setup(bot):
  bot.add_cog(PalworldData(bot))