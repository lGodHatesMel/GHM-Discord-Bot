import discord
from discord.ext import commands
import pytz
from datetime import datetime
import random

def get_local_time(timezone='US/Eastern'):
    local_timezone = pytz.timezone(timezone)
    utc_time = datetime.utcnow()
    local_time = utc_time.astimezone(local_timezone)
    return local_time.strftime('%Y-%m-%d %H:%M:%S %Z')

# Function to customize command visibility based on roles
def is_visible(allowed_roles):
    def predicate(ctx):
        async def check(ctx):
            if ctx.author.id == ctx.guild.owner_id:
                return True

            user_roles = ctx.author.roles
            for role_name in allowed_roles:
                required_role = discord.utils.get(ctx.guild.roles, name=role_name)
                if required_role and required_role in user_roles:
                    return True

            await ctx.send(f"You don't have the required roles ({', '.join(allowed_roles)}) or higher to use this command.")
            return False

        return commands.check(check)

    return predicate

# Function to format set details with line breaks
def format_set_details(set_details):
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
        if i in set_details:
            set_details = set_details.replace(i, f"\n{i}")

    return set_details

def get_random_pokemon_fact():
    pokemon_facts = [
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
    
    return random.choice(pokemon_facts)