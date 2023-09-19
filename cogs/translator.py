import discord
from discord.ext import commands
from googletrans import Translator

class Translation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()

    @commands.command(name='translate')
    async def translate_text(self, ctx, target_language, *, text_to_translate):
        try:
            # Detect the source language (optional)
            detected_language = self.translator.detect(text_to_translate)
            
            # Translate the text to the target language
            translated_text = self.translator.translate(text_to_translate, dest=target_language)
            
            # Create and send an embed with the translation result
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

def setup(bot):
    bot.add_cog(Translation(bot))

# pip install googletrans==4.0.0-rc1
# !translate fr Hello, how are you?

# - `af`: Afrikaans
# - `sq`: Albanian
# - `am`: Amharic
# - `ar`: Arabic
# - `hy`: Armenian
# - `az`: Azerbaijani
# - `eu`: Basque
# - `be`: Belarusian
# - `bn`: Bengali
# - `bs`: Bosnian
# - `bg`: Bulgarian
# - `ca`: Catalan
# - `ceb`: Cebuano
# - `ny`: Chichewa (Chewa)
# - `zh-cn`: Chinese (Simplified)
# - `zh-tw`: Chinese (Traditional)
# - `co`: Corsican
# - `hr`: Croatian
# - `cs`: Czech
# - `da`: Danish
# - `nl`: Dutch
# - `en`: English
# - `eo`: Esperanto
# - `et`: Estonian
# - `tl`: Filipino
# - `fi`: Finnish
# - `fr`: French
# - `fy`: Frisian
# - `gl`: Galician
# - `ka`: Georgian
# - `de`: German
# - `el`: Greek
# - `gu`: Gujarati
# - `ht`: Haitian Creole
# - `ha`: Hausa
# - `haw`: Hawaiian
# - `iw`: Hebrew
# - `hi`: Hindi
# - `hmn`: Hmong
# - `hu`: Hungarian
# - `is`: Icelandic
# - `ig`: Igbo
# - `id`: Indonesian
# - `ga`: Irish
# - `it`: Italian
# - `ja`: Japanese
# - `jw`: Javanese
# - `kn`: Kannada
# - `kk`: Kazakh
# - `km`: Khmer
# - `rw`: Kinyarwanda
# - `ko`: Korean
# - `ku`: Kurdish (Kurmanji)
# - `ky`: Kyrgyz
# - `lo`: Lao
# - `la`: Latin
# - `lv`: Latvian
# - `lt`: Lithuanian
# - `lb`: Luxembourgish
# - `mk`: Macedonian
# - `mg`: Malagasy
# - `ms`: Malay
# - `ml`: Malayalam
# - `mt`: Maltese
# - `mi`: Maori
# - `mr`: Marathi
# - `mn`: Mongolian
# - `my`: Myanmar (Burmese)
# - `ne`: Nepali
# - `no`: Norwegian
# - `or`: Odia (Oriya)
# - `ps`: Pashto
# - `fa`: Persian
# - `pl`: Polish
# - `pt`: Portuguese
# - `pa`: Punjabi
# - `ro`: Romanian
# - `ru`: Russian
# - `sm`: Samoan
# - `gd`: Scots Gaelic
# - `sr`: Serbian
# - `st`: Sesotho
# - `sn`: Shona
# - `sd`: Sindhi
# - `si`: Sinhala
# - `sk`: Slovak
# - `sl`: Slovenian
# - `so`: Somali
# - `es`: Spanish
# - `su`: Sundanese
# - `sw`: Swahili
# - `sv`: Swedish
# - `tg`: Tajik
# - `ta`: Tamil
# - `tt`: Tatar
# - `te`: Telugu
# - `th`: Thai
# - `tr`: Turkish
# - `tk`: Turkmen
# - `uk`: Ukrainian
# - `ur`: Urdu
# - `ug`: Uyghur
# - `uz`: Uzbek
# - `vi`: Vietnamese
# - `cy`: Welsh
# - `xh`: Xhosa
# - `yi`: Yiddish
# - `yo`: Yoruba
# - `zu`: Zulu
   