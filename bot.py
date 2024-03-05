import discord
from discord.ext import commands
from config import prefix, owner_id
from utils.Paginator import Paginator

## Intents
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.dm_messages = True
intents.dm_reactions = True
intents.message_content = True
intents.typing = True

class EmbedHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__()
    def get_command_signature(self, command):
        if command.help:
            return '`!{} {}`'.format(command.qualified_name, command.help)
        else:
            return '`!{}`'.format(command.qualified_name)

    async def send_bot_help(self, mapping):
        ExcludeCommands = ['staffcommands', 'commands', 'help', 'ping', 'botping']
        embeds = []
        current_embed = discord.Embed(color=discord.Color.random())
        current_count = 0
        for cog, commands in mapping.items():
            if getattr(cog, "hidden", False):
                continue
            commands = [c for c in commands if not c.hidden and c.name not in ExcludeCommands]
            if commands:
                cog_name = getattr(cog, "qualified_name", "Other Commands")
                field_value = ""
                for command in commands:
                    signature = self.get_command_signature(command)
                    field_value += signature + "\n"
                    current_count += 1
                    if current_count == 9:
                        current_embed.add_field(name=f"{cog_name}", value=field_value, inline=True)
                        current_embed.title = f"**Server Commands - Page {len(embeds) + 1}**"
                        embeds.append(current_embed)
                        current_embed = discord.Embed(color=discord.Color.random())
                        current_count = 0
                        field_value = ""
                if field_value:
                    current_embed.add_field(name=f"{cog_name}", value=field_value, inline=True)
                current_embed.set_footer(text="Use the reactions to navigate between pages.")
        if len(current_embed.fields) > 0:
            current_embed.set_footer(text="Use the reactions to navigate between pages.")
            current_embed.title = f"**Server Commands - Page {len(embeds) + 1}**"
            embeds.append(current_embed)
        paginator = Paginator(self.context, embeds)
        await paginator.start()

## Bot Setup
bot = commands.Bot(
    command_prefix=prefix,
    case_insensitive=True,
    intents=intents,
    owner_ids=[owner_id],
    help_command=EmbedHelpCommand(),
    description="Custom bot for our Discord server."
)

@bot.command(name='commands')
async def _commands(ctx, *args):
    try:
        await ctx.send_help(*args)
    except Exception as e:
        print(f"An error occurred while sending help: {e}")