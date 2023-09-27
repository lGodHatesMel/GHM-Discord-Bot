import os
import json
import discord
from pathlib import Path
from discord.ext import commands
import asyncio
import utils

class StickyNotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sticky_messages = {}
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
                    # Skip messages with None as message
                    continue

                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    embed = discord.Embed(
                        title="**STICKY NOTE**",
                        description=content,
                        color=discord.Color.random()
                    )

                    # Send the sticky note to the channel
                    sticky_msg = await channel.send(embed=embed)
                    self.sticky_messages[int(channel_id)] = {
                        "message": sticky_msg,
                        "author_id": int(author_id),
                        "content": content
                    }

    async def save_sticky_notes(self):
        sticky_data = {}
        for channel_id, data in self.sticky_messages.items():
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
        for channel_id, data in self.sticky_messages.items():
            asyncio.run_coroutine_threadsafe(
                data["message"].delete(),
                self.bot.loop
            )

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            try:
                # Check if the message is in a channel with a sticky note
                if message.channel.id in self.sticky_messages:
                    # Get the original sticky message data
                    original_sticky_data = self.sticky_messages[message.channel.id]
                    original_sticky_msg_id = original_sticky_data["message"].id
                    original_sticky_msg_author_id = original_sticky_data["author_id"]

                    # Check if the original sticky message is not the same as the new message
                    if original_sticky_msg_id != message.id:
                        # Verify that the author of the old sticky note matches the bot's user ID
                        if original_sticky_msg_author_id == self.bot.user.id:
                            # Attempt to fetch the old sticky note
                            channel = message.channel
                            try:
                                old_sticky_msg = await channel.fetch_message(original_sticky_msg_id)
                            except discord.NotFound:
                                # Message not found, it might have been deleted
                                old_sticky_msg = None

                            await asyncio.sleep(2.5)

                            # Delete the old sticky note if it exists
                            if old_sticky_msg:
                                await old_sticky_msg.delete()

                            # Create a new embedded sticky note with the original content
                            new_embed = discord.Embed(
                                title="**STICKY NOTE**",
                                description=original_sticky_data["content"],
                                color=discord.Color.random()
                            )

                            # Send the new embedded sticky note
                            new_sticky_msg = await message.channel.send(embed=new_embed)
                            # Update the reference to the sticky message
                            self.sticky_messages[message.channel.id]["message"] = new_sticky_msg

            except Exception as e:
                print(f"An error occurred in on_message: {e}")

    @commands.command(help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addsticky(self, ctx, channel: discord.TextChannel, *, message):
        formatted_message = f'{message}'

        embed = discord.Embed(
            title="**STICKY NOTE**",
            description=formatted_message,
            color=discord.Color.random()
        )

        # Check if there's an existing sticky in the channel
        if channel.id in self.sticky_messages:
            prev_sticky_msg = self.sticky_messages[channel.id]["message"]
            await prev_sticky_msg.delete()  # Delete the old sticky message

        sticky_msg = await channel.send(embed=embed)
        self.sticky_messages[channel.id] = {
            "message": sticky_msg,
            "author_id": self.bot.user.id,
            "content": formatted_message
        }
        await self.save_sticky_notes()  # Await the save_sticky_notes coroutine

        await ctx.send(f"Sticky note added to {channel.mention}.")

    @commands.command(aliases=['delsticky'], help='<#Channel>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removesticky(self, ctx, channel: discord.TextChannel):

        if channel.id in self.sticky_messages:
            sticky_msg = self.sticky_messages.pop(channel.id)["message"]
            await sticky_msg.delete()
            # Remove the sticky note entry from the database
            await self.save_sticky_notes()
            await ctx.send(f"Sticky note removed from {channel.mention}.")
        else:
            await ctx.send(f"No sticky note found in {channel.mention}.")

    @commands.command(help='<#Channel> <New Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def editsticky(self, ctx, channel: discord.TextChannel, *, new_message):
        if channel.id not in self.sticky_messages:
            return await ctx.send(f"No sticky note found in {channel.mention}.")

        original_sticky_msg_data = self.sticky_messages[channel.id]

        # Edit the existing sticky message's description
        original_sticky_msg_content = original_sticky_msg_data["content"]
        original_sticky_msg_embed = discord.Embed(
            title="**STICKY NOTE**",
            description=new_message,
            color=discord.Color.random()
        )

        # Send the new embedded sticky note
        new_sticky_msg = await channel.send(embed=original_sticky_msg_embed)
        # Update the reference to the sticky message
        self.sticky_messages[channel.id]["message"] = new_sticky_msg
        self.sticky_messages[channel.id]["content"] = new_message

        # Save the updated sticky notes to the database
        await self.save_sticky_notes()

        await ctx.send(f"Sticky note in {channel.mention} has been edited.")

    @commands.command(aliases=['bd'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')
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