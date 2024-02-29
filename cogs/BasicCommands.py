import discord
from discord.ext import commands
from datetime import datetime, timezone
import json
import utils.utils as utils
from utils.Paginator import Paginator
import logging
from googletrans import Translator
from sympy import sympify

EMOJI_OPTIONS = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.latency = self.bot.latency
        self.translator = Translator()

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

    @commands.command(description='Replies with Pong if bot is up')
    @commands.has_any_role("Moderator", "Admin")
    async def ping(self, ctx):
        await ctx.message.reply('Pong')

    @commands.command(help="Shows bot's latency", hidden=True)
    @commands.is_owner()
    async def botping(self, ctx):
        try:
            BotLatency = self.bot.latency * 1000

            embed = discord.Embed(
                title="Server Ping",
                description=f"Server ping is currently {BotLatency:.2f}ms",
                color=discord.Color.red(),
            )
            avatar_url = (
                ctx.author.avatar.url
                if isinstance(ctx.author.avatar, discord.Asset)
                else "https://www.gravatar.com/avatar/?d=retro&s=32"
            )
            embed.set_thumbnail(url=avatar_url)

            reply = await ctx.message.reply(embed=embed)
            if reply:
                print("Bot ping message sent successfully.")
            else:
                print("Failed to send bot ping message.")
        except Exception as e:
            logging.error(f"An error occurred while trying to get the bot's ping: {e}")

    @commands.command(help="Shows all custom emojis added to bot", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def showemojis(self, ctx):
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

    @commands.command(help="<name> <emoji>", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addemoji(self, ctx, name: str, emoji: str):
        utils.custom_emojis[name] = emoji
        with open('Data/CustomEmojis.json', 'w') as f:
            json.dump(utils.custom_emojis, f)
        await ctx.message.reply(f"Emoji {name} added.")

    @commands.command(help="<name>", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def removeemoji(self, ctx, name: str):
        if name in utils.custom_emojis:
            del utils.custom_emojis[name]
            with open('Data/CustomEmojis.json', 'w') as f:
                json.dump(utils.custom_emojis, f)
            await ctx.message.reply(f"Emoji {name} removed.")
        else:
            await ctx.message.reply(f"Emoji {name} not found.")

    # Set to staff for now
    @commands.command(help="Shows all PKM Facts", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def showallfacts(self, ctx):
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

    @commands.command(help="Adds a new PKM Fact", hidden=True)
    @commands.has_any_role("Helper", "Moderator", "Admin")
    async def addfact(self, ctx, *, fact):
        if len(fact) > 1024:
            await ctx.message.reply("Fact is too long. Please limit it to 1024 characters.")
            return

        with open('Data/PKMFacts.txt', 'a') as file:
            file.write(fact + '\n')
        await ctx.message.reply("Fact added successfully!")

    @commands.command(help="Deletes a PKM Fact", hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def deletefact(self, ctx, *, fact):
        with open('Data/PKMFacts.txt', 'r') as file:
            facts = file.readlines()

        fact += '\n'
        if fact not in facts:
            await ctx.send("Fact not found.")
            return

        facts.remove(fact)

        with open('Data/PKMFacts.txt', 'w') as file:
            file.writelines(facts)
        await ctx.message.reply("Fact deleted successfully!")

    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def togglechannel(self, ctx, channel: discord.TextChannel, role: discord.Role, permission_name: str):
        if permission_name not in ('send_messages', 'read_messages'):
            await ctx.message.reply("Invalid permission name. Use 'send_messages' or 'read_messages'.")
            return

        permissions = channel.overwrites_for(role)
        if getattr(permissions, permission_name):
            setattr(permissions, permission_name, False)
        else:
            setattr(permissions, permission_name, True)

        await channel.set_permissions(role, overwrite=permissions)

        if getattr(permissions, permission_name):
            await ctx.message.reply(f"Permission '{permission_name}' for role '{role.name}' in channel '{channel.name}' has been enabled.")
        else:
            await ctx.message.reply(f"Permission '{permission_name}' for role '{role.name}' in channel '{channel.name}' has been disabled.")

    @togglechannel.error
    async def togglechannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.message.reply("You don't have the required permissions to use this command.")

    @commands.command(help='<#Channel> <Message>', description='Sends a bot down message to a specific channel', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.message.reply(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.GetLocalTime().strftime('%m-%d-%y %I:%M %p')
        author = ctx.message.author
        command = ctx.command.name
        logging.info(f"{current_time} - {author.name} used the *{command}* command.")

    @commands.command(help='<#Channel> <Title> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def announcement(self, ctx, channel: discord.TextChannel, title, *, message):
        with open('config.json') as f:
            config = json.load(f)

        logo_url = config.get('logo_url')
        embed = discord.Embed(
            title=title,
            description=message,
            color=discord.Color.random()
        )
        embed.set_thumbnail(url=logo_url)
        embed.set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)

        await channel.send(embed=embed)
        await ctx.message.reply(f"Announcement sent to {channel.mention}.")

    @commands.command(help='"Poll Title" "option1" "option2" <add_more_if_needed> "Your Message Here"', description='Creates a poll with multiple options', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def poll(self, ctx, pollTitle, *options: str):
        optionsDescription = ""
        for i, option in enumerate(options[:-1]):
            optionsDescription += f"{EMOJI_OPTIONS[i]} {option}\n"

        embed = discord.Embed(
            title=pollTitle,
            description=optionsDescription,
            color=discord.Color.red()
        )

        pollMessage = await ctx.send(embed=embed)
        for i in range(len(options) - 1):
            await pollMessage.add_reaction(EMOJI_OPTIONS[i])

        message = options[-1]
        if message is not None:
            await ctx.send(message)

    @commands.command(help='<Target Language> <Text To Translate>')
    async def translate(self, ctx, TargetLanguage, *, TextToTranslate):
        try:
            DetectedLanguage = self.translator.detect(TextToTranslate)
            TranslatedText = self.translator.translate(TextToTranslate, dest=TargetLanguage)

            embed = discord.Embed(
                title='Translation Result',
                color=discord.Color.blue()
            )
            embed.add_field(name='Source Language', value=DetectedLanguage.lang, inline=True)
            embed.add_field(name='Target Language', value=TargetLanguage, inline=True)
            embed.add_field(name='Original Text', value=TextToTranslate, inline=False)
            embed.add_field(name='Translation', value=TranslatedText.text, inline=False)

            await ctx.message.reply(embed=embed)
        except Exception as e:
            await ctx.message.reply(f'An error occurred: {str(e)}')

    @commands.command(name="calc")
    async def calc(self, ctx, *, equation: str):
        try:
            result = sympify(equation)
            await ctx.reply(
                embed=discord.Embed(
                    description=f"Result: {result}", color=0x00FF00
                )
            )
        except Exception as e:
            await ctx.reply(
                embed=discord.Embed(description=f"Error: {e}", color=0xFF0000)
            )

def setup(bot):
    bot.add_cog(BasicCommands(bot))


# !translate fr Hello, how are you?
# `af`: Afrikaans    | `sq`: Albanian     | `am`: Amharic
# `ar`: Arabic       | `hy`: Armenian     | `az`: Azerbaijani
# `eu`: Basque       | `be`: Belarusian   | `bn`: Bengali
# `bs`: Bosnian      | `bg`: Bulgarian    | `ca`: Catalan
# `ceb`: Cebuano     | `ny`: Chichewa     | `zh-cn`: Chinese (Simplified)
# `zh-tw`: Chinese (Traditional) | `co`: Corsican | `hr`: Croatian
# `cs`: Czech        | `da`: Danish       | `nl`: Dutch
# `en`: English      | `eo`: Esperanto    | `et`: Estonian
# `tl`: Filipino     | `fi`: Finnish      | `fr`: French
# `fy`: Frisian      | `gl`: Galician     | `ka`: Georgian
# `de`: German       | `el`: Greek        | `gu`: Gujarati
# `ht`: Haitian Creole | `ha`: Hausa     | `haw`: Hawaiian
# `iw`: Hebrew       | `hi`: Hindi        | `hmn`: Hmong
# `hu`: Hungarian    | `is`: Icelandic    | `ig`: Igbo
# `id`: Indonesian   | `ga`: Irish        | `it`: Italian
# `ja`: Japanese     | `jw`: Javanese     | `kn`: Kannada
# `kk`: Kazakh       | `km`: Khmer        | `rw`: Kinyarwanda
# `ko`: Korean       | `ku`: Kurdish      | `ky`: Kyrgyz
# `lo`: Lao          | `la`: Latin        | `lv`: Latvian
# `lt`: Lithuanian   | `lb`: Luxembourgish | `mk`: Macedonian
# `mg`: Malagasy     | `ms`: Malay        | `ml`: Malayalam
# `mt`: Maltese      | `mi`: Maori        | `mr`: Marathi
# `mn`: Mongolian    | `my`: Myanmar      | `ne`: Nepali
# `no`: Norwegian    | `or`: Odia         | `ps`: Pashto
# `fa`: Persian      | `pl`: Polish       | `pt`: Portuguese
# `pa`: Punjabi      | `ro`: Romanian     | `ru`: Russian
# `sm`: Samoan       | `gd`: Scots Gaelic | `sr`: Serbian
# `st`: Sesotho      | `sn`: Shona        | `sd`: Sindhi
# `si`: Sinhala      | `sk`: Slovak       | `sl`: Slovenian
# `so`: Somali       | `es`: Spanish      | `su`: Sundanese
# `sw`: Swahili      | `sv`: Swedish      | `tg`: Tajik
# `ta`: Tamil        | `tt`: Tatar        | `te`: Telugu
# `th`: Thai         | `tr`: Turkish      | `tk`: Turkmen
# `uk`: Ukrainian    | `ur`: Urdu         | `ug`: Uyghur
# `uz`: Uzbek        | `vi`: Vietnamese   | `cy`: Welsh
# `xh`: Xhosa        | `yi`: Yiddish      | `yo`: Yoruba
# `zu`: Zulu