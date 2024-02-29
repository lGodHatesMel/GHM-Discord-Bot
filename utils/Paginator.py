import discord
from discord.ext import commands
import asyncio
from utils.utils import custom_emojis

class Paginator:
    def __init__(self, ctx, embeds):
        self.ctx = ctx
        self.embeds = embeds
        self.current_page = 0
        self.message = None
        self.guild_emojis = [str(emoji) for emoji in ctx.guild.emojis]

    def get_reactions(self):
        reactions = ['🏠', '⬅️', '➡️', '🗑️']
        if custom_emojis['last_page'] in self.guild_emojis:
            reactions.append(custom_emojis['last_page'])
        else:
            reactions.append('📄')
        return reactions

    async def start(self):
        self.message = await self.ctx.send(embed=self.embeds[self.current_page])
        if len(self.embeds) > 1:
            await asyncio.sleep(1)
            for reaction in self.get_reactions():
                await self.message.add_reaction(reaction)

        def check(reaction, user):
            return user == self.ctx.author and str(reaction.emoji) in self.get_reactions()

        timeout = 60.0
        while True:
            reaction_add_task = self.ctx.bot.loop.create_task(
                self.ctx.bot.wait_for('reaction_add', check=check)
            )
            reaction_remove_task = self.ctx.bot.loop.create_task(
                self.ctx.bot.wait_for('reaction_remove', check=check)
            )

            done, pending = await asyncio.wait(
                [reaction_add_task, reaction_remove_task],
                timeout=timeout,
                return_when=asyncio.FIRST_COMPLETED
            )

            for task in pending:
                task.cancel()

            if not done:
                break

            try:
                reaction, _ = done.pop().result()
            except asyncio.CancelledError:
                continue

            for task in done:
                task.exception()

            if str(reaction.emoji) == '⬅️' and self.current_page > 0:
                self.current_page -= 1
            elif str(reaction.emoji) == '➡️':
                if self.current_page < len(self.embeds) - 1:
                    self.current_page += 1
                else:
                    self.current_page = 0
            elif str(reaction.emoji) == '🏠':
                self.current_page = 0
            elif str(reaction.emoji) == custom_emojis.get('last_page', '📄'):
                self.current_page = len(self.embeds) - 1
            elif str(reaction.emoji) == '🗑️':
                await self.message.delete()
                return

            await self.message.edit(embed=self.embeds[self.current_page])