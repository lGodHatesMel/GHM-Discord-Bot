import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, ComponentContext
from discord_slash.utils.manage_commands import create_option, create_choice
from discord_slash.model import ButtonStyle
from discord_slash.utils.manage_components import create_button, create_actionrow, create_select, create_select_option, wait_for_component
from discord import Embed, PermissionOverwrite, utils
from discord_slash.context import ComponentContext
from config import GUILDID, CHANNELIDS, CATEGORYIDS, ROLEIDS
import utils.utils as utils
from utils.botdb import TicketDatabase
from utils.Paginator import Paginator
import sqlite3


class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect('Database/tickets.db')
        self.cursor = self.conn.cursor()
        self.cursor = TicketDatabase(self.cursor)

    @commands.Cog.listener()
    async def on_ready(self):
        self.cursor = TicketDatabase(self.cursor)

        guild = self.bot.get_guild(GUILDID)
        channel = guild.get_channel(CHANNELIDS['FormsChannel'])
        embed_title = "Create a Ticket"

        async for message in channel.history(limit=100):
            if message.author == self.bot.user and message.embeds and message.embeds[0].title == embed_title:
                await message.delete()
                break

        embed = Embed(title=embed_title, description="Please select the type of ticket you want to create.")
        select = create_select(
            options=[
                create_select_option("General Support", value="General Support", emoji="👍"),
                create_select_option("Bug Support", value="Bug Support", emoji="🐛"),
                create_select_option("Staff Application", value="Staff Application", emoji="📝"),
            ],
            placeholder="Select your ticket type",
            custom_id="ticket_select"
        )
        action_row = create_actionrow(select)
        await channel.send(embed=embed, components=[action_row])

        self.cursor.execute("SELECT message_id, channel_id, userid, ticket_type, questions, answers, closed_by, deleted_by FROM tickets")
        tickets = self.cursor.fetchall()

        for ticket in tickets:
            guild = self.bot.get_guild(GUILDID)
            if guild is None:
                print(f"Bot is not connected to the guild with ID {GUILDID}")
                continue
            ticket_channel = guild.get_channel(int(ticket[1]))
            if ticket_channel is None:
                print(f"Could not find channel with ID {ticket[1]}")
                continue

            message = await ticket_channel.fetch_message(ticket[0])

            close_button = create_button(style=ButtonStyle.red, label="Close Ticket", custom_id="close_ticket")
            delete_button = create_button(style=ButtonStyle.danger, label="Delete Ticket", custom_id="delete_ticket")
            action_row = create_actionrow(close_button, delete_button)

            user = self.bot.get_user(int(ticket[2]))
            if user is None:
                print(f"Could not find user with ID {ticket[2]}")
                continue

            ticket_type = ticket[3]
            questions = eval(ticket[4])
            form_responses = eval(ticket[5])

            embed = Embed(title=f"Ticket from {user.name}", description=f"Ticket type: {ticket_type}")
            embed.set_author(name=user.name, icon_url=user.avatar_url)
            for question, response in zip(questions, form_responses):
                embed.add_field(name=question, value=response, inline=False)
            embed.set_footer(text="Staff: When finished with ticket, click the Close button first. When ready to delete the channel, click the Delete button.")

            await message.edit(embed=embed, components=[action_row])

    @cog_ext.cog_component()
    async def ticket_select(self, ctx: ComponentContext):
        try:
            category = self.bot.get_channel(CATEGORYIDS['FormsReports'])
            if category is None:
                print("Channel not found")
            else:
                print(f"Found channel: {category.name}")

            # await ctx.send(content="Processing your request...", hidden=True)
            overwrites = {
                ctx.guild.default_role: PermissionOverwrite(read_messages=False),
                ctx.author: PermissionOverwrite(read_messages=True, send_messages=True),
            }
            for role_name in ['Moderators', 'Helpers', 'Admin']:
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                if role is None:
                    print(f"Role {role_name} not found")
                else:
                    print(f"Found role: {role.name}")
                    overwrites[role] = PermissionOverwrite(read_messages=True, send_messages=True)

            form_questions = {
                "General Help": [
                    "Whats your name?",
                    "What your Discord User UID? Should look somehitng like `12345678909410`",
                    "Explain in details what you need help with? Please be as thorough as possible",
                ],
                "Report User": [
                    "Whats the Users Discord name?",
                    "If you know how to get their UID please provide it.",
                    "What was the issue?",
                ],
                "Staff Application": [
                    "Whats your name?",
                    "What your Discord User UID? Should look somehitng like `12345678909410`",
                    "Any prior history of Moderation?",
                    "Are you familiar with Pokemon, PKHeX or other Pokemon tools?",
                    "How active are you on discord?"
                ],
            }

            selected_option = ctx.selected_options[0]
            questions = form_questions.get(selected_option, [])
            timestamp = utils.GetLocalTime().strftime('%m-%d %I:%M')
            dm_channel = ctx.author.dm_channel
            if dm_channel is None:
                dm_channel = await ctx.author.create_dm()

            await ctx.send(content=f"Check your DMs from @{self.bot.user.name} to fill out the form.", hidden=True)

            form_responses = []
            for question in questions:
                await dm_channel.send(content=question)
                response = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author and m.channel == dm_channel)
                form_responses.append(response.content)

            if len(form_responses) == len(questions):
                ticket_channel = await ctx.guild.create_text_channel(f'{selected_option}-{ctx.author.name}-{timestamp}', category=category, overwrites=overwrites)
                await dm_channel.send(f"Thank you, we have processed your ticket and it is now sent to {ticket_channel.mention}!")

                close_button = create_button(style=ButtonStyle.red, label="Close Ticket", custom_id="close_ticket")
                delete_button = create_button(style=ButtonStyle.danger, label="Delete Ticket", custom_id="delete_ticket")
                action_row = create_actionrow(close_button, delete_button)

                embed = Embed(title=f"Ticket from {ctx.author.name}", description=f"Ticket type: {ctx.selected_options[0]}")
                embed.set_author(name=ctx.author.name, icon_url=ctx.author.avatar_url)
                for question, response in zip(questions, form_responses):
                    embed.add_field(name=question, value=response, inline=False)
                embed.set_footer(text="Staff: When finished with ticket, click the Close button first. When ready to delete the channel, click the Delete button.")
                message = await ticket_channel.send(embed=embed, components=[action_row])

                self.cursor.execute('''
                    INSERT INTO tickets (userid, ticket_type, creation_time, questions, answers, message_id, channel_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (ctx.author.id, selected_option, timestamp, str(questions), str(form_responses), message.id, ticket_channel.id))
                self.conn.commit()
        except Exception as e:
            print(f"An error occurred while processing the interaction: {e}")

    @cog_ext.cog_component()
    async def close_ticket(self, ctx: ComponentContext):
        AllowedRoles = [ROLEIDS["Admin"], ROLEIDS["Moderator"], ROLEIDS["Helper"]]
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            await ctx.send("You do not have permission to close tickets.", hidden=True)
            return

        self.cursor.execute("SELECT userid, message_id FROM tickets WHERE channel_id = ?", (ctx.channel.id,))
        ticket = self.cursor.fetchone()
        if ticket is None:
            await ctx.send("No such ticket found.")
            return

        members = ctx.channel.members

        for member in members:
            if not any(role.id in AllowedRoles for role in member.roles):
                await ctx.channel.set_permissions(member, overwrite=None)

        await ctx.send("Ticket closed.", hidden=True)
        self.cursor.execute('''
            UPDATE tickets
            SET closed_by = ?
            WHERE channel_id = ?
        ''', (ctx.author.id, ctx.channel.id))
        self.conn.commit()
        await utils.LogAction(
            ctx.guild,
            "ModLogs",
            "Ticket Closed",
            ctx.author.id,
            f"Ticket {ctx.channel.name} closed by {ctx.author.name}",
            ctx.author,
        )

    @cog_ext.cog_component()
    async def delete_ticket(self, ctx: ComponentContext):
        AllowedRoles = [ROLEIDS["Admin"], ROLEIDS["Moderator"], ROLEIDS["Helper"]]
        if not any(role.id in AllowedRoles for role in ctx.author.roles):
            await ctx.send("You do not have permission to delete tickets.", hidden=True)
            return

        self.cursor.execute("SELECT userid, ticket_type, creation_time, message_id FROM tickets WHERE channel_id = ?", (ctx.channel.id,))
        ticket = self.cursor.fetchone()
        if ticket is None:
            await ctx.send("No such ticket found.")
            return

        await ctx.channel.delete()

        await ctx.send("Ticket deleted.", hidden=True)
        self.cursor.execute('''
            DELETE FROM tickets
            WHERE userid = ? AND ticket_type = ? AND creation_time = ?
        ''', (ticket[0], ticket[1], ticket[2]))
        self.conn.commit()
        await utils.LogAction(
            ctx.guild,
            "ModLogs",
            "Ticket Deleted",
            ctx.author.id,
            f"Ticket {ctx.channel.name} deleted by {ctx.author.name}",
            ctx.author,
        )

    @cog_ext.cog_slash(name="showtickets", description="Get all tickets from the database.")
    async def showtickets(self, ctx: SlashContext):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        self.cursor.execute("SELECT * FROM tickets")
        tickets = self.cursor.fetchall()
        if not tickets:
            await ctx.send("No tickets found in the database.")
            return
        tickets_by_user = {}
        for ticket in tickets:
            userid, ticket_type, creation_time, questions, answers, closed_by = ticket
            if userid not in tickets_by_user:
                tickets_by_user[userid] = []
            tickets_by_user[userid].append((ticket_type, creation_time, questions, answers, closed_by))

        paginator = Paginator()

        for userid, user_tickets in tickets_by_user.items():
            user = self.bot.get_user(userid)
            if user is None:
                continue

            embed = Embed(title=f"Tickets for {user.name}", description=f"Total tickets: {len(user_tickets)}")
            embed.set_author(name=user.name, icon_url=user.avatar_url)
            embed.set_footer(text="Use the reactions to navigate through the pages.")

            for ticket_type, creation_time, questions, answers, closed_by in user_tickets:
                field_value = f"Questions: {questions}\nAnswers: {answers}\nClosed by: {closed_by}"
                if len(embed) + len(field_value) > 6000:
                    paginator.add_page(embed)
                    embed = Embed(title=f"Tickets for {user.name} (cont'd)", description=f"Total tickets: {len(user_tickets)}")
                    embed.set_author(name=user.name, icon_url=user.avatar_url)
                    embed.set_footer(text="Use the reactions to navigate through the pages.")
                embed.add_field(name=f"Ticket: {ticket_type} ({creation_time})", value=field_value, inline=False)
            paginator.add_page(embed)
        await paginator.start(ctx)

    @cog_ext.cog_slash(name="viewtickets", description="View all tickets from a user.",
        options=[create_option(name="userid", description="User ID of the ticket owner", option_type=3, required=True)], guild_ids=[GUILDID])
    async def viewtickets(self, ctx: SlashContext, userid: int):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        userid = int(userid)
        self.cursor.execute("SELECT * FROM tickets WHERE userid = ?", (userid,))
        tickets = self.cursor.fetchall()
        if not tickets:
            await ctx.send("No tickets found for this user.")
            return

        embeds = []
        for ticket in tickets:
            userid, ticket_type, creation_time, questions, answers, closed_by = ticket
            user = self.bot.get_user(userid)
            if user is None:
                await ctx.send("User not found.")
                return

            embed = discord.Embed(title=f"Ticket for {user.name}", description=f"Ticket type: {ticket_type}\nCreation time: {creation_time}")
            embed.set_author(name=user.name, icon_url=user.avatar_url)
            embed.add_field(name="Questions", value=questions, inline=False)
            embed.add_field(name="Answers", value=answers, inline=False)
            embed.add_field(name="Closed by", value=closed_by, inline=False)
            embeds.append(embed)
        paginator = Paginator(ctx, embeds)
        await paginator.start()

    @cog_ext.cog_slash(name="deleteticket", description="Delete a specific ticket from a user.",
        options=[
            create_option(name="userid", description="User ID of the ticket owner", option_type=3, required=True),
            create_option(name="ticket_type", description="Type of the ticket", option_type=3, required=True),
            create_option(name="creation_time", description="Creation time of the ticket", option_type=3, required=True)
        ], guild_ids=[GUILDID])
    async def deleteticket(self, ctx: SlashContext, userid: int, ticket_type: str, creation_time: str):
        if isinstance(ctx, SlashContext):
            AllowedRoles = [ROLEIDS["Moderator"], ROLEIDS["Admin"]]
            if not any(role_id in [role.id for role in ctx.author.roles] for role_id in AllowedRoles):
                await ctx.send('You do not have permission to use this command.')
                return

        self.cursor.execute("DELETE FROM tickets WHERE userid = ? AND ticket_type = ? AND creation_time = ?", (userid, ticket_type, creation_time))
        self.conn.commit()
        await ctx.send("Ticket deleted.")

def setup(bot):
    bot.add_cog(Tickets(bot))