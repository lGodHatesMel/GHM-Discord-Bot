import sqlite3
from sqlite3 import Error

def create_connection(database):
    conn = None
    try:
        conn = sqlite3.connect(database)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS UserInfo (
                uid TEXT PRIMARY KEY,
                info TEXT NOT NULL
            );
        """)
        return conn
    except Error as e:
        print(e)
    return conn