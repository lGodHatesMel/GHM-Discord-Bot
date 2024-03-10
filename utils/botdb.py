import sqlite3
from sqlite3 import Error

def CreateUserDatabase(database):
    conn = None
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS UserInfo (
                uid TEXT PRIMARY KEY,
                info TEXT NOT NULL
            );
        ''')
        return conn
    except Error as e:
        print(e)
    return conn

def CreateRulesDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rules (
                id INTEGER PRIMARY KEY,
                rule TEXT,
                description TEXT
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateCountdownDatabase(conn):
    try:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS countdowns (
                id INTEGER PRIMARY KEY,
                message TEXT,
                end_message TEXT,
                end_timestamp INTEGER,
                channel_id INTEGER
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateCustomCommandsDatabase(cursor, table_name):
    try:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {table_name} (
                command_name TEXT PRIMARY KEY,
                command_response TEXT
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def createFAQDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq (
                name TEXT PRIMARY KEY,
                question TEXT,
                answer TEXT
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateFAQAliasesTable(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS faq_aliases (
                alias TEXT PRIMARY KEY,
                faq_name TEXT
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateStarboardDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS starboard_table (
                message_id INTEGER PRIMARY KEY,
                author_id INTEGER,
                star_count INTEGER,
                starboard_id INTEGER,
                channel_id INTEGER,
                creation_date TEXT
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateTodoDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS todo (
                unique_id integer primary key, 
                user_id text, 
                time text, 
                task text, 
                subtasks text
                )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateStickyNotesDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sticky_notes (
                channel_id INTEGER,
                author_id INTEGER,
                content TEXT,
                message INTEGER
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def TwitterDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS twitter_users (
                user_id TEXT
            )
        ''')
    except sqlite3.Error as e:
        print(e)


def GiveawaysDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaways (
                title TEXT,
                description TEXT,
                end_time TEXT,
                message_id INTEGER
            )
        ''')
        cursor.execute("PRAGMA table_info(giveaways)")
        columns = cursor.fetchall()
        if not any(column[1] == 'winner_id' for column in columns):
            cursor.execute("ALTER TABLE giveaways ADD COLUMN winner_id INTEGER")
    except sqlite3.Error as e:
        print(e)

def CreateGiveawaysEntries(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_entries (
                message_id INTEGER,
                user_id INTEGER
            )
        ''')
    except sqlite3.Error as e:
        print(e)

def CreateEconomyDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS economy (
                user_id TEXT,
                balance REAL
            )
        ''')
    except sqlite3.Error as e:
        print(e)
    return cursor

def CreateTriviaDatabase(cursor):
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_coins (
                user_id TEXT PRIMARY KEY,
                right_count INTEGER,
                wrong_count INTEGER,
                total_coins INTEGER
            )
        ''')
    except sqlite3.Error as e:
        print(e)
    return cursor