import discord
from discord.ext import commands
import utils.utils as utils
from utils.utils import custom_emojis
from utils.botdb import CreateUserDatabase
from utils.Paginator import Paginator
import sqlite3

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('Database/Economy.db')
        self.c = self.conn.cursor()
        self.c.execute('''CREATE TABLE IF NOT EXISTS economy
                    (user_id text, balance real)''')
        self.conn.commit()

    @commands.command()
    async def balance(self, ctx, member: discord.Member = None):
        member = member or ctx.author
        self.c.execute("SELECT balance FROM economy WHERE user_id = ?", (member.id,))
        result = self.c.fetchone()
        if result is None:
            balance = 0
            self.c.execute("INSERT INTO economy VALUES (?, ?)", (member.id, balance))
            self.conn.commit()
        else:
            balance = result[0]

        embed = discord.Embed(
            title=f"{member.name}'s Balance",
            description=f"{member.mention} has {balance} PokeCoins {custom_emojis['pokecoin']}",
            color=discord.Color.green()
        )
        embed.set_thumbnail(url=member.avatar_url)
        await ctx.send(embed=embed)

    @commands.command()
    async def slots(self, ctx):
        pass

    @commands.command()
    async def blackjack(self, ctx):
        pass

    @commands.command()
    async def roulette(self, ctx):
        pass

    def cog_unload(self):
        self.conn.close()

def setup(bot):
    bot.add_cog(Economy(bot))