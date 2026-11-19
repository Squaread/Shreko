import sqlite3
from pathlib import Path
import json

from core import logging as logger

blacklist = []

class Database:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent

        self.conn = sqlite3.connect(BASE_DIR/"user_data.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                money INTEGER DEFAULT 0,
                vault INTEGER DEFAULT 0,
                equipment TEXT,
                inventory TEXT,
                bank INTEGER DEFAULT 0,
                job TEXT,
                courses TEXT DEFAULT '[]',
                aura INTEGER DEFAULT 0,
                password TEXT,
                vault_tier INTEGER DEFAULT 1,
                blacklist BOOLEAN NOT NULL DEFAULT 0 CHECK (blacklist IN (0, 1))
            )
            """)
        self.conn.commit()

    def create_user(self, user_id: int):
        self.cursor.execute("INSERT OR IGNORE INTO users (user_id, money, vault, equipment, inventory, bank, job, courses, aura, password, vault_tier, blacklist) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, 1000, 0, "", '{}', 0, "", '[]', 0, "", 1, 0))
        self.conn.commit()

#------------------------------------------
    def get_user_data(self, parameter, user_id: int):
        self.create_user(user_id)
        self.cursor.execute(f"SELECT {parameter} FROM users WHERE user_id = ?",
            (user_id,))
        data = self.cursor.fetchone()[0]
        return data
#------------------------------------------    
    def post_user_data(self, parameter, user_id, data):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)

        self.cursor.execute(f"UPDATE users SET {parameter} = ? WHERE user_id = ?",
            (data, user_id))

        self.conn.commit()
        logger.database(f"Post user data: {parameter} {user_id} {data}")
#------------------------------------------    
    def get_all_data(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()
#------------------------------------------    
    def filter_users(self, parameter, data):
        self.cursor.execute(f"SELECT * FROM users WHERE {parameter} = ?",
            (data,))
        return self.cursor.fetchall()
#------------------------------------------
    def delete_all_user_data(self, user_id):
        self.cursor.execute("DELETE FROM users WHERE id = ?", 
            (user_id,))
        self.conn.commit()

        logger.database(f"Delete all user data: {user_id}")
#------------------------------------------
    def add_missing_columns(self):
        self.cursor.execute("ALTER TABLE users ADD COLUMN blacklist INTEGER DEFAULT 0;")
        self.conn.commit()
        print("Coluna adicionada com sucesso!")
#------------------------------------------
    def sql_command(self, command):
        self.cursor.execute(f"{command}")
        self.conn.commit()
        logger.database(f"SQL command: {command}")

db = Database()