import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
import pytz
import random

custom_emojis = {
    "nitroboost": "<:nitroboost:1211532554578952303>",
    "last_page": "<:Last_Page:1211360319352479754>",
    "boosttheserver": "<:boosttheserver:1211532493963010159>",
    "readrules": "<:readrules:1209938853343924295>",
    "nintendo_switch": "<:nintendo_switch:1211354515224141865>",
    "cute_arrow": "<:cute_arrow:1209924743969378424>",
    "moderation": "<:moderation:1209933852848562216>",
    "Giveaways": "<:Giveaways:964890435740897320>",
    "sv": "<:sv:992912626533273770>",
    "bdsp": "<:bdsp:957043167071457300>",
    "swsh": "<:swsh:957043238043258960>",
    "arceus": "<:arceus:957042842281345084>",
    "pikagun": "<:pikagun:1211355558888738857>",
    "wrongchannel": "<:wrongchannel:1211354438632087632>",
    "bruheevee": "<:bruheevee:1211355485421305916>",
    "rizz": "<:rizz:1209932282257735680>",
    "pikapout": "<:pikapout:1211355412977287219>",
    "thx": "<:thx:1165294866645909639>",
    "ping": "<:pinged:1211542356780781628>",
    "pw_grizzbolt": "<:pw_grizzbolt:1211542358676742204>",
    "acnh": "<:acnh:1211543299979083796>",

    # Animated emojis
    "lightingbolt": "<a:lightingbolt:1211532526401749002>",
    "pikahello": "<a:pikahello:1211355773754413107>",
    "trainer_pixel": "<a:trainer_pixel:1211354730584866907>",
    "dittodance": "<a:dittodance:1211357556090478614>",
    "pika_minecraft": "<a:pika_minecraft:1211357535005573270>",
    "pokeball_success": "<a:pokeball_success:1211358242723201064>",
    "pikacheeks": "<a:pikacheeks:1211356756224118934>"
}


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
## All possible discord.Color choices
# discord.Color.default()     discord.Color.dark_teal()    discord.Color.teal()       discord.Color.dark_green()
# discord.Color.green()       discord.Color.dark_blue()    discord.Color.blue()       discord.Color.dark_purple()
# discord.Color.purple()      discord.Color.dark_magenta() discord.Color.magenta()    discord.Color.dark_gold()
# discord.Color.gold()        discord.Color.dark_orange()  discord.Color.orange()     discord.Color.dark_red()
# discord.Color.red()         discord.Color.lighter_grey() discord.Color.light_grey() discord.Color.dark_grey()
# discord.Color.darker_grey() discord.Color.blurple()      discord.Color.greyple()    discord.Color.dark_theme()
# discord.Color(0xFFFF00)}(Yellow)  discord.Color(0x00FF00)}(Lime)  discord.Color(0x0000FF)}(Blue) 
# discord.Color(0xFF00FF)}(Magenta)

def GenerateNumber():
    return random.randint(1, 9999)


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


async def LogAction(guild, channel_name, action, target, reason, issuer=None, user_data=None, config=None, embed=None):
    if not config:
        raise ValueError("config is required for LogAction")

    ChannelID = config['channel_ids'].get(channel_name)
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

    embed.add_field(name="User", value=f"{target.mention} ({target.name})", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)

    if issuer:
        value = issuer if isinstance(issuer, str) else issuer.mention
        embed.add_field(name="Issuer", value=value, inline=False)
    
    # if action in ('Ban', 'Unban', 'SoftBanned') and issuer:
    #     value = issuer if isinstance(issuer, str) else issuer.mention
    #     embed.add_field(name="Issuer", value=value, inline=True)

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


