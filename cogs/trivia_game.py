import discord
from discord.ext import commands, tasks
import asyncio
import random
import os
import json
import datetime
import sqlite3

class TriviaGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_channel_id = None
        self.question_message = None
        self.conn = sqlite3.connect('Database/coins.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS user_coins
                (user_id TEXT PRIMARY KEY, right_count INTEGER, wrong_count INTEGER, total_coins INTEGER)''')
        self.conn.commit()
        self.trivia_questions = []
        self.min_question_interval = 1
        self.max_question_interval = 5
        self.post_question.start()

    def cog_unload(self):
        self.post_question.cancel()

    @commands.command(hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def pausetrivia(self, ctx, pause_duration: int = 10):
        if pause_duration <= 0:
            await ctx.send("Pause duration must be a positive integer.")
            return

        self.post_question.stop()

        try:
            embed = discord.Embed(
                title="Trivia Pause",
                description=f"Trivia questions paused for {pause_duration} minutes. ⏸️",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            await asyncio.sleep(pause_duration * 60)

            embed = discord.Embed(
                title="Trivia Resume",
                description="Trivia questions resumed! ▶️",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        finally:
            self.post_question.start()

    @commands.command(hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def skiptrivia(self, ctx):
        if self.question_message:
            await self.question_message.delete()
            self.question_message = None
            await ctx.send("Trivia question skipped.")
            await self.trivia(ctx)

    @commands.command(help="Show's'your PokeCoin info")
    async def coins(self, ctx):
        await self.send_coins_info(ctx, ctx.author)

    @commands.command(help='<uid>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def usercoins(self, ctx, user: discord.User):
        await self.send_coins_info(ctx, user)

    async def send_coins_info(self, ctx, user):
        uid = str(user.id)
        self.cursor.execute("SELECT right_count, wrong_count, total_coins FROM user_coins WHERE user_id = ?", (uid,))
        user_data = self.cursor.fetchone()

        if user_data is None:
            right_count = wrong_count = total_coins = 0
        else:
            right_count, wrong_count, total_coins = user_data

        embed = discord.Embed(
            title=f"{user.name}'s PokeCoin Info:",
            color=discord.Color.gold()
        )

        embed.add_field(name="PokeCoins", value=total_coins)
        embed.add_field(name="Correct Answers", value=right_count)
        embed.add_field(name="Wrong Answers", value=wrong_count)
        await ctx.send(embed=embed)

    async def update_coins(self, user, amount):
        uid = str(user.id)
        self.cursor.execute("SELECT total_coins FROM user_coins WHERE user_id = ?", (uid,))
        user_data = self.cursor.fetchone()

        if user_data is None:
            new_total_coins = amount
            self.cursor.execute("INSERT INTO user_coins VALUES (?, 0, 0, ?)", (uid, new_total_coins))
        else:
            total_coins, = user_data
            new_total_coins = total_coins + amount
            self.cursor.execute("UPDATE user_coins SET total_coins = ? WHERE user_id = ?", (new_total_coins, uid))

        self.conn.commit()
        return new_total_coins

    @commands.command(help='<uid_or_user> <amount>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def givecoins(self, ctx, user: discord.User, amount: int):
        if amount <= 0:
            await ctx.send("Amount must be a positive integer.")
            return

        new_total_coins = await self.update_coins(user, amount)

        embed = discord.Embed(
            title=f"Gave {amount} PokeCoins to {user.name}",
            color=discord.Color.green()
        )

        embed.add_field(name="New Total PokeCoins", value=new_total_coins)
        await ctx.send(embed=embed)

    @commands.command(help='<uid_or_user> <amount>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removecoins(self, ctx, user: discord.User, amount: int):
        if amount <= 0:
            await ctx.send("Amount must be a positive integer.")
            return

        new_total_coins = await self.update_coins(user, -amount)

        if new_total_coins < 0:
            await ctx.send(f"{user.name} doesn't have enough PokeCoins to remove {amount}.")
            await self.update_coins(user, amount)  # undo the previous update
        else:
            embed = discord.Embed(
                title=f"Removed {amount} PokeCoins from {user.name}",
                color=discord.Color.red()
            )
            embed.add_field(name="New Total PokeCoins", value=new_total_coins)
            await ctx.send(embed=embed)

    @tasks.loop(minutes=1)
    async def post_question(self):
        if self.trivia_channel_id:
            channel = self.bot.get_channel(self.trivia_channel_id)
            if channel:
                await self.trivia(None)

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60)

    def get_random_interval(self):
        return random.randint(self.min_question_interval, self.max_question_interval)

    def save_user_info(self):
        pass

    def save_trivia_questions(self):
        # Assuming you have a table for trivia questions
        self.cursor.execute("DELETE FROM trivia_questions")  # Clear the old questions
        for question in self.trivia_questions:
            # Assuming your question is a dict with keys 'question', 'answer', 'category', 'difficulty'
            self.cursor.execute("INSERT INTO trivia_questions VALUES (?, ?, ?, ?)",
                        (question['question'], question['answer'], question['category'], question['difficulty']))
        self.conn.commit()

    async def update_answer_count(self, user, correct):
        uid = str(user.id)
        self.cursor.execute("SELECT right_count, wrong_count FROM user_coins WHERE user_id = ?", (uid,))
        user_data = self.cursor.fetchone()

        if user_data is None:
            right_count = wrong_count = 0
        else:
            right_count, wrong_count = user_data

        if correct:
            right_count += 1
        else:
            wrong_count += 1

        self.cursor.execute("UPDATE user_coins SET right_count = ?, wrong_count = ? WHERE user_id = ?", (right_count, wrong_count, uid))
        self.conn.commit()

def setup(bot):
    bot.add_cog(TriviaGame(bot))