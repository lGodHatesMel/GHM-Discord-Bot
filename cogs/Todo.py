import time
import json
import sqlite3
import discord
from discord.ext import commands

TICK_EMOJI = "✅"
TODO_ARROW_EMOJI = "➡️"

class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.conn = sqlite3.connect('Database/todo.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS todo
            (unique_id integer primary key, user_id text, time text, task text, subtasks text)''')

    @commands.command(help="Shows todo commands.", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def todo(self, ctx: commands.Context):
        embed = discord.Embed(title="Todo Commands", color=discord.Color.blue())
        embed.add_field(name="!show", value="Shows your todo list. Each task has an ID which is used for other commands.", inline=False)
        embed.add_field(name="!add [task]", value="Adds a task to your todo list. Replace [task] with the task you want to add.", inline=False)
        embed.add_field(name="!remove [id]", value="Removes a task from your todo list using its ID. Replace [id] with the ID of the task you want to remove.", inline=False)
        embed.add_field(name="!clear", value="Clears your todo list. This will remove all tasks from your list.", inline=False)
        embed.add_field(name="!addsub [id] [subtask]", value="Adds a subtask to a task. Replace [id] with the ID of the task and [subtask] with the subtask you want to add.", inline=False)
        embed.add_field(name="!completesub [id] [subtask]", value="Marks a subtask as completed. Replace [id] with the ID of the task and [subtask] with the subtask you want to mark as completed.", inline=False)
        await ctx.send(embed=embed)

    @commands.command(help="Shows your todo list.", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def show(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT * FROM todo WHERE user_id = ?", (user_id,))
        res = self.cursor.fetchall()
        if not res:
            embed = discord.Embed(description="Your todo list is empty!", color=discord.Color.red())
        else:
            embed = discord.Embed(title="Your Todo List", color=discord.Color.green())
            for row in res:
                embed.add_field(name=f"ID: {row[0]}", value=row[3], inline=False)
        await ctx.send(embed=embed)

    @commands.command(help='<Task>', hidden=True)
    @commands.is_owner()
    async def add(self, ctx: commands.Context, *, task: str):
        user_id = str(ctx.author.id)
        _t = int(time.time())
        self.cursor.execute("INSERT INTO todo(user_id, time, task) VALUES (?, ?, ?)", (user_id, _t, task))
        self.conn.commit()
        embed = discord.Embed(description=f"{TICK_EMOJI} Added `{task}` to your todo list.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(help='<ID>', hidden=True)
    @commands.is_owner()
    async def remove(self, ctx: commands.Context, unique_id: int):
        self.cursor.execute("DELETE FROM todo WHERE unique_id = ?", (unique_id,))
        self.conn.commit()
        embed = discord.Embed(description=f"{TICK_EMOJI} Removed task with ID `{unique_id}` from your todo list.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(help="Clears your todo list.", hidden=True)
    @commands.is_owner()
    async def clearlist(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        self.cursor.execute("DELETE FROM todo WHERE user_id = ?", (user_id,))
        self.conn.commit()
        embed = discord.Embed(description=f"{TICK_EMOJI} Cleared your todo list.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(help='<ID> <Subtask>', hidden=True)
    @commands.is_owner()
    async def addsub(self, ctx: commands.Context, unique_id: int, *, subtask: str):
        self.cursor.execute("SELECT subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None:
            embed = discord.Embed(description="Task not found!", color=discord.Color.red())
        else:
            subtasks = res[0] + f", {subtask}" if res[0] else subtask
            self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
            self.conn.commit()
            embed = discord.Embed(description=f"{TICK_EMOJI} Added subtask `{subtask}` to task with ID `{unique_id}`.", color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(help='<ID> <Subtask>', hidden=True)
    @commands.is_owner()
    async def completesub(self, ctx: commands.Context, unique_id: int, subtask: str):
        self.cursor.execute("SELECT subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None:
            embed = discord.Embed(description="Task not found!", color=discord.Color.red())
        else:
            subtasks = res[0].replace(subtask, f"{TICK_EMOJI} {subtask}")
            self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
            self.conn.commit()
            embed = discord.Embed(description=f"{TICK_EMOJI} Completed subtask `{subtask}` in task with ID `{unique_id}`.", color=discord.Color.green())
        await ctx.send(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Todo(bot))