def load_trivia_questions(self):
        if os.path.exists(self.trivia_questions_file):
            with open(self.trivia_questions_file, 'r') as f:
                file_contents = f.read()
                print("File Contents:", repr(file_contents))

                if not file_contents:
                    self.trivia_questions = {
                    "easy": [
                        {"question": "What is the second Pokémon in the Pokédex?", "answer": "Ivysaur", "reward": 1},
                        {"question": "Which Pokémon evolves into Raichu?", "answer": "Pichu", "reward": 1},
                        {"question": "What is the type of Jigglypuff?", "choices": ["Normal", "Fairy"], "answer": "Normal", "reward": 1},
                        {"question": "Which Pokémon is known for its ability to fly?", "answer": "Pidgey", "reward": 1},
                        {"question": "What is the primary type of Meowth?", "answer": "Normal", "reward": 1},
                        {"question": "Which Pokémon is known for its long, serpentine body?", "answer": "Ekans", "reward": 1},
                        {"question": "What type is Bulbasaur?", "choices": ["Grass", "Poison"], "answer": "Grass", "reward": 1},
                        {"question": "Which Pokémon has the ability to generate electricity in its cheeks?", "answer": "Pichu", "reward": 1},
                        {"question": "What is the evolved form of Magikarp?", "answer": "Gyarados", "reward": 1},
                        {"question": "Which Pokémon has a flame at the end of its tail?", "answer": "Charmander", "reward": 1},
                        {"question": "What is the primary type of Psyduck?", "answer": "Water", "reward": 1},
                        {"question": "Which Pokémon resembles a turtle?", "answer": "Squirtle", "reward": 1},
                        {"question": "What is the first Pokémon Ash caught?", "answer": "Caterpie", "reward": 1},
                        {"question": "Which Pokémon is known for its strong psychic abilities?", "answer": "Abra", "reward": 1},
                        {"question": "What type is Eevee?", "answer": "Normal", "reward": 1},
                    ],
                    "medium": [
                        {"question": "Which Pokémon is known as the 'Shellfish Pokémon'?", "answer": "Shellder", "reward": 2},
                        {"question": "What is the main type advantage of Electric against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Butterfree?", "answer": "Metapod", "reward": 2},
                        {"question": "What is the main type advantage of Grass against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon is known for its ability to paralyze?", "answer": "Pikachu", "reward": 2},
                        {"question": "What is the main type advantage of Ice against Grass?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Wartortle?", "answer": "Squirtle", "reward": 2},
                        {"question": "What is the main type advantage of Fighting against Normal?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Nidoking?", "answer": "Nidorino", "reward": 2},
                        {"question": "What is the main type advantage of Psychic against Poison?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon is known as the 'Gas Pokémon'?", "answer": "Koffing", "reward": 2},
                        {"question": "What is the main type advantage of Ground against Electric?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon evolves into Jolteon?", "answer": "Eevee", "reward": 2},
                        {"question": "What is the main type advantage of Fairy against Fighting?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                        {"question": "Which Pokémon is known for its ability to absorb sunlight?", "answer": "Oddish", "reward": 2},
                    ],
                    "hard": [
                        {"question": "Which Pokémon is known as the 'Cocoon Pokémon'?", "answer": "Metapod", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the sea?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Articuno", "reward": 3},
                        {"question": "Which Pokémon evolves into Dragonair?", "answer": "Dratini", "reward": 3},
                        {"question": "What is the evolved form of Haunter?", "answer": "Gengar", "reward": 3},
                        {"question": "Which Pokémon is known for its ability to manipulate time?", "answer": "Celebi", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the sky?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                        {"question": "Which Pokémon evolves into Tyranitar?", "answer": "Pupitar", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the volcano?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Moltres", "reward": 3},
                        {"question": "Which Pokémon is known for its ability to manipulate space?", "answer": "Palkia", "reward": 3},
                        {"question": "What is the legendary trio of Sinnoh?", "choices": ["Uxie", "Mesprit", "Azelf"], "answer": "Uxie", "reward": 3},
                        {"question": "Which Pokémon evolves into Salamence?", "answer": "Shelgon", "reward": 3},
                        {"question": "What is the legendary bird Pokémon of the thunder?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                        {"question": "Which Pokémon is known for its ability to travel between dimensions?", "answer": "Giratina", "reward": 3},
                        {"question": "What is the legendary trio of Johto?", "choices": ["Raikou", "Entei", "Suicune"], "answer": "Raikou", "reward": 3},
                        {"question": "Which Pokémon evolves into Lucario?", "answer": "Riolu", "reward": 3},
                    ],
                }
                else:
                    try:
                        self.trivia_questions = json.loads(file_contents)
                    except json.JSONDecodeError as e:
                        print("Error decoding JSON:", e)
        else:
            self.trivia_questions = {
            "easy": [
                {"question": "What is the second Pokémon in the Pokédex?", "answer": "Ivysaur", "reward": 1},
                {"question": "Which Pokémon evolves into Raichu?", "answer": "Pichu", "reward": 1},
                {"question": "What is the type of Jigglypuff?", "choices": ["Normal", "Fairy"], "answer": "Normal", "reward": 1},
                {"question": "Which Pokémon is known for its ability to fly?", "answer": "Pidgey", "reward": 1},
                {"question": "What is the primary type of Meowth?", "answer": "Normal", "reward": 1},
                {"question": "Which Pokémon is known for its long, serpentine body?", "answer": "Ekans", "reward": 1},
                {"question": "What type is Bulbasaur?", "choices": ["Grass", "Poison"], "answer": "Grass", "reward": 1},
                {"question": "Which Pokémon has the ability to generate electricity in its cheeks?", "answer": "Pichu", "reward": 1},
                {"question": "What is the evolved form of Magikarp?", "answer": "Gyarados", "reward": 1},
                {"question": "Which Pokémon has a flame at the end of its tail?", "answer": "Charmander", "reward": 1},
                {"question": "What is the primary type of Psyduck?", "answer": "Water", "reward": 1},
                {"question": "Which Pokémon resembles a turtle?", "answer": "Squirtle", "reward": 1},
                {"question": "What is the first Pokémon Ash caught?", "answer": "Caterpie", "reward": 1},
                {"question": "Which Pokémon is known for its strong psychic abilities?", "answer": "Abra", "reward": 1},
                {"question": "What type is Eevee?", "answer": "Normal", "reward": 1},
            ],
            "medium": [
                {"question": "Which Pokémon is known as the 'Shellfish Pokémon'?", "answer": "Shellder", "reward": 2},
                {"question": "What is the main type advantage of Electric against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Butterfree?", "answer": "Metapod", "reward": 2},
                {"question": "What is the main type advantage of Grass against Water?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon is known for its ability to paralyze?", "answer": "Pikachu", "reward": 2},
                {"question": "What is the main type advantage of Ice against Grass?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Wartortle?", "answer": "Squirtle", "reward": 2},
                {"question": "What is the main type advantage of Fighting against Normal?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Nidoking?", "answer": "Nidorino", "reward": 2},
                {"question": "What is the main type advantage of Psychic against Poison?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon is known as the 'Gas Pokémon'?", "answer": "Koffing", "reward": 2},
                {"question": "What is the main type advantage of Ground against Electric?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon evolves into Jolteon?", "answer": "Eevee", "reward": 2},
                {"question": "What is the main type advantage of Fairy against Fighting?", "choices": ["Super Effective", "Not Effective", "No Advantage"], "answer": "Super Effective", "reward": 2},
                {"question": "Which Pokémon is known for its ability to absorb sunlight?", "answer": "Oddish", "reward": 2},
            ],
            "hard": [
                {"question": "Which Pokémon is known as the 'Cocoon Pokémon'?", "answer": "Metapod", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the sea?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Articuno", "reward": 3},
                {"question": "Which Pokémon evolves into Dragonair?", "answer": "Dratini", "reward": 3},
                {"question": "What is the evolved form of Haunter?", "answer": "Gengar", "reward": 3},
                {"question": "Which Pokémon is known for its ability to manipulate time?", "answer": "Celebi", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the sky?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                {"question": "Which Pokémon evolves into Tyranitar?", "answer": "Pupitar", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the volcano?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Moltres", "reward": 3},
                {"question": "Which Pokémon is known for its ability to manipulate space?", "answer": "Palkia", "reward": 3},
                {"question": "What is the legendary trio of Sinnoh?", "choices": ["Uxie", "Mesprit", "Azelf"], "answer": "Uxie", "reward": 3},
                {"question": "Which Pokémon evolves into Salamence?", "answer": "Shelgon", "reward": 3},
                {"question": "What is the legendary bird Pokémon of the thunder?", "choices": ["Articuno", "Zapdos", "Moltres"], "answer": "Zapdos", "reward": 3},
                {"question": "Which Pokémon is known for its ability to travel between dimensions?", "answer": "Giratina", "reward": 3},
                {"question": "What is the legendary trio of Johto?", "choices": ["Raikou", "Entei", "Suicune"], "answer": "Raikou", "reward": 3},
                {"question": "Which Pokémon evolves into Lucario?", "answer": "Riolu", "reward": 3},
            ],
        }

        self.user_coins = {}
        self.post_question.start()