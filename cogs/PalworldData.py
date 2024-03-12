import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from config import GUILDID
from typing import Union
import json
import aiohttp
import io
import os
from PIL import Image
from utils.Paginator import Paginator

class PalworldData(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.data_folder = 'Data'
    self.pal_info_data = self.load_json('PalworldDex.json')
    self.palitems_info_data = self.load_json('PalworldItems.json')
    self.palgear_info_data= self.load_json('PalworldGear.json')
    self.palskills_info_data = self.load_json('PalworldPassiveSkills.json')

  def load_json(self, filename):
    file_path = os.path.join(self.data_folder, filename)
    with open(file_path) as f:
      data = json.load(f)
    # print(f"Loaded JSON data from {file_path}")
    return data

  @cog_ext.cog_subcommand(base="Palworld", name="palitem", description="Get information about a specific item.",
    options=[create_option(name="item_name", description="Item Name", option_type=3, required=True)], guild_ids=[GUILDID])
  async def palitem(self, ctx: Union[commands.Context, SlashContext], item_name: str):
    for item in self.palitems_info_data:
      if item_name.lower() == item['name'].lower():
        embed = discord.Embed(title=item['name'], color=discord.Color.random())
        embed.set_thumbnail(url=f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Items/{item['image']}")
        embed.add_field(name="Type", value=item['type'], inline=True)
        embed.add_field(name="Gold", value=item['gold'], inline=True)
        embed.add_field(name="Weight", value=item['weight'], inline=True)
        await ctx.send(embed=embed)
        return
    await ctx.send(f"Item '{item_name}' not found.")

  @cog_ext.cog_subcommand(base="Palworld", name="pallistitemtypes", description="Displays all unique item types.", guild_ids=[GUILDID])
  async def pallistitemtypes(self, ctx: Union[commands.Context, SlashContext]):
    types = set(item['type'] for item in self.palitems_info_data)
    types_str = "\n".join(sorted(types))
    embeds = []
    for i in range(0, len(types_str), 1024):
      chunk = types_str[i:i+1024]
      embed = discord.Embed(title="Item Types", color=discord.Color.random())
      embed.add_field(name=f"Item List Types", value=chunk, inline=True)
      embeds.append(embed)
    paginator = Paginator(ctx, embeds)
    await paginator.start()

  @cog_ext.cog_subcommand(base="Palworld", name="palitemtype", description="Get items of a specific type.",
    options=[create_option(name="type_name", description="Type Name", option_type=3, required=True)], guild_ids=[GUILDID])
  async def palitemtype(self, ctx: Union[commands.Context, SlashContext], type_name: str):
    MatchItems = [item['name'] for item in self.palitems_info_data if type_name.lower() == item['type'].lower()]
    if MatchItems:
      Item_str = "\n".join(MatchItems)
      embeds = []
      for i in range(0, len(Item_str), 1024):
        chunk = Item_str[i:i+1024]
        embed = discord.Embed(title=f"Items of type '{type_name}' (part {i//1024 + 1})", color=discord.Color.random())
        embed.add_field(name="Items", value=chunk, inline=False)
        embed.set_footer(text="Use the reactions to navigate between pages.")
        embeds.append(embed)
      paginator = Paginator(ctx, embeds)
      await paginator.start()
    else:
      await ctx.send(f"No items of type '{type_name}' found.")

  @cog_ext.cog_subcommand(base="Palworld", name="palgear", description="Displays all gear data.", guild_ids=[GUILDID])
  async def palgear(self, ctx: Union[commands.Context, SlashContext]):
    embeds = []
    embed = discord.Embed(title="Palworld Gear", color=discord.Color.random())
    char_count = len(embed.title) + len(embed.footer.text)
    field_count = 0
    for gear in self.palgear_info_data:
      for rarity in ['common', 'uncommon', 'rare', 'epic', 'legendary']:
        if rarity in gear['status']:
          gear_info = f"HP: {gear['status'][rarity]['hp']}, Defense: {gear['status'][rarity]['defense']}, Price: {gear['status'][rarity]['price']}, Durability: {gear['status'][rarity]['durability']}"
          field_name = f"{gear['name']} ({rarity.capitalize()})"
          if char_count + len(field_name) + len(gear_info) > 6000 or field_count >= 25:
            embeds.append(embed)
            embed = discord.Embed(title="Palworld Gear", color=discord.Color.random())
            char_count = len(embed.title) + len(embed.footer.text)
            field_count = 0
          embed.add_field(name=field_name, value=gear_info, inline=True)
          char_count += len(field_name) + len(gear_info)
          field_count += 1
    embeds.append(embed)

    for i, embed in enumerate(embeds):
      embed.title = f"Palworld Gear (Page {i+1} of {len(embeds)})"
    paginator = Paginator(ctx, embeds)
    await paginator.start()

  @cog_ext.cog_subcommand(base="Palworld", name="pallistallskills", description="List all skills.", guild_ids=[GUILDID])
  async def pallistallskills(self, ctx: SlashContext):
    skills = list(self.palskills_info_data.values())
    embeds = []
    for i in range(0, len(skills), 14):
      embed = discord.Embed(title='All Skills', color=discord.Color.random())
      for skill in skills[i:i+14]:
        embed.add_field(name=skill['name'], value="⠀", inline=False)
      embed.set_footer(text="Use the reactions to navigate through the pages.")
      embeds.append(embed)
    paginator = Paginator(ctx, embeds)
    await paginator.start()

  @cog_ext.cog_subcommand(base="Palworld", name="palskills", description="Get information about a specific skill.",
    options=[create_option(name="skill_name", description="Skill Name", option_type=3, required=True)], guild_ids=[GUILDID])
  async def palskills(self, ctx: SlashContext, skill_name: str):
    for skill in self.palskills_info_data.values():
      if skill_name.lower() == skill['name'].lower():
        embed = discord.Embed(title='Passive Skills', color=discord.Color.random())
        embed.add_field(name="Skill", value=skill['name'], inline=False)
        embed.add_field(name="Positive", value=skill['positive'] if skill['positive'] else "None", inline=False)
        embed.add_field(name="Negative", value=skill['negative'] if skill['negative'] else "None", inline=False)
        embed.add_field(name="Tier", value=skill['tier'], inline=False)
        paginator = Paginator(ctx, [embed])
        await paginator.start()
        return
    await ctx.send(f"Skill '{skill_name}' not found.")

  @cog_ext.cog_subcommand(base="Palworld", name="palinfo", description="Get information about a specific Pal.",
    options=[create_option(name="pal_name", description="Pal Name", option_type=3, required=True)], guild_ids=[GUILDID])
  async def palinfo(self, ctx: Union[commands.Context, SlashContext], pal_name: str):
    PalName = pal_name
    PalData = None
    for pal in self.pal_info_data:
      if PalName.lower() == pal["name"].strip().lower():
        PalData = pal
        break

    if PalData is None:
      await ctx.send(f"Sorry, I could not find any information about {PalName}.")
      return

    embed_title = "[Click Here for Wiki Link]"
    embed_url = PalData["wiki"]
    embed = discord.Embed(title=embed_title, url=embed_url, color=discord.Color.random())

    SuitabilityInfo = ""
    for suitability in PalData["suitability"]:
      if 'emoji' in suitability:
        EmojiName = suitability['emoji']
        emoji = discord.utils.get(self.bot.emojis, name=EmojiName)
        if emoji:
          EmojiID = f"<:{emoji.name}:{emoji.id}>"
          SuitabilityInfo += f"{suitability['type']} {EmojiID} Lvl: {suitability['level']}\n"
        else:
          SuitabilityInfo += f"{suitability['type']} Lvl: {suitability['level']}\n"
    embed.add_field(name="Suitability", value=SuitabilityInfo, inline=True)

    DropeInfo = ""
    for drop in PalData["drops"]:
      DropeInfo += f"{drop}\n"
    embed.add_field(name="Drops", value=DropeInfo, inline=True)

    if "stats" in PalData:
      stats = PalData["stats"]
      StatsInfo = (
        f"HP: {stats['hp']}  -  Food: {stats['food']}  -  Stamina: {stats['stamina']}\n"
        f"Defense: {stats['defense']}  -  Support: {stats['support']}\n"
        f"(Attack)\n"
        f"Melee: {stats['attack']['melee']}  -  Range: {stats['attack']['ranged']}\n"
        f"(Speed)\n"
        f"Ride: {stats['speed']['ride']}  -  Run: {stats['speed']['run']}  -  Walk: {stats['speed']['walk']}"
      )
      embed.add_field(name="Stats", value=StatsInfo, inline=False)

    async with aiohttp.ClientSession() as session:
      async with session.get(PalData["image"]) as resp:
        if resp.status == 200:
          data = io.BytesIO(await resp.read())
          try:
            ImageFile = discord.File(data, 'image.png')
            embed.set_thumbnail(url=f"attachment://{ImageFile.filename}")
          except Exception as e:
            print(f"Error creating discord.File: {e}")
      embed.set_thumbnail(url=f"attachment://{ImageFile.filename}")

    TypingIcon = []
    for typing in PalData["types"]:
      type_image_url = f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Typings/{typing}.png"
      TypingIcon.append(type_image_url)

    if TypingIcon:
      embed.set_author(name=f"{PalData['name']} #{PalData['pal_id']}", icon_url=TypingIcon[0])

    MapImage = None
    if "pal_id" in PalData:
      map_url = f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Maps/{PalData['pal_id']}.png"
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
              MapImage = discord.File(resized_data, 'map_image.png')
            except Exception as e:
              print(f"Error creating discord.File: {e}")
              MapImage = None

    if MapImage is not None:
      embed.set_image(url=f"attachment://{MapImage.filename}")
    embed.set_footer(text=PalData["description"])

    files = [f for f in [ImageFile, MapImage] if f is not None]
    await ctx.send(embed=embed, files=files)

  # @cog_ext.cog_slash(name="palcommands", description="Displays all Palworld commands.", guild_ids=[GUILDID], options=[])
  # @commands.command(help="- Displays all Palworld commands")
  # async def palcommands(self, ctx: Union[commands.Context, SlashContext]):
  #   embed = discord.Embed(title="Palworld Commands", color=discord.Color.random())
  #   for command in self.get_commands():
  #     embed.add_field(name=command.name, value=command.help, inline=False)
  #   await ctx.send(embed=embed)

def setup(bot):
  bot.add_cog(PalworldData(bot))