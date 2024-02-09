import os
import json
import discord
from pathlib import Path
from discord.ext import commands
import asyncio
import utils
import logging

class StickyNotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.StickyMsg = {}
        self.database_folder = 'Database'
        self.database_file = os.path.join(self.database_folder, 'sticky_notes.json')

    async def load_sticky_notes(self):
        file = Path(self.database_file)

        if not file.exists():
            return

        with file.open() as f:
            sticky_data = json.load(f)
            for channel_id, data in sticky_data.items():
                author_id = data.get("author_id")
                content = data.get("content")
                message = data.get("message")

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

    async def save_sticky_notes(self):
        sticky_data = {}
        for channel_id, data in self.StickyMsg.items():
            sticky_data[channel_id] = {
                "message": data["message"].id,
                "author_id": data["author_id"],
                "content": data["content"]
            }

        with open(self.database_file, 'w') as file:
            json.dump(sticky_data, file, indent=4)

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
                await self.GreetingMessage(message)
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

    async def GreetingMessage(self, message):
        words = message.content.lower().split()
        if "hello" in words or "hey" in words:
            await message.reply(f"Hello, {message.author.mention}!")

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

    @commands.command(aliases=['bd'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.GetLocalTime().strftime('%Y-%m-%d %H:%M:%S')
        author = ctx.message.author
        command = ctx.command.name
        print(f"{current_time} - {author.name} used the *{command}* command.")

    @commands.command(aliases=['announce', 'ann'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def announcement(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Announcement:**\n{message}")
        await ctx.send(f"Announcement sent to {channel.mention}.")

def setup(bot):
    bot.add_cog(StickyNotes(bot))