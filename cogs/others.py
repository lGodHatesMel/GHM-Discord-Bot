from discord.ext import commands
import discord

class Others(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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

def setup(bot):
    bot.add_cog(Others(bot))