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

    def get_reactions(self):
        return ['🏠', '⬅️', '➡️', custom_emojis['last_page'], '🗑️'] # '📄'

    async def start(self):
        self.message = await self.ctx.send(embed=self.embeds[self.current_page])
        if len(self.embeds) > 1:
            await asyncio.sleep(1)
            for reaction in self.get_reactions():
                await self.message.add_reaction(reaction)

        def check(reaction, user):
            return user == self.ctx.author and str(reaction.emoji) in self.get_reactions()

        while True:
            try:
                done, pending = await asyncio.wait([
                    self.ctx.bot.wait_for('reaction_add', timeout=60.0, check=check),
                    self.ctx.bot.wait_for('reaction_remove', timeout=60.0, check=check)
                ], return_when=asyncio.FIRST_COMPLETED)
            except asyncio.TimeoutError:
                print('The task took too long to complete.')
                continue

            try:
                reaction, user = done.pop().result()
            except asyncio.TimeoutError:
                return

            for future in done:
                future.exception()

            for future in pending:
                future.cancel()

            if str(reaction.emoji) == '⬅️' and self.current_page > 0:
                self.current_page -= 1
            elif str(reaction.emoji) == '➡️':
                if self.current_page < len(self.embeds) - 1:
                    self.current_page += 1
                else:
                    self.current_page = 0
            elif str(reaction.emoji) == '🏠':
                self.current_page = 0
            elif str(reaction.emoji) == custom_emojis['last_page']:
                self.current_page = len(self.embeds) - 1
            elif str(reaction.emoji) == '🗑️':
                await self.message.delete()
                return

            await self.message.edit(embed=self.embeds[self.current_page])