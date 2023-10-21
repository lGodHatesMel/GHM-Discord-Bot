import os
import json
import asyncio
import datetime
import random

import discord
from discord.ext import commands, tasks

class UserData:
    def __init__(self, right_count=0, wrong_count=0, total_coins=0):
        self.right_count = right_count
        self.wrong_count = wrong_count
        self.total_coins = total_coins

class TriviaGame(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.trivia_channel_id = None
        self.min_question_interval = None
        self.max_question_interval = None
        self.question_message = None
        self.load_trivia_config()
        self.trivia_questions_file = os.path.join('Database', 'coins.json')
        self.load_trivia_questions()

    def load_trivia_questions(self):
        if os.path.exists(self.trivia_questions_file):
            with open(self.trivia_questions_file, 'r') as f:
                file_contents = f.read()
                print("File Contents:", repr(file_contents))

                if not file_contents:
                    self.trivia_questions = {
                    "easy": [
                        {"question": "What is the second Pokémon in the Pokédex?", "answer": "Ivysaur", "reward": 1},
                        {"question": "Which Pokémon evolves into Raichu?", "answer": "Pichu", "reward": 1},
                        {"question": "What is the type of Jigglypuff?", "choices": ["Normal", "Fairy"], "answer": "Normal", "reward": 1},
                        {"question": "Which Pokémon is known for its ability to fly?", "answer": "Pidgey", "reward": 1},
                        {"question": "What is the primary type of Meowth?", "answer": "Normal", "reward": 1},
                        {"question": "Which Pokémon is known for its long, serpentine body?", "answer": "Ekans", "reward": 1},
                        {"question": "What type is Bulbasaur?", "choices": ["Grass", "Poison"], "answer": "Grass", "reward": 1},
                        {"question": "Which Pokémon has the ability to generate electricity in its cheeks?", "answer": "Pichu", "reward": 1},
                        {"question": "What is the evolved form of Magikarp?", "answer": "Gyarados", "reward": 1},
                        {"question": "Which Pokémon has a flame at the end of its tail?", "answer": "Charmander", "reward": 1},
                        {"question": "What is the primary type of Psyduck?", "answer": "Water", "reward": 1},
                        {"question": "Which Pokémon resembles a turtle?", "answer": "Squirtle", "reward": 1},
                        {"question": "What is the first Pokémon Ash caught?", "answer": "Caterpie", "reward": 1},
                        {"question": "Which Pokémon is known for its strong psychic abilities?", "answer": "Abra", "reward": 1},
                        {"question": "What type is Eevee?", "answer": "Normal", "reward": 1},
                    ],
                    "medium": [
                        {"question": "Which Pokémon is known as the 'Shellfish Pokémon'?", "answer": "Shellder", "reward": 2},
                        {"question": "What is the main type advantage of Electric against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Butterfree?", "answer": "Metapod", "reward": 2},
                        {"question": "What is the main type advantage of Grass against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon is known for its ability to paralyze?", "answer": "Pikachu", "reward": 2},
                        {"question": "What is the main type advantage of Ice against Grass?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Wartortle?", "answer": "Squirtle", "reward": 2},
                        {"question": "What is the main type advantage of Fighting against Normal?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Nidoking?", "answer": "Nidorino", "reward": 2},
                        {"question": "What is the main type advantage of Psychic against Poison?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon is known as the 'Gas Pokémon'?", "answer": "Koffing", "reward": 2},
                        {"question": "What is the main type advantage of Ground against Electric?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Jolteon?", "answer": "Eevee", "reward": 2},
                        {"question": "What is the main type advantage of Fairy against Fighting?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon is known for its ability to absorb sunlight?", "answer": "Oddish", "reward": 2},
                    ],
                    "hard": [
                        {"question": "Which Pokémon is known as the 'Cocoon Pokémon'?", "answer": "Metapod", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the sea?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Articuno", "reward": 3},
                        {"question": "Which Pokémon evolves into Dragonair?", "answer": "Dratini", "reward": 3},
                        {"question": "What is the evolved form of Haunter?", "answer": "Gengar", "reward": 3},
                        {"question": "Which Pokémon is known for its ability to manipulate time?", "answer": "Celebi", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the sky?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                        {"question": "Which Pokémon evolves into Tyranitar?", "answer": "Pupitar", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the volcano?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Moltres", "reward": 3},
                        {"question": "Which Pokémon is known for its ability to manipulate space?", "answer": "Palkia", "reward": 3},
                        {"question": "What is the legendary trio of Sinnoh?", "choices": ["Uxie", "Mesprit", "Azelf"], "answer": "Uxie", "reward": 3},
                        {"question": "Which Pokémon evolves into Salamence?", "answer": "Shelgon", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the thunder?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                        {"question": "Which Pokémon is known for its ability to travel between dimensions?", "answer": "Giratina", "reward": 3},
                        {"question": "What is the legendary trio of Johto?", "choices": ["Raikou", "Entei", "Suicune"], "answer": "Raikou", "reward": 3},
                        {"question": "Which Pokémon evolves into Lucario?", "answer": "Riolu", "reward": 3},
                    ],
                }
                else:
                    try:
                        self.trivia_questions = json.loads(file_contents)
                    except json.JSONDecodeError as e:
                        print("Error decoding JSON:", e)
        else:
            self.trivia_questions = {
            "easy": [
                {"question": "What is the second Pokémon in the Pokédex?", "answer": "Ivysaur", "reward": 1},
                {"question": "Which Pokémon evolves into Raichu?", "answer": "Pichu", "reward": 1},
                {"question": "What is the type of Jigglypuff?", "choices": ["Normal", "Fairy"], "answer": "Normal", "reward": 1},
                {"question": "Which Pokémon is known for its ability to fly?", "answer": "Pidgey", "reward": 1},
                {"question": "What is the primary type of Meowth?", "answer": "Normal", "reward": 1},
                {"question": "Which Pokémon is known for its long, serpentine body?", "answer": "Ekans", "reward": 1},
                {"question": "What type is Bulbasaur?", "choices": ["Grass", "Poison"], "answer": "Grass", "reward": 1},
                {"question": "Which Pokémon has the ability to generate electricity in its cheeks?", "answer": "Pichu", "reward": 1},
                {"question": "What is the evolved form of Magikarp?", "answer": "Gyarados", "reward": 1},
                {"question": "Which Pokémon has a flame at the end of its tail?", "answer": "Charmander", "reward": 1},
                {"question": "What is the primary type of Psyduck?", "answer": "Water", "reward": 1},
                {"question": "Which Pokémon resembles a turtle?", "answer": "Squirtle", "reward": 1},
                {"question": "What is the first Pokémon Ash caught?", "answer": "Caterpie", "reward": 1},
                {"question": "Which Pokémon is known for its strong psychic abilities?", "answer": "Abra", "reward": 1},
                {"question": "What type is Eevee?", "answer": "Normal", "reward": 1},
            ],
            "medium": [
                {"question": "Which Pokémon is known as the 'Shellfish Pokémon'?", "answer": "Shellder", "reward": 2},
                {"question": "What is the main type advantage of Electric against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Butterfree?", "answer": "Metapod", "reward": 2},
                {"question": "What is the main type advantage of Grass against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon is known for its ability to paralyze?", "answer": "Pikachu", "reward": 2},
                {"question": "What is the main type advantage of Ice against Grass?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Wartortle?", "answer": "Squirtle", "reward": 2},
                {"question": "What is the main type advantage of Fighting against Normal?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Nidoking?", "answer": "Nidorino", "reward": 2},
                {"question": "What is the main type advantage of Psychic against Poison?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon is known as the 'Gas Pokémon'?", "answer": "Koffing", "reward": 2},
                {"question": "What is the main type advantage of Ground against Electric?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Jolteon?", "answer": "Eevee", "reward": 2},
                {"question": "What is the main type advantage of Fairy against Fighting?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon is known for its ability to absorb sunlight?", "answer": "Oddish", "reward": 2},
            ],
            "hard": [
                {"question": "Which Pokémon is known as the 'Cocoon Pokémon'?", "answer": "Metapod", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the sea?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Articuno", "reward": 3},
                {"question": "Which Pokémon evolves into Dragonair?", "answer": "Dratini", "reward": 3},
                {"question": "What is the evolved form of Haunter?", "answer": "Gengar", "reward": 3},
                {"question": "Which Pokémon is known for its ability to manipulate time?", "answer": "Celebi", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the sky?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                {"question": "Which Pokémon evolves into Tyranitar?", "answer": "Pupitar", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the volcano?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Moltres", "reward": 3},
                {"question": "Which Pokémon is known for its ability to manipulate space?", "answer": "Palkia", "reward": 3},
                {"question": "What is the legendary trio of Sinnoh?", "choices": ["Uxie", "Mesprit", "Azelf"], "answer": "Uxie", "reward": 3},
                {"question": "Which Pokémon evolves into Salamence?", "answer": "Shelgon", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the thunder?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                {"question": "Which Pokémon is known for its ability to travel between dimensions?", "answer": "Giratina", "reward": 3},
                {"question": "What is the legendary trio of Johto?", "choices": ["Raikou", "Entei", "Suicune"], "answer": "Raikou", "reward": 3},
                {"question": "Which Pokémon evolves into Lucario?", "answer": "Riolu", "reward": 3},
            ],
        }

        self.user_coins = {}

        self.post_question.start()

    def load_trivia_config(self):
        config_file = 'config.json'
        with open(config_file, 'r') as f:
            config = json.load(f)
            self.trivia_channel_id = int(config.get('trivia_channel_id', 0))
            self.min_question_interval = config.get('min_question_interval_minutes', 30)
            self.max_question_interval = config.get('max_question_interval_minutes', 60)

    @commands.command(hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def trivia(self, ctx):
        difficulty = random.choice(["easy", "medium", "hard"])
        questions = self.trivia_questions.get(difficulty, [])

        if not questions:
            await ctx.send(f"No {difficulty.capitalize()} questions available.")
            return

        print("Available questions:", questions)

        question_data = random.choice(questions)
        print("Selected question data:", question_data)

        question = question_data.get("question", "")
        answer = question_data.get("answer", "")
        reward = question_data.get("reward", 0)

        choices = question_data.get("choices", [])

        embed = discord.Embed(
            title=f"**Question ({difficulty.capitalize()}):**",
            description=question,
            color=discord.Color.blue()
        )

        if choices:
            choices_str = "\n".join([f"{index + 1}. {choice}" for index, choice in enumerate(choices)])
            embed.add_field(name="Choices", value=choices_str, inline=False)

        embed.set_footer(text="Type your answer in the chat to respond.")
        self.question_message = await ctx.send(embed=embed)

        def check(message):
            return message.author == ctx.author and message.channel == ctx.channel

        print("Before wait_for block")
        try:
            user_response = await self.bot.wait_for('message', check=check, timeout=30)  # Adjust the timeout as needed
        except asyncio.TimeoutError:
            await ctx.send("Time's up! You didn't answer in time.")
            return
        print("After wait_for block")

        uid = str(ctx.author.id)
        user_data = self.user_coins.get(uid, {"coindata": {"right_count": 0, "wrong_count": 0, "total_coins": 0}})

        if user_response.content.lower() == answer.lower():
            user_data["coindata"]["total_coins"] += reward
            user_data["coindata"]["right_count"] += 1
            correct_embed = discord.Embed(
                title="Correct!",
                description=f"You earned {reward} PokeCoins!",
                color=discord.Color.green()
            )
            await ctx.send(embed=correct_embed)

            await ctx.channel.purge()

            embed = discord.Embed(
                title="New Trivia Question Soon",
                description="A new trivia question will be available soon. Get ready!",
                color=discord.Color.blue()
            )
            new_message = await ctx.send(embed=embed)

            await asyncio.sleep(self.get_random_interval())
            await new_message.delete()
            await self.trivia(ctx, difficulty)

        else:
            user_data["coindata"]["wrong_count"] += 1
            incorrect_embed = discord.Embed(
                title="Oops!",
                description=f"The correct answer was {answer}. Better luck next time.",
                color=discord.Color.red()
            )
            await ctx.send(embed=incorrect_embed)

        self.user_coins[uid] = user_data
        print("Before save_user_info")
        self.save_user_info()
        print("After save_user_info")

    @commands.command(hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def pausetrivia(self, ctx, pause_duration: int = 10):
        """
        Pause trivia questions for a specified duration.
        Syntax: !pausetrivia [pause_duration]
        Default duration is 10 minutes.
        """

        if pause_duration <= 0:
            await ctx.send("Pause duration must be a positive integer.")
            return

        # Pause the post_question task
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
        uid = str(ctx.author.id)
        user_data = self.user_coins.get(uid, {"coindata": {"right_count": 0, "wrong_count": 0, "total_coins": 0}})

        embed = discord.Embed(
            title=f"{ctx.author.name}'s PokeCoin Info:",
            color=discord.Color.gold()
        )

        embed.add_field(name="PokeCoins", value=user_data['coindata']['total_coins'])
        embed.add_field(name="Correct Answers", value=user_data['coindata']['right_count'])
        embed.add_field(name="Wrong Answers", value=user_data['coindata']['wrong_count'])

        await ctx.send(embed=embed)

    @commands.command(help='<uid>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def usercoins(self, ctx, uid: int):
        uid_str = str(uid)
        user_data = self.user_coins.get(uid_str, {"coindata": {"right_count": 0, "wrong_count": 0, "total_coins": 0}})

        embed = discord.Embed(
            title=f"User {uid}'s PokeCoin Info:",
            color=discord.Color.gold()
        )

        embed.add_field(name="PokeCoins", value=user_data['coindata']['total_coins'])
        embed.add_field(name="Correct Answers", value=user_data['coindata']['right_count'])
        embed.add_field(name="Wrong Answers", value=user_data['coindata']['wrong_count'])

        await ctx.send(embed=embed)

    @commands.command(help='<uid_or_user> <amount>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def givecoins(self, ctx, user: discord.User, amount: int):
        uid = str(user.id)
        user_data = self.user_coins.get(uid, {"coindata": {"right_count": 0, "wrong_count": 0, "total_coins": 0}})
        user_data['coindata']['total_coins'] += amount
        self.user_coins[uid] = user_data
        print("Before save_user_info")
        self.save_user_info()
        print("After save_user_info")

        embed = discord.Embed(
            title=f"Gave {amount} PokeCoins to {user.name}",
            color=discord.Color.green()
        )

        embed.add_field(name="New Total PokeCoins", value=user_data['coindata']['total_coins'])
        await ctx.send(embed=embed)

    @commands.command(help='<uid_or_user> <amount>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removecoins(self, ctx, user: discord.User, amount: int):
        uid = str(user.id)
        user_data = self.user_coins.get(uid, {"coindata": {"right_count": 0, "wrong_count": 0, "total_coins": 0}})

        # Check if there are enough coins to remove
        if user_data['coindata']['total_coins'] >= amount:
            user_data['coindata']['total_coins'] -= amount
            self.user_coins[uid] = user_data
            print("Before save_user_info")
            self.save_user_info()
            print("After save_user_info")

            embed = discord.Embed(
                title=f"Removed {amount} PokeCoins from {user.name}",
                color=discord.Color.red()
            )

            embed.add_field(name="New Total PokeCoins", value=user_data['coindata']['total_coins'])
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"{user.name} doesn't have enough PokeCoins to remove {amount}.")

    @tasks.loop(minutes=1)
    async def post_question(self):
        if self.trivia_channel_id:
            channel = self.bot.get_channel(self.trivia_channel_id)
            if channel:
                # Get the last message in the channel
                last_message = await channel.history(limit=1).flatten()
                if last_message:
                    ctx = await self.bot.get_context(last_message[0])
                    await self.bot.invoke(self.bot.get_command('trivia'), ctx)

    @post_question.before_loop
    async def before_post_question(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60)

    def get_random_interval(self):
        return random.randint(self.min_question_interval, self.max_question_interval)

    def save_user_info(self):
        print("save_user_info() called")
        db_file = os.path.join('Database', 'coins.json')

        filtered_user_info = {uid: data for uid, data in self.user_coins.items() if data["total_coins"] > 0}

        with open(db_file, 'w') as f:
            json.dump(
                filtered_user_info,
                f,
                indent=4,
                default=lambda o: o.isoformat() if isinstance(o, datetime.datetime) else None,
            )
            print("User CoinData saved successfully.")

    def save_trivia_questions(self):
        with open(self.trivia_questions_file, 'w') as f:
            json.dump(self.trivia_questions, f, indent=4)

def setup(bot):
    bot.add_cog(TriviaGame(bot))