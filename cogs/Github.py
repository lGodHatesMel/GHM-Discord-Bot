import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashCommand, SlashContext
from discord_slash.utils.manage_commands import create_option
from config import GUILDID
import requests

class GitHub(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @cog_ext.cog_slash(name="github", description="Get information about a GitHub repository",
        options=[
            create_option(name="owner", description="Owner of the repository", option_type=3, required=True),
            create_option(name="repo", description="Name of the repository", option_type=3, required=True)
        ], guild_ids=[GUILDID])
    async def github(self, ctx: SlashContext, owner: str, repo: str):
        response = requests.get(f'https://api.github.com/repos/{owner}/{repo}')
        data = response.json()

        if response.status_code == 200:
            embed = discord.Embed(
                title=data['name'],
                description=data['description'],
                color=discord.Color.blue()
            )
            embed.add_field(name="Stars", value=data['stargazers_count'])
            embed.add_field(name="Forks", value=data['forks'])
            embed.add_field(name="Open Issues", value=data['open_issues'])
            embed.set_thumbnail(url=data['owner']['avatar_url'])
            embed.add_field(name="Repo Link", value=data['html_url'])

            release_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/releases')
            release_data = release_response.json()
            if release_response.status_code == 200 and release_data:
                latest_release = release_data[0]
                embed.add_field(name="Latest Release", value=latest_release['name'])
                embed.add_field(name="Release Link", value=latest_release['html_url'])
                if 'prerelease' in latest_release and latest_release['prerelease']:
                    embed.add_field(name="Release Type", value="Development")
                else:
                    embed.add_field(name="Release Type", value="Stable")
            else:
                embed.add_field(name="Latest Release", value="No releases found.")

            branches_response = requests.get(f'https://api.github.com/repos/{owner}/{repo}/branches')
            branches_data = branches_response.json()
            if branches_response.status_code == 200 and branches_data:
                branch_names = [branch['name'] for branch in branches_data]
                embed.add_field(name="Branches", value=", ".join(branch_names))
            else:
                embed.add_field(name="Branches", value="No branches found.")

            await ctx.send(embed=embed)
        else:
            await ctx.send('Repository not found.')

def setup(bot):
    bot.add_cog(GitHub(bot))