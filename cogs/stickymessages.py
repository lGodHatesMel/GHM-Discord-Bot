import os
import sqlite3
import discord
from pathlib import Path
from discord.ext import commands
import asyncio
import logging

class StickyMessages(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.StickyMsg = {}
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'sticky_notes.db')

    async def load_sticky_notes(self):
        file = Path(self.database_file)

        if not file.exists():
            return

        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute("SELECT * FROM sticky_notes")
        sticky_data = c.fetchall()
        for channel_id, author_id, content, message in sticky_data:
            if message is None:
                continue

            channel = self.bot.get_channel(int(channel_id))
            if channel:
                embed = discord.Embed(
                    title="**STICKY NOTE**",
                    description=content,
                    color=discord.Color.random()
                )

                StickyMsg = await channel.send(embed=embed)
                self.StickyMsg[int(channel_id)] = {
                    "message": StickyMsg,
                    "author_id": int(author_id),
                    "content": content
                }
        conn.close()

    async def save_sticky_notes(self):
        conn = sqlite3.connect(self.database_file)
        c = conn.cursor()
        c.execute("CREATE TABLE IF NOT EXISTS sticky_notes (channel_id INTEGER, author_id INTEGER, content TEXT, message INTEGER)")
        c.execute("DELETE FROM sticky_notes")
        for channel_id, data in self.StickyMsg.items():
            c.execute("INSERT INTO sticky_notes VALUES (?,?,?,?)", (channel_id, data["author_id"], data["content"], data["message"].id))
        conn.commit()
        conn.close()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.load_sticky_notes()
        self.cleanup()
        
    def cleanup(self):
        for channel_id, data in self.StickyMsg.items():
            asyncio.run_coroutine_threadsafe(
                data["message"].delete(),
                self.bot.loop
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            try:
                await self.StickyMessages(message)
            except Exception as e:
                logging.error(f"An error occurred in on_message: {e}")

    async def StickyMessages(self, message):
        if message.channel.id in self.StickyMsg:
            OriginalStickyData = self.StickyMsg[message.channel.id]
            OriginalStickyMsgID = OriginalStickyData["message"].id
            OriginalStickyMsgAuthorID = OriginalStickyData["author_id"]

            if OriginalStickyMsgID != message.id:
                if OriginalStickyMsgAuthorID == self.bot.user.id:
                    channel = message.channel
                    try:
                        OldStickyMsg = await channel.fetch_message(OriginalStickyMsgID)
                    except discord.NotFound:
                        OldStickyMsg = None

                    await asyncio.sleep(2.5)

                    if OldStickyMsg:
                        await OldStickyMsg.delete()

                    new_embed = discord.Embed(
                        title="**STICKY NOTE**",
                        description=OriginalStickyData["content"],
                        color=discord.Color.random()
                    )

                    NewStickyMsg = await message.channel.send(embed=new_embed)
                    self.StickyMsg[message.channel.id]["message"] = NewStickyMsg

    @commands.command(help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addsticky(self, ctx, channel: discord.TextChannel, *, message):
        formatted_message = f'{message}'

        embed = discord.Embed(
            title="**STICKY NOTE**",
            description=formatted_message,
            color=discord.Color.random()
        )

        if channel.id in self.StickyMsg:
            PrevStickyMsg = self.StickyMsg[channel.id]["message"]
            await PrevStickyMsg.delete()

        StickyMsg = await channel.send(embed=embed)
        self.StickyMsg[channel.id] = {
            "message": StickyMsg,
            "author_id": self.bot.user.id,
            "content": formatted_message
        }
        await self.save_sticky_notes()

        await ctx.send(f"Sticky note added to {channel.mention}.")

    @commands.command(aliases=['delsticky'], help='<#Channel>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removesticky(self, ctx, channel: discord.TextChannel):

        if channel.id in self.StickyMsg:
            StickyMsg = self.StickyMsg.pop(channel.id)["message"]
            await StickyMsg.delete()
            await self.save_sticky_notes()
            await ctx.send(f"Sticky note removed from {channel.mention}.")
        else:
            await ctx.send(f"No sticky note found in {channel.mention}.")

    @commands.command(help='<#Channel> <New Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def editsticky(self, ctx, channel: discord.TextChannel, *, new_message):
        if channel.id not in self.StickyMsg:
            return await ctx.send(f"No sticky note found in {channel.mention}.")

        OriginaStickyMsgData = self.StickyMsg[channel.id]

        OriginalStickyMsgContent = OriginaStickyMsgData["content"]
        OriginalStickyMsgEmbed = discord.Embed(
            title="**STICKY NOTE**",
            description=new_message,
            color=discord.Color.random()
        )

        NewStickyMsg = await channel.send(embed=OriginalStickyMsgEmbed)
        self.StickyMsg[channel.id]["message"] = NewStickyMsg
        self.StickyMsg[channel.id]["content"] = new_message

        await self.save_sticky_notes()

        await ctx.send(f"Sticky note in {channel.mention} has been edited.")

def setup(bot):
    bot.add_cog(StickyMessages(bot))