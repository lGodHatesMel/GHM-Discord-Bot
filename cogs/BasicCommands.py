import discord
from discord import Embed
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from typing import Union
import random
import json
import asyncio
import utils.utils as utils
from utils.Paginator import Paginator
import logging
from googletrans import Translator
from sympy import sympify
from config import LOGO_URL, GUILDID, ROLEIDS

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latency = self.bot.latency
        self.translator = Translator()
        with open('Data/BadWordList.txt', 'r') as file:
            self.BadWords = file.read().splitlines()

    @commands.Cog.listener()
    async def on_message(self, message):
        if not message.author.bot:
            try:
                await self.GreetingMessage(message)
            except Exception as e:
                logging.error(f"An error occurred in on_message (greeting): {e}")

    async def GreetingMessage(self, message):
        words = message.content.lower().split()
        if "hello" in words or "hey" in words:
            await message.reply(f"Hello, {message.author.mention}!")

    # @cog_ext.cog_slash(name="hello", description="Says hello!", options=[
    #     create_option(
    #         name="name",
    #         description="Enter your name",
    #         option_type=3,
    #         required=True
    #     )], guild_ids=[GUILDID])
    # async def _hello(self, ctx: Union[commands.Context, SlashContext], name: str = 'World'):
    #     admin_role = discord.utils.get(ctx.guild.roles, id=ROLEIDS["Admin"])
    #     moderator_role = discord.utils.get(ctx.guild.roles, id=ROLEIDS["Moderator"])
    #     if admin_role not in ctx.author.roles and moderator_role not in ctx.author.roles:
    #         await ctx.send("You are not authorized to use this command.")
    #         return
    #     await ctx.send(f'Hello, {name}!')

    @cog_ext.cog_subcommand(base="Staff", name="addbadword", description="(STAFF) Add word to the bad word list",
        options=[create_option(name="word", description="Enter the word to add to the bad word list", option_type=3, required=True)], guild_ids=[GUILDID])
    @commands.command(help="Add word to the bad word list", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def addbadword(self, ctx: Union[commands.Context, SlashContext], *, word):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        self.BadWords.append(word)
        with open('Data/BadWordList.txt', 'a') as file:
            file.write(f'{word}\n')
        await ctx.send(f'Word "{word}" has been added to the bad words list.')

    @cog_ext.cog_subcommand(base="Staff", name="badwordlist", description="(STAFF) Show current bad word list", guild_ids=[GUILDID], options=[])
    async def badwordlist(self, ctx: Union[commands.Context, SlashContext]):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Admin"], ROLEIDS["Moderator"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send("You are not authorized to use this command.")
                return

        words_per_page = 50
        bad_words = [self.BadWords[i:i + words_per_page] for i in range(0, len(self.BadWords), words_per_page)]
        embeds = [discord.Embed(title="Bad Words List", description=", ".join(words), color=0x3498db) for words in bad_words]
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    @cog_ext.cog_subcommand(base="Staff", name="purge", description="(STAFF) Delete a number of messages",
    options=[create_option(name="amount", description="Number of messages to delete", option_type=4, required=True)], guild_ids=[GUILDID])
    @commands.command(name="purge", aliases=["clearmessages"], help="1 to 100", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def purge(self, ctx: Union[commands.Context, SlashContext], amount: int):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send("You are not authorized to use this command.")
                return

        if amount <= 0:
            await ctx.send("Please specify a valid number of messages to clear.")
            return
        if amount > 100:
            await ctx.send("You can only clear up to 100 messages at a time.")
            return

        try:
            if ctx.message is not None:
                await ctx.message.delete()
            deleted_messages = await ctx.channel.purge(limit=amount, bulk=True)
            await ctx.send(f"Cleared {len(deleted_messages)} messages.", delete_after=5)
        except commands.MissingPermissions:
            await ctx.send("Bot doesn't have the necessary permissions to clear messages.")

    @cog_ext.cog_slash(name="showallfacts", description="Shows all PKM Facts", guild_ids=[GUILDID], options=[])
    async def showallfacts(self, ctx: Union[commands.Context, SlashContext]):
        with open('Data/PKMFacts.txt', 'r') as file:
            PKMFacts = file.read().splitlines()
        embeds = []
        author_name = "Pokemon Facts"
        icon_url = "https://raw.githubusercontent.com/lGodHatesMel/RandomResources/main/Images/pkm_facts.png"
        base_chars = len(author_name) + len(icon_url)
        embed = discord.Embed(color=discord.Color.random())
        embed.set_author(name=author_name, icon_url=icon_url)
        fact_count = 0
        for fact in PKMFacts:
            fact_chars = len(fact) + len("\u200b") + len("inline=False")
            if fact_chars > 1024 or fact_count == 25 or base_chars + fact_chars > 6000:
                embeds.append(embed)
                embed = discord.Embed(color=discord.Color.random())
                embed.set_author(name=author_name, icon_url=icon_url)
                base_chars = len(author_name) + len(icon_url)
                fact_count = 0
            embed.add_field(name="\u200b", value=fact, inline=False)
            base_chars += fact_chars
            fact_count += 1
        if base_chars > 0:
            embeds.append(embed)

        for i, embed in enumerate(embeds):
            footer_text = f"Page {i+1} of {len(embeds)} - Use the reactions to navigate between pages."
            embed.set_footer(text=footer_text)
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    @cog_ext.cog_subcommand(base="Staff", name="addfact", description="(STAFF) Adds a new PKM Fact",
        options=[create_option(name="fact", description="The fact to add", option_type=3, required=True)], guild_ids=[GUILDID])
    @commands.command(name="addfact", help="Adds a new PKM Fact", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addfact(self, ctx: Union[commands.Context, SlashContext], fact: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Helper"], ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        if len(fact) > 1024:
            await ctx.send("Fact is too long. Please limit it to 1024 characters.")
            return

        with open('Data/PKMFacts.txt', 'a') as file:
            file.write(fact + '\n')
        await ctx.send("Fact added successfully!")

    @cog_ext.cog_subcommand(base="Staff", name="deletefact", description="(STAFF) Deletes a PKM Fact",
    options=[create_option(name="fact", description="The fact to delete", option_type=3, required=True)], guild_ids=[GUILDID])
    @commands.command(name="deletefact", help="Deletes a PKM Fact", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletefact(self, ctx: Union[commands.Context, SlashContext], fact: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        with open('Data/PKMFacts.txt', 'r') as file:
            facts = file.readlines()
        fact += '\n'
        if fact not in facts:
            await ctx.send("Fact not found.")
            return

        facts.remove(fact)
        with open('Data/PKMFacts.txt', 'w') as file:
            file.writelines(facts)
        await ctx.send("Fact deleted successfully!")

    @cog_ext.cog_subcommand(base="Staff", name="botdown", description="(STAFF) Sends a bot down message to a specific channel",
        options=[
            create_option(name="channel", description="The channel", option_type=7, required=True),
            create_option(name="message", description="The message", option_type=3, required=True)
        ], guild_ids=[GUILDID])
    @commands.command(name="botdown", help='<#Channel> <Message>', description='Sends a bot down message to a specific channel', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx: Union[commands.Context, SlashContext], channel: discord.TextChannel, message: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        author = ctx.author
        command = ctx.command.name
        logging.info(f"{current_time} - {author.name} used the *{command}* command.")

    @cog_ext.cog_subcommand(base="Staff", name="announcement", description="(STAFF) Send an announcement to a specific channel",
    options=[
        create_option(name="channel", description="The channel", option_type=7, required=True),
        create_option(name="title", description="The title of the announcement", option_type=3, required=True),
        create_option(name="message", description="The announcement message", option_type=3, required=True)
    ], guild_ids=[GUILDID])
    @commands.command(name="announcement", help='<#Channel> <Title> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def announcement(self, ctx: Union[commands.Context, SlashContext], channel: discord.TextChannel, title: str, message: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

            embed = discord.Embed(
                title=title,
                description=message,
                color=discord.Color.random()
            )
            embed.set_thumbnail(url=LOGO_URL)
            embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

            await channel.send(embed=embed)
            await ctx.send(f"Announcement sent to {channel.mention}.")
        else:
            await ctx.send('You do not have permission to use this command.')

    @cog_ext.cog_slash(name="showemojis", description="Shows all custom emojis added to bot", guild_ids=[GUILDID], options=[])
    async def showemojis(self, ctx: Union[commands.Context, SlashContext]):
        embeds = []
        embed = discord.Embed(title="Custom Emojis", color=discord.Color.random())
        for i, (name, emoji) in enumerate(utils.custom_emojis.items(), start=1):
            if i % 25 == 0:
                embeds.append(embed)
                embed = discord.Embed(title="Custom Emojis", color=discord.Color.random())
            embed.add_field(name=name, value=emoji, inline=True)
        embeds.append(embed)
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    @cog_ext.cog_subcommand(base="Staff", name="addemoji", description="(STAFF) Add a custom emoji",
    options=[
        create_option(name="name", description="Name of the emoji", option_type=3, required=True),
        create_option(name="emoji", description="The emoji", option_type=3, required=True)
    ], guild_ids=[GUILDID])
    @commands.command(name="addemoji", help="<name> <emoji>", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addemoji(self, ctx: Union[commands.Context, SlashContext], name: str, emoji: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Helper"], ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

            utils.custom_emojis[name] = emoji
            with open('Data/CustomEmojis.json', 'w') as f:
                json.dump(utils.custom_emojis, f, indent=4)
            await ctx.send(f"Emoji {name} added.")
        else:
            await ctx.send('You do not have permission to use this command.')

    @cog_ext.cog_subcommand(base="Staff", name="removeemoji", description="(STAFF) Remove a custom emoji",
        options=[create_option(name="name", description="Name of the emoji", option_type=3, required=True)], guild_ids=[GUILDID])
    @commands.command(name="removeemoji", help="<name>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removeemoji(self, ctx: Union[commands.Context, SlashContext], name: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

            if name in utils.custom_emojis:
                del utils.custom_emojis[name]
                with open('Data/CustomEmojis.json', 'w') as f:
                    json.dump(utils.custom_emojis, f)
                await ctx.send(f"Emoji {name} removed.")
            else:
                await ctx.send(f"Emoji {name} not found.")
        else:
            await ctx.send('You do not have permission to use this command.')

    @cog_ext.cog_slash(name="ping", description="Replies with Pong if bot is up", guild_ids=[GUILDID], options=[])
    async def ping(self, ctx: Union[commands.Context, SlashContext]):
        await ctx.send('Pong!')

    @cog_ext.cog_subcommand(base="Staff", name="togglechannel", description="(STAFF) Toggle channel permissions",
    options=[
        create_option(name="channel", description="The channel", option_type=7, required=True),
        create_option(name="role", description="The role", option_type=8, required=True),
        create_option(name="permission_name", description="The permission name", option_type=3, required=True)
    ], guild_ids=[GUILDID])
    @commands.command(name="togglechannel", help="<channel> <role> <premission>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def togglechannel(self, ctx: Union[commands.Context, SlashContext], channel: discord.TextChannel, role: discord.Role, permission_name: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                if permission_name not in ('send_messages', 'read_messages'):
                    await ctx.send("Invalid permission name. Use 'send_messages' or 'read_messages'.")
                    return

            permissions = channel.overwrites_for(role)
            if getattr(permissions, permission_name):
                setattr(permissions, permission_name, False)
            else:
                setattr(permissions, permission_name, True)

            await channel.set_permissions(role, overwrite=permissions)

            if getattr(permissions, permission_name):
                await ctx.send(f"Permission '{permission_name}' for role '{role.name}' in channel '{channel.name}' has been enabled.")
            else:
                await ctx.send(f"Permission '{permission_name}' for role '{role.name}' in channel '{channel.name}' has been disabled.")
        else:
            await ctx.send('You do not have permission to use this command.')

    @cog_ext.cog_subcommand(base="Staff", name="createpoll", description="(STAFF) Creates a poll with multiple options",
        options=[
            create_option(name="channel", description="The channel", option_type=7, required=True),
            create_option(name="poll_title", description="The poll title", option_type=3, required=True),
            create_option(name="options", description="The poll options", option_type=3, required=True),
            create_option(name="duration", description="The poll duration", option_type=4, required=True),
            create_option(name="duration_unit", description="The duration unit", option_type=3, required=True)
        ], guild_ids=[GUILDID])
    @commands.command(name="createpoll", help='<#channel> "Poll Title" "option1" "option2" "Your Message Here" <duration> <duration_unit>', description="Creates a poll with multiple options", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def createpoll(self, ctx: Union[commands.Context, SlashContext], channel: discord.TextChannel, poll_title: str, options: str, duration: int, duration_unit: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

            options = options.split(',')
            if duration_unit.lower() == "days":
                duration = duration * 24 * 60 * 60
            elif duration_unit.lower() == "hours":
                duration = duration * 60 * 60
            else:
                await ctx.send("Invalid duration unit! Please specify either 'days' or 'hours'.")
                return

            optionsDescription = ""
            for i, option in enumerate(options[:-1]):
                optionsDescription += f"{utils.EmojiNumbers[i]} {option}\n"

            embed = discord.Embed(
                title=poll_title,
                description=optionsDescription,
                color=discord.Color.red()
            )
            pollMessage = await channel.send(embed=embed)
            for i in range(len(options) - 1):
                await pollMessage.add_reaction(utils.EmojiNumbers[i])

            message = options[-1]
            if message is not None:
                await ctx.send(message)

            await asyncio.sleep(duration)

            pollMessage = await pollMessage.channel.fetch_message(pollMessage.id)
            reactions = pollMessage.reactions
            winner = max(reactions, key=lambda r: r.count)
            embed = discord.Embed(
                title="Poll ended",
                description=f"The option {winner.emoji} won the poll.",
                color=discord.Color.green()
            )
            await channel.send(embed=embed)
        else:
            await ctx.send('You do not have permission to use this command.')

    @cog_ext.cog_slash(name="translate", description="Translate text to a target language",
        options=[
            create_option(name="target_language", description="The target language", option_type=3, required=True),
            create_option(name="text_to_translate", description="The text to translate", option_type=3, required=True)
        ], guild_ids=[GUILDID])
    @commands.command(name="translate", help='<Target Language> <Text To Translate>')
    async def translate(self, ctx: Union[commands.Context, SlashContext], target_language: str, text_to_translate: str):
        try:
            detected_language = self.translator.detect(text_to_translate)
            translated_text = self.translator.translate(text_to_translate, dest=target_language)

            embed = discord.Embed(
                title='Translation Result',
                color=discord.Color.blue()
            )
            embed.add_field(name='Source Language', value=detected_language.lang, inline=True)
            embed.add_field(name='Target Language', value=target_language, inline=True)
            embed.add_field(name='Original Text', value=text_to_translate, inline=False)
            embed.add_field(name='Translation', value=translated_text.text, inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

    @cog_ext.cog_slash(name="calc", description="Calculate an equation",
            options=[create_option(name="equation", description="The equation to calculate", option_type=3, required=True)], guild_ids=[GUILDID])
    @commands.command(name="calc")
    async def calc(self, ctx: Union[commands.Context, SlashContext], equation: str):
        image_urls = [
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-73-648aa668e5875__700.jpg",
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-62-6489cdaf6f80a__700.jpg",
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-66-6489d4dcda57d__700.jpg",
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-69-648aa1a040326__700.jpg",
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-64895ff9b1075__700.jpg",
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-65-6489d08507365__700.jpg",
            "https://www.boredpanda.com/blog/wp-content/uploads/2023/06/funny-witty-math-memes-6489605f61515__700.jpg"
        ]

        try:
            result = sympify(equation)
            embed = Embed(title="Calculation Result", description=f"Equation: `{equation}`\nResult: `{result}`", color=0x00FF00)
            embed.set_thumbnail(url=random.choice(image_urls))
            await ctx.send(embed=embed)
        except Exception as e:
            embed = Embed(title="Calculation Error", description=f"Error: `{e}`", color=0xFF0000)
            embed.set_thumbnail(url=random.choice(image_urls))
            await ctx.send(embed=embed)

    @cog_ext.cog_slash(name="languagescodes", description="Displays available languages for translation.", guild_ids=[GUILDID], options=[])
    async def languagescodes(self, ctx: Union[commands.Context, SlashContext]):
        languages = [
            "`af`: Afrikaans", "`sq`: Albanian", "`am`: Amharic",
            "`ar`: Arabic", "`hy`: Armenian", "`az`: Azerbaijani",
            "`eu`: Basque", "`be`: Belarusian", "`bn`: Bengali",
            "`bs`: Bosnian", "`bg`: Bulgarian", "`ca`: Catalan",
            "`ceb`: Cebuano", "`ny`: Chichewa", "`zh-cn`: Chinese (Simplified)",
            "`zh-tw`: Chinese (Traditional)", "`co`: Corsican", "`hr`: Croatian",
            "`cs`: Czech", "`da`: Danish", "`nl`: Dutch",
            "`en`: English", "`eo`: Esperanto", "`et`: Estonian",
            "`tl`: Filipino", "`fi`: Finnish", "`fr`: French",
            "`fy`: Frisian", "`gl`: Galician", "`ka`: Georgian",
            "`de`: German", "`el`: Greek", "`gu`: Gujarati",
            "`ht`: Haitian Creole", "`ha`: Hausa", "`haw`: Hawaiian",
            "`iw`: Hebrew", "`hi`: Hindi", "`hmn`: Hmong",
            "`hu`: Hungarian", "`is`: Icelandic", "`ig`: Igbo",
            "`id`: Indonesian", "`ga`: Irish", "`it`: Italian",
            "`ja`: Japanese", "`jw`: Javanese", "`kn`: Kannada",
            "`kk`: Kazakh", "`km`: Khmer", "`rw`: Kinyarwanda",
            "`ko`: Korean", "`ku`: Kurdish", "`ky`: Kyrgyz",
            "`lo`: Lao", "`la`: Latin", "`lv`: Latvian",
            "`lt`: Lithuanian", "`lb`: Luxembourgish", "`mk`: Macedonian",
            "`mg`: Malagasy", "`ms`: Malay", "`ml`: Malayalam",
            "`mt`: Maltese", "`mi`: Maori", "`mr`: Marathi",
            "`mn`: Mongolian", "`my`: Myanmar", "`ne`: Nepali",
            "`no`: Norwegian", "`or`: Odia", "`ps`: Pashto",
            "`fa`: Persian", "`pl`: Polish", "`pt`: Portuguese",
            "`pa`: Punjabi", "`ro`: Romanian", "`ru`: Russian",
            "`sm`: Samoan", "`gd`: Scots Gaelic", "`sr`: Serbian",
            "`st`: Sesotho", "`sn`: Shona", "`sd`: Sindhi",
            "`si`: Sinhala", "`sk`: Slovak", "`sl`: Slovenian",
            "`so`: Somali", "`es`: Spanish", "`su`: Sundanese",
            "`sw`: Swahili", "`sv`: Swedish", "`tg`: Tajik",
            "`ta`: Tamil", "`tt`: Tatar", "`te`: Telugu",
            "`th`: Thai", "`tr`: Turkish", "`tk`: Turkmen",
            "`uk`: Ukrainian", "`ur`: Urdu", "`ug`: Uyghur",
            "`uz`: Uzbek", "`vi`: Vietnamese", "`cy`: Welsh",
            "`xh`: Xhosa", "`yi`: Yiddish", "`yo`: Yoruba",
            "`zu`: Zulu"
        ]

        grouped_languages = ["\t".join([f"{languages[i]:<20}", languages[i+1] if i+1 < len(languages) else ""]) for i in range(0, len(languages), 2)]
        pages = [discord.Embed(title="Supported Languages", description="\n".join(grouped_languages[i:i+15]), color=0x3498db) for i in range(0, len(grouped_languages), 15)]
        for page in pages:
            page.set_footer(text="Use the language code for translation commands.")
        paginator = Paginator(ctx, pages)
        await paginator.start()

def setup(bot):
    bot.add_cog(BasicCommands(bot))