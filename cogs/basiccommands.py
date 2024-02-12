import discord
from discord.ext import commands
from datetime import datetime, timezone
import utils
import logging
from googletrans import Translator

class BasicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
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

    @commands.command(help='Replies with Pong if bot is up', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def ping(self, ctx):
        await ctx.send('Pong')


    # @commands.command(help="Shows bot's latency", hidden=True)
    # @commands.has_any_role("Moderator", "Admin")
    # async def botping(self, ctx):
    #     try:
    #         BotLatency = self.bot.latency * 1000

    #         embed = discord.Embed(
    #             title="Server Ping",
    #             description=f"Server ping is currently {BotLatency:.2f}ms",
    #             color=discord.Color.red()
    #         )
    #         avatar_url = str(ctx.author.avatar.url) if ctx.author.avatar else 'https://www.gravatar.com/avatar/?d=retro&s=32'
    #         embed.set_thumbnail(url=avatar_url)

    #         reply = await ctx.reply(embed=embed)

    #         if reply:
    #             print("Bot ping message sent successfully.")
    #         else:
    #             print("Failed to send bot ping message.")

    #     except Exception as e:
    #         print(f"Error in botping command: {e}")


    @commands.command(hidden=True)
    @commands.has_permissions(administrator=True)
    async def togglechannel(self, ctx, channel: discord.TextChannel, role: discord.Role, permission_name: str):
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

    @togglechannel.error
    async def togglechannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You don't have the required permissions to use this command.")


    @commands.command(aliases=['bd'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def botdown(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Bot Down:**\n{message}")
        await ctx.send(f"Bot Down message sent to {channel.mention}.")

        current_time = utils.GetLocalTime().strftime('%m-%d-%y %H:%M')
        author = ctx.message.author
        command = ctx.command.name
        print(f"{current_time} - {author.name} used the *{command}* command.")


    @commands.command(aliases=['announce', 'ann'], help='<#Channel> <Message>', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def announcement(self, ctx, channel: discord.TextChannel, *, message):

        await channel.send(f"**Announcement:**\n{message}")
        await ctx.send(f"Announcement sent to {channel.mention}.")


    @commands.command(help='Creates a poll. Usage: !poll "Poll Title" "option1" "option2" <add_more_if_needed> "Your Message Here"', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def poll(self, ctx, pollTitle, *options: str):
        emojiOptions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣']

        optionsDescription = ""
        for i, option in enumerate(options[:-1]):
            optionsDescription += f"{emojiOptions[i]} {option}\n"

        embed = discord.Embed(
            title=pollTitle,
            description=optionsDescription,
            color=discord.Color.red()
        )

        message = options[-1]
        if message is not None:
            await ctx.send(message)

        pollMessage = await ctx.send(embed=embed)

        for i in range(len(options) - 1):
            await pollMessage.add_reaction(emojiOptions[i])


    @commands.command(help='translate <TargetLanguage> <TextToTranslate>')
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

            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f'An error occurred: {str(e)}')

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
