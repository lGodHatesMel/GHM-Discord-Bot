import discord
from discord.ext import commands
from utils.Paginator import Paginator
from config import PREFIX
import time
import sqlite3


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
        embed = discord.Embed(title="Todo Commands", color=discord.Color.blue())
        embed.add_field(name=f"`{PREFIX}showalltasks`", value="*Shows all tasks from database.*", inline=False)
        embed.add_field(name=f"`{PREFIX}showallmytasks`", value="*Shows all your tasks from the todo list.*", inline=False)
        embed.add_field(name=f"`{PREFIX}showtask [id]`", value="*Shows your todo list. Each task has an ID which is used for other commands.*", inline=False)
        embed.add_field(name=f"`{PREFIX}addtask [name]`", value="*Adds a task to your todo list. Replace [task] with the task you want to add.*", inline=False)
        embed.add_field(name=f"`{PREFIX}removetask [id]`", value="*Removes a task from your todo list using its ID. Replace [id] with the ID of the task you want to remove.*", inline=False)
        embed.add_field(name=f"`{PREFIX}clearmytasks`", value="*Clears your todo list. This will remove all tasks from your list.*", inline=False)
        embed.add_field(name=f"`{PREFIX}addsubtask [id] [name] | [note]`", value="*Adds a subtask to a task. Replace [id] with the ID of the task and [subtask] with the subtask you want to add.*", inline=False)
        embed.add_field(name=f"`{PREFIX}removesubtask [id] [name]`", value="*Adds a subtask to a task. Replace [id] with the ID of the task and [subtask] with the subtask you want to remove.*", inline=False)
        embed.add_field(name=f"`{PREFIX}completesubtask [id] [name]`", value="*Marks a subtask as completed. Replace [id] with the ID of the task and [subtask] with the subtask you want to mark as completed.*", inline=False)
        embed.add_field(name=f"`{PREFIX}cancelsubtask [id] [name]`", value="*Cancels a subtask. Replace [id] with the ID of the task and [subtask] with the subtask you want to cancel.*", inline=False)
        embed.add_field(name=f"`{PREFIX}setsubstatus [id] [name] [action]`", value="*Set status of a subtask. Replace [id] with the ID of the task and [subtask] with the subtask you want to prioritize.*", inline=False)
        await ctx.send(embed=embed)

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
                subtasks_list = subtasks.split(", ")
                formatted_subtasks = "\n".join(subtasks_list)
                task += "\n\n**Check List:**\n" + formatted_subtasks
            task = task[:1024]
            embed = discord.Embed(title=task, description="", color=discord.Color.green())
            embed.set_author(name=f"Task created by {creator.name}", icon_url=creator.avatar_url)
            embed.set_footer(text=f"Task ID: {res[0]}")
        await ctx.message.reply(embed=embed)

    @commands.command(help="Shows all your tasks from the todo list.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def showallmytasks(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT * FROM todo WHERE user_id = ?", (user_id,))
        res = self.cursor.fetchall()
        if not res:
            embed = discord.Embed(description="No tasks found!", color=discord.Color.red())
            await ctx.message.reply(embed=embed)
        else:
            embeds = []
            for i, row in enumerate(res):
                task = "__" + row[3] + "__"
                subtasks = row[4]
                task = task[:1024]
                if subtasks:
                    subtasks_list = subtasks.split(", ")
                    formatted_subtasks = "\n".join(subtasks_list)[:1024]
                    task += "\n\n**Check List:**\n" + formatted_subtasks
                embed = discord.Embed(title=f"ID: {row[0]}", description=task, color=discord.Color.green())
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                if len(res) > 1:
                    embed.set_footer(text=f"Page {i+1} of {len(res)}. Use the emojis to navigate through the tasks.")
                else:
                    embed.set_footer(text="Use the emojis to navigate through the tasks.")
                embeds.append(embed)
            paginator = Paginator(ctx, embeds)
            await paginator.start()

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

    @commands.command(help="Clears all tasks from your todo list.", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def clearmytasks(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        self.cursor.execute("DELETE FROM todo WHERE user_id = ?", (user_id,))
        self.conn.commit()
        embed = discord.Embed(description=f"{TICK_EMOJI} Cleared all tasks from your todo list.", color=discord.Color.green())
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
            note = '- Note: ' + note.strip() if note else ''
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

    @commands.command(help='<ID> <Subtask> <Action>', hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def setsubstatus(self, ctx: commands.Context, unique_id: int, subtask: str, action: str):
        user_id = str(ctx.author.id)
        self.cursor.execute("SELECT user_id, subtasks FROM todo WHERE unique_id = ?", (unique_id,))
        res = self.cursor.fetchone()
        if res is None or (res[0] != user_id and not await self.bot.is_owner(ctx.author)):
            embed = discord.Embed(description="Task not found or you don't have permission to modify this subtask!", color=discord.Color.red())
        else:
            if action.lower() == "prioritize":
                subtasks = res[1].replace(f"☐ {subtask}", f"☐ {subtask} ⭐")
                self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
                self.conn.commit()
                embed = discord.Embed(description=f"⭐ Prioritized subtask `{subtask}` in task with ID `{unique_id}`.", color=discord.Color.green())
            elif action.lower() == "testing":
                subtasks = res[1].replace(f"☐ {subtask}", f"☐ {subtask} 🧪")
                self.cursor.execute("UPDATE todo SET subtasks = ? WHERE unique_id = ?", (subtasks, unique_id))
                self.conn.commit()
                embed = discord.Embed(description=f"🧪 Set subtask `{subtask}` to testing in task with ID `{unique_id}`.", color=discord.Color.green())
            else:
                embed = discord.Embed(description="Invalid action! Please specify either 'prioritize' or 'testing'.", color=discord.Color.red())
        await ctx.message.reply(embed=embed)

def setup(bot: commands.Bot):
    bot.add_cog(Todo(bot))