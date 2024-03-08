import discord
from discord.ext import commands
from config import CHANNEL_IDS
from datetime import datetime, timezone, timedelta
import pytz
import random
import json


def load_emojis():
    with open('Data/CustomEmojis.json', 'r') as f:
        return json.load(f)
custom_emojis = load_emojis()

# Currently used with Polls
EmojiNumbers = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']

def GenerateNumber():
    return random.randint(1, 9999)

def TruncateText(text, length):
    return text[:length]

def GetLocalTime():
    utc_now = datetime.now(timezone.utc)
    target_timezone = pytz.timezone('US/Eastern')
    local_time = utc_now.astimezone(target_timezone)
    return local_time

def TimeDelta(days=0, hours=0, minutes=0, seconds=0):
    return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)


async def FetchMember(guild, target):
    if isinstance(target, str):
        try:
            return await guild.FetchMember(target)
        except discord.NotFound:
            raise ValueError(f"User with ID {target} not found")
    return target

async def GetMember(ctx, user_id):
    member = ctx.guild.GetMember(user_id)
    if member is None:
        raise ValueError("Member not found in this server.")
    return member

def GetMention(target):
    if isinstance(target, (discord.Role, discord.User)):
        return target.mention
    else:
        return target.name


ACTIONS = {
    "Kick":         {"emoji": "👢",  "color": discord.Color.orange()},
    "Ban":          {"emoji": "🔨",  "color": discord.Color.red()},
    "SoftBan":      {"emoji": "⏳",  "color": discord.Color.gold()},
    "Unban":        {"emoji": "🕊️",  "color": discord.Color.green()},
    "Warning":      {"emoji": "⚠️",  "color": discord.Color(0xFFFF00)}, # Yellow
    "Note":         {"emoji": "📝",  "color": discord.Color.blue()},
    "Database":     {"emoji": "💾",  "color": discord.Color.teal()},
    "Edit":         {"emoji": "✏️",  "color": discord.Color.blurple()},
    "Deletion":     {"emoji": "🗑️",  "color": discord.Color.dark_red()},
    "Blacklisted":  {"emoji": "🚫",  "color": discord.Color.dark_grey()},
    "BOT DM":       {"emoji": "🤖",  "color": discord.Color.light_grey()},
}

async def LogAction(guild, channel_name, action, target, reason, issuer=None, user_data=None, config=None, embed=None):
    if not config:
        raise ValueError("config is required for LogAction")

    ChannelID = CHANNEL_IDS.get(channel_name)
    if not ChannelID:
        raise ValueError(f"{channel_name} is not defined in the config")

    channel = guild.get_channel(ChannelID)
    if not channel:
        raise ValueError(f"Channel with ID {ChannelID} not found")

    action_data = ACTIONS.get(action, {"emoji": "", "color": discord.Color.red()})
    emoji = action_data["emoji"]
    embed_color = action_data["color"]
    timestamp = GetLocalTime()
    target = await FetchMember(guild, target)

    embed = discord.Embed(
        title=f"{emoji} {action}",
        color=embed_color,
        timestamp=timestamp
    )

    field_name = "DM Message" if action == 'BOT DM' else "Reason"

    if len(reason) > 1024:
        reason = reason[:1021] + '...'

    embed.add_field(name=field_name, value=reason, inline=False)
    embed.add_field(name="User", value=f"{target.mention} ({target.name})", inline=False)

    if issuer:
        value = issuer if isinstance(issuer, str) else issuer.mention
        embed.add_field(name="Issuer", value=value, inline=False)

    if user_data and action == 'Ban':
        bans = [ban for ban in user_data.get("banned", [])]
        for ban in bans:
            timestamp = ban['timestamp'].strftime('%m-%d-%y %I:%M %p')
            embed.add_field(
                name="Ban Info",
                value=f"Date/Time: {timestamp}\nIssuer: {ban['issuer']}\nReason: {ban['reason']}\nLifted: {ban['lifted']}\nUnban Reason: {ban.get('unban_reason', 'N/A')}",
                inline=False,
            )
    await channel.send(embed=embed)


async def LogUserChange(user, change_message):
    MemberLogChannelId = CHANNEL_IDS.get('MemberLogs', None)
    if MemberLogChannelId:
        ModLogsChannelID = user.guild.get_channel(int(MemberLogChannelId))
        if ModLogsChannelID:
            embed = discord.Embed(
                title="User Changes",
                description=f"User: {user.mention}",
                color=discord.Color.green(),
            )
            embed.set_author(name=f"{user.name}", icon_url=user.avatar_url)
            change_message = change_message.replace("Roles added: ", "Roles Added:\n")
            change_message = change_message.replace("Roles removed: ", "Roles Removed:\n")
            change_message = change_message.replace(", ", "\n")
            embed.add_field(name="**Updated Details**", value=change_message, inline=False)
            timestamp = GetLocalTime().strftime('%m-%d-%y %I:%M %p')
            embed.set_footer(text=f"UID: {user.id} • {timestamp}")
            await ModLogsChannelID.send(embed=embed)

async def LogBlacklistedWords(channel, action, target, reason, user_id):
    timestamp = GetLocalTime().strftime('%m-%d-%y %I:%M %p')
    embed = discord.Embed(color=discord.Color.red())
    embed.set_author(name=f"{target.name}", icon_url=target.avatar_url)
    embed.description = f"{action} in {channel.mention}"
    embed.add_field(name=f"{action} Message", value=reason, inline=False)
    embed.set_footer(text=f"UID: {user_id} • {timestamp}")
    if len(embed.fields) > 25:
        embed.fields = embed.fields[:25]
    await channel.send(embed=embed)


def RandomPKMFacts():
    with open('Data/PKMFacts.txt', 'r') as file:
        PKMFacts = file.read().splitlines()
    return random.choice(PKMFacts)


# Function to format set details with line breaks
def FormatedSetDetails(SetDetails):
    splittables = [
        "Ability:", "EVs:", "IVs:", "Shiny:", "Gigantamax:", "Ball:", "- ", "Level:",
        "Happiness:", "Language:", "OT:", "OTGender:", "TID:", "SID:", "Alpha:", "Tera Type:",
        "Adamant Nature", "Bashful Nature", "Brave Nature", "Bold Nature", "Calm Nature",
        "Careful Nature", "Docile Nature", "Gentle Nature", "Hardy Nature", "Hasty Nature",
        "Impish Nature", "Jolly Nature", "Lax Nature", "Lonely Nature", "Mild Nature",
        "Modest Nature", "Naive Nature", "Naughty Nature", "Quiet Nature", "Quirky Nature",
        "Rash Nature", "Relaxed Nature", "Sassy Nature", "Serious Nature", "Timid Nature",
        "*",
    ]
    for i in splittables:
        if i in SetDetails:
            SetDetails = SetDetails.replace(i, f"\n{i}")
    return SetDetails