def RandomPKMFacts():
    PKMFacts = [
        "Jigglypuff's singing can put anyone to sleep, even in real life!",
        "Magikarp's 'Splash' move is secretly a powerful technique that no one understands.",
        "MissingNo. is the only Pokemon that can crash a Game Boy game.",
        "Pikachu's favorite snack is ketchup, according to the anime.",
        "Slowpoke is so slow that it once took an entire day for it to notice its tail was gone.",
        "Pokemon: The Animated Series has over 20 seasons and is still going strong.",
        "Ash Ketchum's dream is to become a Pokemon Master and catch 'em all.",
        "The Pokemon world is inhabited by many legendary and mythical Pokemon like Mewtwo and Celebi.",
        "Team Rocket's motto is one of the most iconic phrases in the series.",
        "The Pokemon League is where trainers compete to become champions.",
        "The first Pokemon games, Red and Green, were released in Japan in 1996.",
        "The most valuable Pokemon games are sealed, first-edition copies of Red and Blue.",
        "In Pokemon Yellow, Pikachu follows you around as your loyal companion.",
        "The Johto region introduced day and night cycles to Pokemon games.",
        "Pokemon Gold and Silver were the first games to feature breeding.",
        "The Pokemon TCG has thousands of different cards, including rare holographic ones.",
        "Charizard, Blastoise, and Venusaur are some of the most sought-after TCG cards.",
        "The TCG has its own competitive scene with tournaments and championships.",
        "Some TCG cards have different artwork depending on the set they come from.",
        "Collecting rare TCG cards is a hobby for many Pokemon fans.",
        "Satoshi Tajiri, the creator of Pokemon, was inspired by his childhood love of collecting insects.",
        "Game Freak, the company that makes Pokemon games, started as a self-published magazine.",
        "Pokemon Red and Green were developed by a team of only six people.",
        "The original Pokemon games were designed to be connected via a Link Cable.",
        "Ken Sugimori is the artist responsible for designing many iconic Pokemon.",
        "There are currently over 800 different Pokemon species.",
        "The term 'Pokemon' is short for 'Pocket Monsters' in Japanese.",
        "Ditto is the only Pokemon that can breed with any other Pokemon.",
        "Meowth is one of the few Pokemon that can speak human language.",
        "Gengar is believed to be Clefable's shadow, according to its Pokedex entry.",
        "Type matchups determine the effectiveness of Pokemon moves in battles.",
        "In the main games, each region has its own unique set of Pokemon species.",
        "Eevee has the most evolution options, with eight different forms.",
        "Pokemon can hold items that boost their stats or trigger special effects.",
        "Legendaries like Articuno, Zapdos, and Moltres are inspired by Greek mythology.",
        "Pikachu is one of the most recognizable mascots in the world.",
        "Pokemon's theme song, 'Gotta Catch 'Em All,' is an iconic tune.",
        "Pokemon movies have been released alongside the anime series.",
        "Pokemon has its own line of toys, clothing, and merchandise.",
        "The franchise holds the Guinness World Record for the most successful media franchise.",
        "The Alola region is inspired by the Hawaiian Islands and features unique regional forms.",
        "Galar, inspired by the UK, introduced the concept of Dynamaxing Pokemon.",
        "Hoenn, based on the Japanese island of Kyushu, is known for its diverse ecosystems.",
        "Unova is inspired by New York City and features a mix of urban and natural areas.",
        "Sinnoh's mythology is based on the creation trio: Dialga, Palkia, and Giratina.",
        "Mewtwo was genetically created from the DNA of the mythical Pokemon Mew.",
        "Rayquaza has the power to quell clashes between Kyogre and Groudon.",
        "Arceus is considered the god of all Pokemon and is said to have created the Pokemon world.",
        "Lugia, the guardian of the seas, plays a significant role in the second Pokemon movie.",
        "The legendary bird trio represents fire, lightning, and the north wind.",
        "Pikachu's name is a combination of 'pika' (electric spark sound) and 'chu' (mouse sound).",
        "The first generation of Pokémon, Generation I, consisted of 151 different species.",
        "Mew, the 151st Pokémon, was added secretly to the first-generation games.",
        "Lavender Town became infamous due to rumors of a theme song causing headaches and nightmares.",
        "Many Pokémon are inspired by real animals and objects, like Ekans and Muk.",
        "Blissey has the highest base HP stat of all Pokémon.",
        "Legendary Pokémon, like Mewtwo and Arceus, are extremely rare and have special roles.",
        "The Pokémon with the longest English name is 'Crabominable.'",
        "Rhydon was the first Pokémon ever designed by Satoshi Tajiri and Ken Sugimori.",
        "Pokémon games are available in numerous languages, including English.",
        "The Pokémon World Championships are held annually for video games and trading card game tournaments.",
        "Eevee can evolve into eight different forms, known as 'Eeveelutions.'",
        "Pokémon has had a profound impact on pop culture with TV series, movies, trading card games, and more.",
        "The original Pokémon Red and Green games were developed by Game Freak and published by Nintendo in 1996 (Japan) and 1998 (North America).",
        "The concept of Pokémon was inspired by Satoshi Tajiri's childhood interest in collecting creatures and his desire to connect Game Boy devices for trading.",
        "The rarest Pokémon card is the Pikachu Illustrator card, with only a few in existence. It was never released commercially and was given to winners of a Pokémon illustration contest.",
        "In the Pokémon world, there are many different regions, each with its own unique Pokémon species and culture, such as Kanto, Johto, and Sinnoh.",
        "Ash Ketchum, the protagonist of the Pokémon animated series, is known as Satoshi in Japan, named after Pokémon's creator, Satoshi Tajiri.",
        "Meowth, one of the Team Rocket trio's Pokémon, is known for being one of the few Pokémon that can speak human language.",
        "The Pokémon franchise includes a wide range of spin-off games, including Pokémon Snap, Pokémon Mystery Dungeon, and Pokémon GO.",
        "The first Pokémon movie, titled 'Pokémon: The First Movie - Mewtwo Strikes Back,' was released in 1998, followed by numerous other Pokémon movies.",
        "The Pokémon theme song, 'Gotta Catch 'Em All,' is one of the most recognizable and catchy theme songs in the history of animated series.",
        "Jigglypuff is known for putting opponents to sleep by singing a lullaby and then drawing on their faces with its marker-like pen.",
        "The original Pokémon Red and Green games allowed players to encounter a glitch Pokémon known as 'MissingNo,' which could duplicate items.",
        "Magikarp is often considered one of the weakest Pokémon but can evolve into the powerful Gyarados.",
        "The move 'Splash' has no effect in battles except for one special Magikarp in the Pokémon series that can use it to defeat a powerful opponent.",
        "The Pokémon world features a variety of items like Potions, Poké Balls, and Rare Candies to aid trainers in their journey.",
        "The Legendary Pokémon Articuno, Zapdos, and Moltres are inspired by the three legendary birds of Greek mythology: Articuno represents the north wind, Zapdos represents lightning, and Moltres represents fire.",
        "The Pokémon Ditto is known for its ability to transform into other Pokémon. It can breed with almost any Pokémon and produce offspring of that species.",
        "The type chart in Pokémon determines the strengths and weaknesses of different types, such as Water being strong against Fire but weak against Grass.",
        "The original Pokémon games were developed with the help of the Game Boy's link cable, allowing players to trade and battle Pokémon with their friends.",
        "The Pokémon anime series has been running since 1997 and has over a thousand episodes.",
        "Mewtwo, one of the most iconic Legendary Pokémon, was genetically created from the DNA of Mew.",
        "The Pokémon world is home to various villainous teams like Team Rocket, Team Aqua, and Team Galactic, each with its own nefarious plans.",
        "The Pokémon Pikachu is the franchise's official mascot and is featured prominently in marketing and promotional materials.",
        "The term 'shiny Pokémon' refers to rare variants of Pokémon with different color palettes. They have a 1 in 4,096 chance of appearing in the wild.",
        "There are different types of Poké Balls, each with varying levels of effectiveness in catching Pokémon. The Master Ball is the rarest and guarantees a capture.",
        "The Pokémon games often have two versions (e.g., Pokémon Red and Blue) with some exclusive Pokémon in each version, encouraging trading between players.",
        "The Pokémon Togepi is known for its ability to hatch from eggs, symbolizing new beginnings in the Pokémon world.",
        "Eevee's evolution into Espeon or Umbreon depends on the time of day in the games, adding a day-night mechanic to its evolution.",
        "The Legendary Pokémon Rayquaza is said to have the power to quell clashes between Kyogre and Groudon, two other Legendary Pokémon.",
        "The Pokémon Clefairy was originally considered to be the mascot of the franchise before Pikachu took its place.",
        "The Pokémon series has its own trading card game, which has been popular since its launch in the late 1990s.",
        "The Pokémon series has introduced various regions, including the tropical Alola region and the Galar region inspired by the United Kingdom.",
        "Mimikyu, a Ghost/Fairy-type Pokémon, wears a Pikachu costume to make friends because it believes that people dislike its true appearance.",
        "The Pokémon Psyduck is known for its chronic headaches, which can trigger its powerful Psychic-type abilities when the pain becomes too much to bear.",
        "The Pokémon Slowpoke has a tail that can detach and regenerate, leading to the creation of a dish called 'Slowpoke Tail' in the Pokémon world.",
        "The Pokémon franchise holds the Guinness World Record for the most successful video game-based media franchise.",
        "The Pokémon Ditto is the only Pokémon that can breed with genderless Pokémon and produce offspring.",
        "The evolution of Eevee into Glaceon or Leafeon depends on specific locations in the games, adding an environmental factor to its evolution.",
        "The Pokémon Meowth is known for its signature move 'Pay Day,' which can earn trainers extra in-game currency when used in battles.",
        "In the Pokémon series, Professor Oak, the first Pokémon professor, is known for his iconic line: 'Are you a boy or a girl?'",
        "The Pokémon Gengar is believed to be the shadow of Clefable, another Pokémon, according to its Pokédex entry.",
    ]
    return random.choice(PKMFacts)