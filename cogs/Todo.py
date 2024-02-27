import time
import json
import sqlite3
import discord
from discord.ext import commands

TICK_EMOJI = "✅"
X_EMOJI = "❌"
TODO_ARROW_EMOJI = "➡️"

class Todo(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.conn = sqlite3.connect('Database/todo.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS todo
            (unique_id integer primary key, user_id text, time text, task text, subtasks text)''')

    @commands.command(help="Shows todo commands.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def todocommands(self, ctx: commands.Context):
        with open('config.json') as f:
            config = json.load(f)
        prefix = config['prefix']

        embed = discord.Embed(title="Todo Commands", color=discord.Color.blue())
        embed.add_field(name=f"`{prefix}showalltasks`", value="*Shows all tasks from database.*", inline=False)
        embed.add_field(name=f"`{prefix}showtask`", value="*Shows your todo list. Each task has an ID which is used for other commands.*", inline=False)
        embed.add_field(name=f"`{prefix}addtask [name]`", value="*Adds a task to your todo list. Replace [task] with the task you want to add.*", inline=False)
        embed.add_field(name=f"`{prefix}removetask [id]`", value="*Removes a task from your todo list using its ID. Replace [id] with the ID of the task you want to remove.*", inline=False)
        embed.add_field(name=f"`{prefix}cleartask`", value="*Clears your todo list. This will remove all tasks from your list.*", inline=False)
        embed.add_field(name=f"`{prefix}addsubtask [id] [name] | [note]`", value="*Adds a subtask to a task. Replace [id] with the ID of the task and [subtask] with the subtask you want to add.*", inline=False)
        embed.add_field(name=f"`{prefix}removesubtask [id] [name]`", value="*Adds a subtask to a task. Replace [id] with the ID of the task and [subtask] with the subtask you want to remove.*", inline=False)
        embed.add_field(name=f"`{prefix}completesubtask [id] [name]`", value="*Marks a subtask as completed. Replace [id] with the ID of the task and [subtask] with the subtask you want to mark as completed.*", inline=False)
        embed.add_field(name=f"`{prefix}cancelsubtask [id] [name]`", value="*Cancels a subtask. Replace [id] with the ID of the task and [subtask] with the subtask you want to cancel.*", inline=False)
        embed.add_field(name=f"`{prefix}prioritizesubtask [id] [name]`", value="*Prioritizes a subtask. Replace [id] with the ID of the task and [subtask] with the subtask you want to prioritize.*", inline=False)
        await ctx.send(embed=embed)

    @commands.command(help="<id>", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def showtask(self, ctx: commands.Context, unique_id: int):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT * FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if not res or (res[1] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to view this task!", color=discord.Color.red())
        else:
            task = "__" + res[3] + "__"
            subtasks = res[4]
            creator_id = res[1]
            creator = self.bot.get_user(int(creator_id))
            if subtasks:
                task += "\n\n**Check List:**\n" + "\n".join(subtasks.split(", "))
            embed = discord.Embed(title=task, description="", color=discord.Color.green())
            embed.set_author(name=f"Task created by {creator.name}", icon_url=creator.avatar_url)
            embed.set_footer(text=f"Task ID: {res[0]}")
        await ctx.message.reply(embed=embed)

    @commands.command(help="Shows all tasks from your todo list.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def showalltasks(self, ctx: commands.Context):
        self.cursor.execute("SELECT * FROM todo")
        res = self.cursor.fetchall()
        if not res:
            embed = discord.Embed(description="No tasks found!", color=discord.Color.red())
        else:
            embed = discord.Embed(title="All Tasks", color=discord.Color.green())
            for row in res:
                task = row[3]
                creator_id = row[1]
                creator = self.bot.get_user(int(creator_id))
                if creator:
                    creator_name = creator.name
                else:
                    creator_name = "Unknown"
                embed.add_field(name=f"ID: {row[0]}", value=f"Task: {task}\nCreator: {creator_name}", inline=False)
        await ctx.message.reply(embed=embed)

    @commands.command(help='<Task>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addtask(self, ctx: commands.Context, *, task: str):
        user_id = str(ctx.author.id)
        _t = int(time.time())
        self.cursor.execute("INSERT INTO todo(user_id, time, task, subtasks) VALUES (?, ?, ?, ?)", (user_id, _t, task, ""))
        self.conn.commit()
        embed = discord.Embed(description=f"{TICK_EMOJI} Created new todo list `{task}`.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

    @commands.command(help="<id>", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def removetask(self, ctx: commands.Context, unique_id: int):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to remove this task!", color=discord.Color.red())
        else:
            self.cursor.execute("DELETE FROM todo WHERE unique_id = ?", (unique_id,))
            self.conn.commit()
            embed = discord.Embed(description=f"{TICK_EMOJI} Removed task with ID `{unique_id}` from your todo list.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

    @commands.command(help="Clears a specific task from your todo list.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def cleartask(self, ctx: commands.Context, unique_id: int):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to clear this task!", color=discord.Color.red())
        else:
            self.cursor.execute("DELETE FROM todo WHERE unique_id = ?", (unique_id,))
            self.conn.commit()
            embed = discord.Embed(description=f"{TICK_EMOJI} Cleared task with ID `{unique_id}` from your todo list.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

    @commands.command(help='<ID> <Subtask> | <Note>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addsubtask(self, ctx: commands.Context, unique_id: int, *, subtask: str):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id, subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to add a subtask to this task!", color=discord.Color.red())
        else:
            subtask_name, note = subtask.split('|', 1) if '|' in subtask else (subtask, '')
            subtask_name = subtask_name.strip()
            note = note.strip()
            subtask = f"☐ {subtask_name} {note}"
            subtasks = res[1] + f", {subtask}" if res[1] else subtask
            self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
            self.conn.commit()
            embed = discord.Embed(description=f"{TICK_EMOJI} Added task `{subtask}` to todo list with ID `{unique_id}`.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

    @commands.command(help='<ID> <Subtask>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def removesubtask(self, ctx: commands.Context, unique_id: int, *, subtask: str):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id, subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to remove a subtask from this task!", color=discord.Color.red())
        else:
            subtasks = res[1].split(', ')
            subtask = next((s for s in subtasks if subtask.strip() in s), None)
            if subtask:
                subtasks.remove(subtask)
                self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (', '.join(subtasks), unique_id))
                self.conn.commit()
                embed = discord.Embed(description=f"{TICK_EMOJI} Removed subtask `{subtask}` from todo list with ID `{unique_id}`.", color=discord.Color.green())
            else:
                embed = discord.Embed(description="Subtask not found!", color=discord.Color.red())
        await ctx.message.reply(embed=embed)

    @commands.command(help='<ID> <Subtask>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def completesubtask(self, ctx: commands.Context, unique_id: int, *, subtask: str):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id, subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to complete this subtask!", color=discord.Color.red())
        else:
            subtasks = res[1].replace(f"☐ {subtask}", f"{TICK_EMOJI} {subtask}")
            self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
            self.conn.commit()
            embed = discord.Embed(description=f"{TICK_EMOJI} Completed subtask `{subtask}` in task with ID `{unique_id}`.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

    @commands.command(help='<ID> <Subtask>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def cancelsubtask(self, ctx: commands.Context, unique_id: int, *, subtask: str):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id, subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to cancel this subtask!", color=discord.Color.red())
        else:
            subtasks = res[1].replace(f"☐ {subtask}", f"{X_EMOJI} {subtask}")
            self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
            self.conn.commit()
            embed = discord.Embed(description=f"{X_EMOJI} Cancelled subtask `{subtask}` in task with ID `{unique_id}`.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

    @commands.command(help='<ID> <Subtask>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def prioritizesubtask(self, ctx: commands.Context, unique_id: int, *, subtask: str):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id, subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to prioritize this subtask!", color=discord.Color.red())
        else:
            subtasks = res[1].replace(f"☐ {subtask}", f"{TODO_ARROW_EMOJI} ☐ {subtask}")
            self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
            self.conn.commit()
            embed = discord.Embed(description=f"{TODO_ARROW_EMOJI} Prioritized subtask `{subtask}` in task with ID `{unique_id}`.", color=discord.Color.green())
        await ctx.message.reply(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Todo(bot))