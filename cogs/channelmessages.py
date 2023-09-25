import os
import json
import discord
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
        try:
            with open(self.database_file, 'r') as file:
                sticky_data = json.load(file)
                channels_to_remove = []

                for channel_id, data in sticky_data.items():
                    author_id = data.get("author_id")
                    content = data.get("content")
                    message_id = data.get("message_id")

                    if message_id is None:
                        # Skip messages with None as message_id
                        continue

                    channel = self.bot.get_channel(int(channel_id))
                    if channel:
                        try:
                            message = await channel.fetch_message(message_id)
                        except discord.NotFound:
                            # Message not found, add channel to the list to remove later
                            channels_to_remove.append(channel_id)
                            continue

                        embed = discord.Embed(
                            title="**STICKY NOTE**",
                            description=content,
                            color=discord.Color.random()
                        )

                        # Delete the previous sticky note message
                        if channel.id in self.sticky_messages:
                            prev_sticky_msg = self.sticky_messages[channel.id]
                            await prev_sticky_msg.delete()

                        # Send the new sticky note to the channel
                        sticky_msg = await channel.send(embed=embed)
                        self.sticky_messages[channel.id] = sticky_msg

                        # Update the message ID in the database
                        sticky_data[channel_id]["message_id"] = sticky_msg.id

                # Remove channels marked for removal from the dictionary
                for channel_id in channels_to_remove:
                    del sticky_data[channel_id]

            # Save the updated sticky notes to the database
            with open(self.database_file, 'w') as file:
                json.dump(sticky_data, file, indent=4)
        except FileNotFoundError:
            self.sticky_messages = {}

    async def add_sticky(self, channel, embed):
        # Send the sticky note to the channel
        sticky_msg = await channel.send(embed=embed)
        self.sticky_messages[channel.id] = {
            "message_id": sticky_msg.id,
            "author_id": self.bot.user.id
        }

        self.save_sticky_notes()

    def save_sticky_notes(self):
        sticky_data = {}

        for channel_id, sticky_msg_data in self.sticky_messages.items():
            # Extract relevant information
            author_id = sticky_msg_data["author_id"]
            message_id = sticky_msg_data["message_id"]
            content = sticky_msg_data["content"]

            # Store the data in the dictionary
            sticky_data[channel_id] = {
                "author_id": author_id,
                "content": content,
                "message_id": message_id
            }

        with open(self.database_file, 'w') as file:
            json.dump(sticky_data, file, indent=4)

    @commands.Cog.listener()
    async def on_ready(self):
        # Schedule the loading of sticky notes using asyncio.create_task
        asyncio.create_task(self.load_sticky_notes())

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            # Check if the message is in a channel with a sticky note
            if message.channel.id in self.sticky_messages:
                # Get the original sticky message data
                original_sticky_data = self.sticky_messages[message.channel.id]
                original_sticky_msg_id = original_sticky_data["message_id"]
                original_sticky_msg_author_id = original_sticky_data["author_id"]

                # Check if the original sticky message is not the same as the new message
                if original_sticky_msg_id != message.id:
                    # Verify that the author of the old sticky note matches the bot's user ID
                    if original_sticky_msg_author_id == self.bot.user.id:
                        # Delete the old sticky note
                        channel = message.channel
                        old_sticky_msg = await channel.fetch_message(original_sticky_msg_id)
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
                        self.sticky_messages[message.channel.id]["message_id"] = new_sticky_msg.id

    @commands.command(help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addsticky(self, ctx, channel: discord.TextChannel, *, message):
        formatted_message = f'{message}'

        embed = discord.Embed(
            title="**STICKY NOTE**",
            description=formatted_message,
            color=discord.Color.random()
        )

        sticky_msg = await channel.send(embed=embed)
        self.sticky_messages[channel.id] = {
            "message_id": sticky_msg.id,
            "author_id": self.bot.user.id,
            "content": formatted_message
        }
        self.save_sticky_notes()

        await ctx.send(f"Sticky note added to {channel.mention}.")

    @commands.command(aliases=['delsticky'], help='<#Channel>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removesticky(self, ctx, channel: discord.TextChannel):

        if channel.id in self.sticky_messages:
            sticky_msg = self.sticky_messages.pop(channel.id)
            await sticky_msg.delete()
            # Remove the sticky note entry from the database
            self.save_sticky_notes()
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
        self.sticky_messages[channel.id]["message_id"] = new_sticky_msg.id
        self.sticky_messages[channel.id]["content"] = new_message

        # Save the updated sticky notes to the database
        self.save_sticky_notes()

        await ctx.send(f"Sticky note in {channel.mention} has been edited.")

    @commands.command(aliases=['bd', 'down'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.get_local_time().strftime('%Y-%m-%d %H:%M:%S')
        author = ctx.message.author
        command = ctx.command.name
        print(f"{current_time} - {author.name} used the *{command}* command.")

    @commands.command(aliases=['announce', 'am'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def announcement(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Announcement:**\n{message}")
        await ctx.send(f"Announcement sent to {channel.mention}.")

    def cleanup(self):
        for channel_id, sticky_msg_data in self.sticky_messages.items():
            asyncio.run_coroutine_threadsafe(
                self.bot.get_channel(channel_id).fetch_message(sticky_msg_data["message_id"]).delete(),
                self.bot.loop
            )

    async def on_disconnect(self):
        # Perform cleanup when the bot disconnects
        self.cleanup()

def setup(bot):
    bot.add_cog(StickyNotes(bot))