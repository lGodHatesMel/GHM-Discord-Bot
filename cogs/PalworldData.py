import discord
from discord.ext import commands
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
    self.palinfo = self.load_json('PalworldDex.json')
    self.palitems = self.load_json('PalworldItems.json')
    self.palgear = self.load_json('PalworldGear.json')
    self.palskills = self.load_json('PalworldPassiveSkills.json')

  def load_json(self, filename):
    file_path = os.path.join(self.data_folder, filename)
    with open(file_path) as f:
      data = json.load(f)
    print(f"Loaded JSON data from {file_path}")
    return data

  async def create_embed(self, PalName):
    PalData = None
    for pal in self.palinfo:
      if PalName.lower() == pal["name"].strip().lower():
        PalData = pal
        break

    if PalData is None:
      return None, None

    # embed_title = "Wiki Link: " + PalData["name"]
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
    return embed, ImageFile, MapImage

  @commands.command(help="<pal name>")
  async def palinfo(self, ctx, *PalName):
    PalName = ' '.join(PalName)
    embed, ImageFile, MapImage = await self.create_embed(PalName)
    if embed:
      files = [f for f in [ImageFile, MapImage] if f is not None]
      await ctx.reply(embed=embed, files=files)
    else:
      await ctx.reply(f"Sorry, I could not find any information about {PalName}.")

  @commands.command(help="<item name>")
  async def palitem(self, ctx, *, ItemName: str):
    for item in self.palitems:
      if ItemName.lower() == item['name'].lower():
        embed = discord.Embed(title=item['name'], color=discord.Color.random())
        embed.set_thumbnail(url=f"https://github.com/lGodHatesMel/Palworld-Data/raw/main/Images/Items/{item['image']}")
        embed.add_field(name="Type", value=item['type'], inline=True)
        embed.add_field(name="Gold", value=item['gold'], inline=True)
        embed.add_field(name="Weight", value=item['weight'], inline=True)
        await ctx.send(embed=embed)
        return
    await ctx.send(f"Item '{ItemName}' not found.")

  @commands.command(help="- Displays all unique item types")
  async def pallistitemtypes(self, ctx):
    types = set(item['type'] for item in self.palitems)
    types_str = "\n".join(sorted(types))
    embeds = []
    for i in range(0, len(types_str), 1024):
      chunk = types_str[i:i+1024]
      embed = discord.Embed(title="Item Types", color=discord.Color.random())
      embed.add_field(name=f"Item List Types", value=chunk, inline=True)
      embeds.append(embed)
    paginator = Paginator(ctx, embeds)
    await paginator.start()

  @commands.command(help="<type name>")
  async def palitemtype(self, ctx, *, TypeName: str):
    MatchItems = [item['name'] for item in self.palitems if TypeName.lower() == item['type'].lower()]
    if MatchItems:
      Item_str = "\n".join(MatchItems)
      embeds = []
      for i in range(0, len(Item_str), 1024):
        chunk = Item_str[i:i+1024]
        embed = discord.Embed(title=f"Items of type '{TypeName}' (part {i//1024 + 1})", color=discord.Color.random())
        embed.add_field(name="Items", value=chunk, inline=False)
        embed.set_footer(text="Use the reactions to navigate between pages.")
        embeds.append(embed)
      paginator = Paginator(ctx, embeds)
      await paginator.start()
    else:
      await ctx.send(f"No items of type '{TypeName}' found.")

  @commands.command(help="- Displays all gear data")
  async def palgear(self, ctx):
    embeds = []
    embed = discord.Embed(title="Palworld Gear", color=discord.Color.random())
    char_count = len(embed.title) + len(embed.footer.text)
    field_count = 0
    for gear in self.palgear:
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

  @commands.command(help="<skill name>")
  async def palskills(self, ctx, *, SkillName: str):
    for skill in self.palskills:
      if SkillName.lower() == skill.lower():
        skill_data = self.palskills[skill]
        embed = discord.Embed(title='Passive Skills', color=discord.Color.random())
        embed.add_field(name="Skill", value=skill_data['name'], inline=False)
        embed.add_field(name="Positive", value=skill_data['positive'] if skill_data['positive'] else "None", inline=False)
        embed.add_field(name="Negative", value=skill_data['negative'] if skill_data['negative'] else "None", inline=False)
        embed.add_field(name="Tier", value=skill_data['tier'], inline=False)
        paginator = Paginator(ctx, [embed])
        await paginator.start()
        return
    await ctx.send(f"Skill '{SkillName}' not found.")

  @commands.command(help="- Displays all Palworld commands")
  async def palcommands(self, ctx):
    embed = discord.Embed(title="Palworld Commands", color=discord.Color.random())
    for command in self.get_commands():
      embed.add_field(name=command.name, value=command.help, inline=False)
    await ctx.send(embed=embed)

def setup(bot):
  bot.add_cog(PalworldData(bot))