from discord.ext import commands
import discord

class Others(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='poll', help='Creates a poll. Usage: !poll option1 option2 option3 option4 "Poll Title"', hidden=True)
    @commands.has_any_role("Moderator", "Admin")
    async def poll(self, ctx, option1, option2, option3, option4, *, pollTitle):
        emojiOptions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

        optionsDescription = f"{emojiOptions[0]} {option1}\n" \
                            f"{emojiOptions[1]} {option2}\n" \
                            f"{emojiOptions[2]} {option3}\n" \
                            f"{emojiOptions[3]} {option4}"

        embed = discord.Embed(
            title=pollTitle,
            description=optionsDescription,
            color=discord.Color.red()
        )

        pollMessage = await ctx.send(embed=embed)

        for emoji in emojiOptions:
            await pollMessage.add_reaction(emoji)

def setup(bot):
    bot.add_cog(Others(bot))