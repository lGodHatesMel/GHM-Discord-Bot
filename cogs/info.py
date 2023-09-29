import os
import asyncio
import json
import random
import discord
from discord.ext import commands

class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.info_aliases = {}
        database_folder = 'Database'
        self.json_file = os.path.join(database_folder, 'info.json')
        self.aliases_file = os.path.join(database_folder, 'info_aliases.json')

        if os.path.exists(self.aliases_file):
            with open(self.aliases_file, 'r') as f:
                self.info_aliases = json.load(f)

    def save_aliases(self):
        with open(self.aliases_file, 'w') as f:
            json.dump(self.info_aliases, f, indent=4)

    async def update_info(self, ctx):
        info_channel_id = self.bot.config.get('info_channel_id')

        if info_channel_id is None:
            await ctx.send("⚠ INFO channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        info_channel = ctx.guild.get_channel(info_channel_id)

        if not info_channel:
            await ctx.send("⚠ INFO channel not found. Make sure 'info_channel_id' in config.json points to a valid channel.")
            return

        with open(self.json_file, "r") as f:
            info_db = json.load(f)
        messages = []
        for info_name, entry in info_db.items():
            embed = discord.Embed(color=discord.Color.red())
            embed.title = f"INFO {info_name.upper()}"
            embed.add_field(name="Question:", value=entry['question'], inline=False)
            embed.add_field(name="Information:", value=f"{entry['information']}", inline=False)
            aliases = []
            for word, info in self.info_aliases.items():
                if info == info_name:
                    aliases.append(word)
            if aliases:
                embed.set_footer(text="Aliases: " + ", ".join(aliases))
            messages.append(embed)
        
        for message in messages:
            existing_message = None
            async for msg in info_channel.history(limit=100):
                if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == message.title:
                    existing_message = msg
                    break
            
            if existing_message:
                await existing_message.edit(embed=message)
            else:
                await info_channel.send(embed=message)

        self.save_aliases()

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def addinfo(self, ctx):
        info_channel_id = self.bot.config.get('info_channel_id')

        if info_channel_id is None:
            await ctx.send("⚠ INFO channel ID is not set in config.json. Set it to a valid channel ID to use this feature.")
            return

        info_channel = ctx.guild.get_channel(info_channel_id)

        if not info_channel:
            await ctx.send("⚠ INFO channel not found. Make sure 'info_channel_id' in config.json points to a valid channel.")
            return

        await ctx.send("Type the bot command name for this INFO entry (no spaces or special characters), or type `cancel` to cancel:")

        try:
            name = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            name = name.content.lower()
            if name == "cancel":
                return await ctx.send("❌ Canceled by user.")
            
            await ctx.send("Type the question to be added after this message:")

            question = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=60.0)
            question_content = question.content

            await ctx.send("Type the information after this message:")

            info = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=60.0)
            info_content = info.content

        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")

        if len("❔ QX. __{}__\n{}".format(question_content, info_content)) > 1950:
            return await ctx.send("⚠ This INFO entry is too long.")

        with open(self.json_file, "r") as f:
            info_db = json.load(f)

        if name in info_db:
            return await ctx.send("⚠ This name is already in use for another INFO entry.")

        info_db[name] = {
            "question": question_content,
            "information": info_content
        }

        with open(self.json_file, "w") as f:
            json.dump(info_db, f, indent=4)

        await ctx.send("✅ Entry added.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(aliases=['infoaddaliases'], hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def infoalias(self, ctx, info_name: str = "", *, words: str = ""):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        for word in words.strip().split():
            self.info_aliases[word] = info_name
        with open(self.aliases_file, "w") as f:
            json.dump(self.info_aliases, f, indent=4)
        await ctx.send("✅ Alias added/updated.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deletealias(self, ctx, word: str):
        if word not in self.info_aliases:
            return await ctx.send("⚠ INFO alias does not exist.")
        del self.info_aliases[word]
        with open(self.aliases_file, "w") as f:
            json.dump(self.info_aliases, f, indent=4)
        await ctx.send("✅ Alias removed.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(aliases=['aliases'], help='<infoname> [This will give you all the aliases to that info]')
    async def listaliases(self, ctx, info_name: str = ""):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        aliases = []
        for word, info in self.info_aliases.items():
            if info == info_name:
                aliases.append(word)
        if not aliases:
            return await ctx.send("⚠ No aliases found.")
        await ctx.send("Aliases for INFO entry {}: {}".format(info_name, ", ".join(aliases)))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def deleteinfo(self, ctx, info_name: str = ""):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        with open(self.json_file, "r") as f:
            info_db = json.load(f)
        try:
            del info_db[info_name]
            for word, info in self.info_aliases.items():
                if info == info_name:
                    del self.info_aliases[word]
            with open(self.json_file, "w") as f:
                json.dump(info_db, f, indent=4)
        except KeyError:
            return await ctx.send("⚠ No such entry exists.")
        with open(self.aliases_file, "w") as f:
            json.dump(self.info_aliases, f, indent=4)
        await ctx.send("✅ Entry deleted.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def editinfo(self, ctx, info_name: str = "", edit_type: str = "a"):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        if not(edit_type[0] == "q" or edit_type[0] == "a"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `information` (default).")
        with open(self.json_file, "r") as f:
            info_db = json.load(f)
        try:
            entry = info_db[info_name]
        except KeyError:
            return await ctx.send("⚠ No such entry exists.")
        random_num = random.randint(1, 9999)
        edit_type_readable = {
            "q": "question",
            "i": "information"
        }
        await ctx.send("Enter the new {} content:\n\nType `cancel-{:04d}` to cancel.".format(edit_type_readable[edit_type[0]], random_num))
        try:
            new_content = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
            if new_content.content == "cancel-{:04d}".format(random_num):
                return await ctx.send("❌ Canceled by user.")
        except asyncio.TimeoutError:
            return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")
        
        if edit_type[0] == "q":
            entry['question'] = new_content.content
        elif edit_type[0] == "a":
            entry['information'] = new_content.content
        
        info_db[info_name] = entry
        
        with open(self.json_file, "w") as f:
            json.dump(info_db, f, indent=4)
        
        await ctx.send("✅ Entry modified.")
        self.bot.loop.create_task(self.update_info(ctx))

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def inforaw(self, ctx, info_name: str = "", return_type: str = "both"):
        if not info_name:
            return await ctx.send("⚠ INFO entry name is required.")
        if not(return_type[0] == "q" or return_type[0] == "a" or return_type[0] == "b"):
            return await ctx.send("⚠ Unknown return type. Acceptable arguments are: `question`, `information`, `both` (default).")
        with open(self.json_file, "r") as f:
            info_db = json.load(f)
        try:
            entry = info_db[info_name]
        except KeyError:
            return await ctx.send("⚠ No such entry exists.")
        if return_type[0] == "q":
            msg = entry['question']
        elif return_type[0] == "a":
            msg = entry['information']
        else:
            msg = "\n\n".join([entry['question'], entry['information']])
        await ctx.send("```\n{}\n```".format(msg))

    @commands.command(aliases=['infoview'], help='<info_name> or <info_alias_name>')
    async def info(self, ctx, info_req: str):
        with open(self.json_file, "r") as f:
            info_db = json.load(f)

        if info_req in self.info_aliases:
            info_req = self.info_aliases[info_req]

        if info_req not in info_db:
            return await ctx.send("⚠ No such entry exists.")

        entry = info_db[info_req]
        embed = discord.Embed(color=discord.Color.red())
        embed.title = f"INFO: {info_req.upper()}"
        embed.add_field(name="Question:", value=entry['question'], inline=False)
        embed.add_field(name="Information:", value=f"{entry['information']}", inline=False)
        await ctx.send(embed=embed)

    @commands.command(hidden=True)
    @commands.has_any_role("Admin")
    async def refreshinfo(self, ctx):
        await ctx.send("Refreshing INFO...")
        self.bot.loop.create_task(self.update_info(ctx))

def setup(bot):
    bot.add_cog(Info(bot))

# import asyncio
# import discord
# from discord.ext import commands
# import os
# import json
# import random

# class InfoManager(commands.Cog):
#     def __init__(self, bot):
#         self.bot = bot
#         self.info_database = {}
#         self.aliases_database = {}
#         database_folder = 'Database'
#         self.info_json_file = os.path.join(database_folder, 'info.json')
#         self.aliases_json_file = os.path.join(database_folder, 'info_aliases.json')

#         if os.path.exists(self.info_json_file):
#             with open(self.info_json_file, 'r') as f:
#                 self.info_database = json.load(f)
        
#         if os.path.exists(self.aliases_json_file):
#             with open(self.aliases_json_file, 'r') as f:
#                 self.aliases_database = json.load(f)

#     def save_info(self):
#         with open(self.info_json_file, 'w') as f:
#             json.dump(self.info_database, f, indent=4)
        
#         with open(self.aliases_json_file, 'w') as f:
#             json.dump(self.aliases_database, f, indent=4)
            
#     async def update_info(self, ctx):
#         if not self.embeds_database:
#             await ctx.send("⚠ No embeds found in the database.")
#             return

#         for embed_type, embeds in self.embeds_database.items():
#             for channel_id, embed_data in embeds.items():
#                 channel = ctx.guild.get_channel(channel_id)

#                 if not channel:
#                     continue

#                 embed = discord.Embed.from_dict(embed_data)
#                 existing_message = None

#                 async for msg in channel.history(limit=100):
#                     if msg.author == self.bot.user and msg.embeds and msg.embeds[0].title == embed.title:
#                         existing_message = msg
#                         break

#                 if existing_message:
#                     await existing_message.edit(embed=embed)
#                 else:
#                     await channel.send(embed=embed)

#         self.save_info()
#         await ctx.send("✅ All embeds updated.")

# # You can call this function like this:
# # await self.update_embeds(ctx)


#     @commands.command(help='Add a new info to a channel with a given type.', hidden=True)
#     @commands.has_any_role("Admin")
#     async def addinfo(self, ctx, channel: discord.TextChannel, info_type: str):
#         try:
#             await ctx.send("Enter the name of the info (e.g., !howto svcommands):")
#             name_response = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=60.0)
#             name = name_response.content.lower()

#             await ctx.send("Enter the info description:")
#             description_response = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=120.0)
#             description = description_response.content

#             await ctx.send("Enter the info message content:")
#             message_response = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=120.0)
#             message = message_response.content

#             info = discord.Embed(
#                 title=name,
#                 description=description,
#                 color=discord.Color.random()
#             )

#             if info_type not in self.info_database:
#                 self.info_database[info_type] = {}
#             self.info_database[info_type][name] = {
#                 "channel_id": channel.id,
#                 "info": info.to_dict()
#             }

#             self.save_info()
#             await ctx.send(f"✅ Info '{name}' added to channel '{channel}' with type '{info_type}'.")
#         except asyncio.TimeoutError:
#             await ctx.send("🚫 Timed out while waiting for responses, cancelling.")
#         except Exception as e:
#             print(e)
#             await ctx.send("❌ An error occurred while adding the info.")
#             self.bot.loop.create_task(self.update_info(ctx))

#     @commands.command(hidden=True)
#     @commands.has_any_role("Admin")
#     async def refreshinfo(self, ctx, info_type: str, name: str):
#         try:
#             if info_type in self.info_database and name in self.info_database[info_type]:
#                 info_data = self.info_database[info_type][name]["info"]
#                 info = discord.Embed.from_dict(info_data)
#                 channel_id = self.info_database[info_type][name]["channel_id"]
#                 channel = ctx.guild.get_channel(channel_id)
#                 if channel:
#                     await channel.send(embed=info)
#                     await ctx.send(f"✅ Info '{name}' refreshed in channel '{channel}' with type '{info_type}'.")
#                 else:
#                     await ctx.send(f"❌ Channel not found for '{name}' with type '{info_type}'.")
#             else:
#                 await ctx.send(f"❌ info '{name}' not found for type '{info_type}'.")
#         except Exception as e:
#             print(e)
#             await ctx.send("❌ An error occurred while refreshing the info.")
#             self.bot.loop.create_task(self.update_info(ctx))

#     @commands.command(hidden=True)
#     @commands.has_any_role("Admin")
#     async def deleteinfo(self, ctx, info_type: str, name: str = ""):
#         if not info_type or not name:
#             return await ctx.send("⚠ info type and name are required.")
        
#         if info_type in self.info_database and name in self.info_database[info_type]:
#             del self.info_database[info_type][name]
#             self.save_info()
#             await ctx.send(f"✅ Info '{name}' deleted for type '{info_type}'.")
#         else:
#             await ctx.send(f"❌ Info '{name}' not found for type '{info_type}'.")

#     @commands.command(hidden=True)
#     @commands.has_any_role("Admin")
#     async def editinfo(self, ctx, info_type: str, name: str = ""):
#         if not info_type or not name:
#             return await ctx.send("⚠ Info type and name are required.")
        
#         if info_type in self.info_database and name in self.info_database[info_type]:
#             entry = self.info_database[info_type][name]["info"]
#             random_num = random.randint(1, 9999)
#             await ctx.send(f"Enter the new description content for '{name}':\n\nType `cancel-{random_num:04d}` to cancel.")
#             try:
#                 new_description_response = await self.bot.wait_for("message", check=(lambda m: m.channel == ctx.message.channel and m.author == ctx.author), timeout=30.0)
#                 new_description = new_description_response.content
#                 if new_description == "cancel-{:04d}".format(random_num):
#                     return await ctx.send("❌ Canceled by user.")
#             except asyncio.TimeoutError:
#                 return await ctx.send("🚫 Timed out while waiting for a response, cancelling.")
            
#             entry['description'] = new_description
#             self.info_database[info_type][name]["info"] = entry
#             self.save_info()
            
#             await ctx.send(f"✅ Description modified for '{name}' in type '{info_type}'.")
#         else:
#             await ctx.send(f"❌ Info '{name}' not found for type '{info_type}'.")
#             self.bot.loop.create_task(self.update_info(ctx))

#     @commands.command(aliases=['infoview'], help='<info_name> or <info_alias_name>')
#     async def viewinfo(self, ctx, info_type: str, name: str):
#         try:
#             if info_type in self.info_database and name in self.info_database[info_type]:
#                 info_data = self.info_database[info_type][name]["info"]
#                 info = discord.Embed.from_dict(info_data)
#                 await ctx.send(embed=info)
#             else:
#                 await ctx.send(f"❌ Info '{name}' not found for type '{info_type}'.")
#         except Exception as e:
#             print(e)
#             await ctx.send("❌ An error occurred while viewing the info.")
            
#     @commands.command(hidden=True, help='Add aliases to an info.')
#     @commands.has_any_role("Moderator", "Admin")
#     async def addinfoalias(self, ctx, info_type: str, name: str = "", *, words: str = ""):
#         if not info_type or not name:
#             return await ctx.send("⚠ Info type and name are required.")
#         if info_type in self.info_database and name in self.info_database[info_type]:
#             for word in words.strip().split():
#                 self.info_database[info_type][name].setdefault("aliases", []).append(word)
#             self.save_info()
#             await ctx.send("✅ Aliases added/updated.")
#         else:
#             await ctx.send(f"❌ Info '{name}' not found for type '{info_type}'.")
#             self.bot.loop.create_task(self.update_info(ctx))

#     @commands.command(aliases=['deleteinfoalias'], hidden=True, help='Remove an alias from an info.')
#     @commands.has_any_role("Admin")
#     async def removeinfoalias(self, ctx, info_type: str, name: str = "", word: str = ""):
#         if not info_type or not name:
#             return await ctx.send("⚠ Info type and name are required.")
#         if info_type in self.info_database and name in self.info_database[info_type]:
#             aliases = self.info_database[info_type][name].get("aliases", [])
#             if word in aliases:
#                 aliases.remove(word)
#                 self.save_info()
#                 await ctx.send("✅ Alias removed.")
#             else:
#                 await ctx.send("⚠ Alias does not exist for this info.")
#         else:
#             await ctx.send(f"❌ Info '{name}' not found for type '{info_type}'.")
#             self.bot.loop.create_task(self.update_info(ctx))

#     @commands.command(aliases=['infoaliases'], help='<info_type> <info_name> [This will give you all the aliases to that info]')
#     async def listinfoaliases(self, ctx, info_type: str, name: str = ""):
#         if not info_type or not name:
#             return await ctx.send("⚠ Info type and name are required.")
#         if info_type in self.info_database and name in self.info_database[info_type]:
#             aliases = self.info_database[info_type][name].get("aliases", [])
#             if not aliases:
#                 return await ctx.send("⚠ No aliases found.")
#             await ctx.send(f"Aliases for info '{name}' in type '{info_type}': {', '.join(aliases)}")
#         else:
#             await ctx.send(f"❌ Info '{name}' not found for type '{info_type}'.")

# def setup(bot):
#     bot.add_cog(InfoManager(bot))