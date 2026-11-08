import sqlite3
from pathlib import Path
import json

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
                vault_tier INTEGER DEFAULT 1
            )
            """)
        self.conn.commit()

    def create_user(self, user_id: int):
        self.cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, money, vault, equipment, inventory, bank, job, courses, aura, password, vault_tier) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, 1000, 0, "", '{}', 0, "", '[]', 0, "", 1)
        )
        self.conn.commit()
#------------------------------------------
    def get_user_data(self, parameter, user_id: int):
        self.create_user(user_id)
        self.cursor.execute(
            f"SELECT {parameter} FROM users WHERE user_id = ?",
            (user_id,)
        )
        data = self.cursor.fetchone()[0]
        return data
#------------------------------------------    
    def post_user_data(self, parameter, user_id, data):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)

        self.cursor.execute(
            f"UPDATE users SET {parameter} = ? WHERE user_id = ?",
            (data, user_id)
        )

        self.conn.commit()
#------------------------------------------    
    def get_all_data(self):
        self.cursor.execute("SELECT * FROM users")
        return self.cursor.fetchall()
    
    def add_missing_columns(self):
        sql_renomear = "ALTER TABLE users RENAME COLUMN xp TO aura;"
        self.cursor.execute(sql_renomear)

        self.conn.commit()
        print("Tabela renomeada com sucesso!")


    def sql_command(self, command):
        self.cursor.execute(f"""
                {command}
            """)
        self.conn.commit()

db = Database()