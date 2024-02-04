import discord
from discord.ext import commands
import json
import aiohttp
import io
import os

class PalworldData(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    data_folder = 'Data'
    self.palworld_file = os.path.join(data_folder, 'palworlddex.json')
    with open(self.palworld_file) as f:
      self.palinfo = json.load(f)

  async def create_embed(self, pal_name):
    pal_data = None
    for pal in self.palinfo:
      if pal_name.lower() == pal["name"].strip().lower():
        pal_data = pal
        break

    if pal_data is None:
      return None, None

    embed = discord.Embed(title=pal_data["name"], url=pal_data["wiki"], description=pal_data["description"], color=discord.Color.blue())

    async with aiohttp.ClientSession() as session:
      async with session.get(pal_data["image"]) as resp:
          if resp.status != 200:
              return None, None
          data = io.BytesIO(await resp.read())
          image_file = discord.File(data, 'image.png')

    embed.set_image(url=f"attachment://{image_file.filename}")

    type_emojis = []
    for type in pal_data["types"]:
        type_emojis.append(f"{type['type'].capitalize()}: :{type['emoji']}:")
    embed.add_field(name="Types", value=", ".join(type_emojis))

    drop_images = []
    for drop in pal_data["drops"]:
        drop_image_url = f"https://raw.githubusercontent.com/lgodhatesmel/Palworld-Data/main/images/drops/{drop}.png"
        drop_images.append(drop_image_url)
    embed.add_field(name="Drops", value=", ".join(drop_images))

    embed.add_field(name="Suitability", value=", ".join([f"{s['type']} ({s['level']})" for s in pal_data["suitability"]]))
    embed.add_field(name="Aura", value=pal_data["aura"]["name"])
    embed.add_field(name="Stats", value=f"HP: {pal_data['stats']['hp']}\nMelee: {pal_data['stats']['attack']['melee']}\nRanged: {pal_data['stats']['attack']['ranged']}\nDefense: {pal_data['stats']['defense']}\nRide: {pal_data['stats']['speed']['ride']}\nRun: {pal_data['stats']['speed']['run']}\nWalk: {pal_data['stats']['speed']['walk']}\nStamina: {pal_data['stats']['stamina']}\nSupport: {pal_data['stats']['support']}\nFood: {pal_data['stats']['food']}")
    return embed, image_file

  @commands.command()
  async def palinfo(self, ctx, pal_name):
    embed, image_file = await self.create_embed(pal_name)

    if embed:
      await ctx.reply(embed=embed, file=image_file)
    else:
      await ctx.reply(f"Sorry, I could not find any information about {pal_name}.")

def setup(bot):
  bot.add_cog(PalworldData(bot))