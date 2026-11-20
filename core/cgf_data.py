import sqlite3
from pathlib import Path
import json
import random

from core.user_data import db as user_db

from modules.economy import service as EconomyService

from config import CGF, BANCO_CENTRAL

class Database:
    def __init__(self):
        BASE_DIR = Path(__file__).resolve().parent.parent

        self.conn = sqlite3.connect(BASE_DIR/"cgf_data.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                match_id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_type TEXT,
                team_1 INTEGER NOT NULL,
                team_2 INTEGER NOT NULL,
                teamgoals_1 INTEGER NOT NULL DEFAULT 0,
                teamgoals_2 INTEGER NOT NULL DEFAULT 0,
                winner INTEGER,
                stadium_id INTEGER,
                tickets_sold INTEGER DEFAULT 0,
                ticket_value INTEGER DEFAULT 0,
                expenses INTEGER DEFAULT 0,
                tax INTEGER DEFAULT 0,
                profit INTEGER DEFAULT 0,
                match_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (team_1) REFERENCES teams(team_id),
                FOREIGN KEY (team_2) REFERENCES teams(team_id),
                FOREIGN KEY (winner) REFERENCES teams(team_id),
                FOREIGN KEY (stadium_id) REFERENCES stadiums(stadium_id),
                CHECK (team_1 != team_2));
            """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS stadiums (
                stadium_id INTEGER PRIMARY KEY,
                stadium_name TEXT,
                capacity INTEGER DEFAULT 0,
                statistics TEXT DEFAULT '{"matches": 0, "goals": 0, "collected": 0, "visitors": 0}');
            """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS teams (
                team_id INTEGER PRIMARY KEY,
                team_name TEXT,
                stadium_id INTEGER,
                statistics TEXT DEFAULT '{"goals": 0, "goals_conceded": 0, "victories": 0, "draws": 0, "defeats": 0}',
                popularity INTEGER DEFAULT 0,

                FOREIGN KEY (stadium_id)
                    REFERENCES stadiums(stadium_id)
            );
        """)

        self.conn.commit()

    def get_team_data(self, parameter, team_id: int):
        self.cursor.execute(f"SELECT {parameter} FROM teams WHERE team_id = ?",
            (team_id,))
        data = self.cursor.fetchone()[0]
        return data

    def post_team_data(self, parameter, team_id, data):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)
        if isinstance(data, float):
            data = int(data)

        self.cursor.execute(f"UPDATE teams SET {parameter} = ? WHERE team_id = ?",
            (data, team_id))

        self.conn.commit()

    def get_all_teams_data(self):
        self.cursor.execute("""
            SELECT
                teams.team_id,
                teams.team_name,
                stadiums.stadium_name,
                teams.statistics,
                teams.popularity

            FROM teams

            LEFT JOIN stadiums
                ON teams.stadium_id = stadiums.stadium_id
        """)

        return self.cursor.fetchall()

    def get_stadium_data(self, parameter, stadium_id: int):
        self.cursor.execute(f"SELECT {parameter} FROM stadiums WHERE stadium_id = ?",
            (stadium_id,))
        data = self.cursor.fetchone()[0]
        return data
    
    def post_stadium_data(self, parameter, stadium_id, data):
        if isinstance(data, (dict, list)):
            data = json.dumps(data, ensure_ascii=False)
        if isinstance(data, float):
            data = int(data)

        self.cursor.execute(f"UPDATE stadiums SET {parameter} = ? WHERE stadium_id = ?",
            (data, stadium_id))

        self.conn.commit()

    def get_all_stadiums_data(self):
        self.cursor.execute("SELECT * FROM stadiums")
        return self.cursor.fetchall()

    def add_stadium(self, stadium_id, stadium_name, capacity):
        self.cursor.execute("""
            INSERT INTO stadiums (stadium_id, stadium_name, capacity)
            VALUES (?, ?, ?)
        """, (stadium_id, stadium_name, capacity))

        self.conn.commit()


    def edit_stadium(self, stadium_id, stadium_name, capacity):
        self.cursor.execute("""
            UPDATE stadiums
            SET stadium_name = ?, capacity = ?
            WHERE stadium_id = ?
        """, (stadium_name, capacity, stadium_id))

        self.conn.commit()


    def delete_stadium(self, stadium_id):
        self.cursor.execute("""
            DELETE FROM stadiums WHERE stadium_id = ?
        """, (stadium_id,))

        self.conn.commit()

    def add_team(self, team_id, team_name, stadium_id):
        self.cursor.execute("""
            INSERT INTO teams (team_id, team_name, stadium_id)
            VALUES (?, ?, ?)
        """, (team_id, team_name, stadium_id))

        self.conn.commit()

    def edit_team(self, team_id, team_name, stadium_id):
        self.cursor.execute("""
            UPDATE teams
            SET team_name = ?, stadium_id = ?
            WHERE team_id = ?
        """, (team_name, stadium_id, team_id))

        self.conn.commit()

    def delete_team(self, team_id):
        self.cursor.execute("""
            DELETE FROM teams WHERE team_id = ?
        """, (team_id,))

        self.conn.commit()

    def get_all_matches_data(self):
        self.cursor.execute("""
            SELECT
                m.match_id,
                m.match_type,

                m.team_1,
                t1.team_name,

                m.team_2,
                t2.team_name,

                m.teamgoals_1,
                m.teamgoals_2,

                m.winner,
                m.tickets_sold,
                m.match_date,

                m.stadium_id,
                s.stadium_name,

                m.ticket_value,
                m.expenses,
                m.tax,
                m.profit

            FROM matches m

            LEFT JOIN teams t1
                ON m.team_1 = t1.team_id

            LEFT JOIN teams t2
                ON m.team_2 = t2.team_id

            LEFT JOIN stadiums s
                ON m.stadium_id = s.stadium_id

            ORDER BY m.match_date DESC, m.match_id DESC
        """)

        return self.cursor.fetchall()

    def add_match(self, match_type, team_1, team_2, teamgoals_1, teamgoals_2, stadium_id, tickets_sold, ticket_value, tax, expenses, profit):

        if team_1 == team_2:
            raise ValueError("Os times precisam ser diferentes.")

        winner = None

        if teamgoals_1 > teamgoals_2:
            winner = team_1
        elif teamgoals_2 > teamgoals_1:
            winner = team_2

        self.cursor.execute("""
            INSERT INTO matches (
                match_type,
                team_1,
                team_2,
                teamgoals_1,
                teamgoals_2,
                winner,
                stadium_id,
                tickets_sold,
                ticket_value,
                tax,
                expenses,
                profit
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            match_type,
            team_1,
            team_2,
            teamgoals_1,
            teamgoals_2,
            winner,
            stadium_id,
            tickets_sold,
            ticket_value,
            tax,
            expenses,
            profit
        ))

        self.conn.commit()
        
db = Database()

def calc_match(team_1: int, team_2: int, stadium_id: int, match_type: str, ticket_value: int, goals_1: int, goals_2: int):
    # Multiplicadores dos tipos de partida
    match_multipliers = {
        "Amistoso": 0.65,
        "Pontos corridos": 1.00,
        "Fase de grupos": 1.10,
        "Oitavas de finais": 1.20,
        "Quartas de finais": 1.30,
        "Semifinal": 2.50,
        "Terceiro lugar": 1.15,
        "Final": 3.80
    }

    # Preço de referência por tipo de partida
    reference_prices = {
        "Amistoso": 20,
        "Pontos corridos": 50,
        "Fase de grupos": 90,
        "Oitavas de finais": 100,
        "Quartas de finais": 110,
        "Semifinal": 130,
        "Terceiro lugar": 100,
        "Final": 180
    }

    match_multiplier = match_multipliers.get(match_type, 1.0)
    reference_price = reference_prices.get(match_type, 80)

    # Popularidade dos times
    team_1_popularity = db.get_team_data("popularity", team_1) or 0
    team_2_popularity = db.get_team_data("popularity", team_2) or 0

    popularity = (team_1_popularity + team_2_popularity) / 2
    popularity = max(0, min(100, popularity))

    # Capacidade do estádio
    stadium_capacity = db.get_stadium_data("capacity", stadium_id) or 0

    # Influência do preço na procura
    ticket_value = max(0, ticket_value)

    price_variation = random.uniform(0.80, 1.50)
    adjusted_reference_price = reference_price * price_variation

    # Influência do preço na procura
    if ticket_value == 0:
        price_multiplier = 1.5
    else:
        price_multiplier = (adjusted_reference_price / ticket_value) ** 1.2
        price_multiplier = max(0, min(1.5, price_multiplier))

        if ticket_value > adjusted_reference_price*10000: price_multiplier = 0

    # Calcula a ocupação do estádio
    attendance_rate = 0.10 + (popularity / 100) * 0.65
    attendance_rate *= match_multiplier
    attendance_rate *= price_multiplier

    attendance_rate = max(0, min(1.0, attendance_rate))

    tickets_sold = min(
        stadium_capacity,
        int(stadium_capacity * attendance_rate)
    )

    # Receita bruta
    revenue = ticket_value * tickets_sold

    # Impostos
    economy = EconomyService.load_economy()
    tax_factor = economy.get("cgf_tax", 0.0)

    tax_value = int(revenue * tax_factor)

    # Despesas operacionais
    expenses_factor = random.uniform(0.30, 0.60)
    expenses = int((revenue * expenses_factor) + stadium_capacity*0.8)

    # Lucro líquido
    profit = revenue - expenses - tax_value

    # Credita o lucro na CGF
    current_balance = user_db.get_user_data("bank", CGF) or 0
    user_db.post_user_data("bank", CGF, current_balance + profit)

    # Impostos para o banco central
    central_balance = user_db.get_user_data("bank", BANCO_CENTRAL) or 0
    user_db.post_user_data("bank", BANCO_CENTRAL, central_balance + tax_value)

    # Atualiza estatísticas dos times
    team_1_statistics = json.loads(
        db.get_team_data("statistics", team_1) or "{}"
    )
    team_2_statistics = json.loads(
        db.get_team_data("statistics", team_2) or "{}"
    )

    # Gols marcados e sofridos
    team_1_statistics["goals"] = team_1_statistics.get("goals", 0) + goals_1
    team_2_statistics["goals"] = team_2_statistics.get("goals", 0) + goals_2

    team_1_statistics["goals_conceded"] = (
        team_1_statistics.get("goals_conceded", 0) + goals_2
    )
    team_2_statistics["goals_conceded"] = (
        team_2_statistics.get("goals_conceded", 0) + goals_1
    )

    # Resultado da partida
    if goals_1 > goals_2:
        team_1_statistics["victories"] = team_1_statistics.get("victories", 0) + 1
        team_2_statistics["defeats"] = team_2_statistics.get("defeats", 0) + 1

    elif goals_2 > goals_1:
        team_1_statistics["defeats"] = team_1_statistics.get("defeats", 0) + 1
        team_2_statistics["victories"] = team_2_statistics.get("victories", 0) + 1

    else:
        team_1_statistics["draws"] = team_1_statistics.get("draws", 0) + 1
        team_2_statistics["draws"] = team_2_statistics.get("draws", 0) + 1

    # Recalcula a popularidade com base no histórico acumulado
    def calculate_popularity(statistics):
        victories = statistics.get("victories", 0)
        draws = statistics.get("draws", 0)
        defeats = statistics.get("defeats", 0)
        goals = statistics.get("goals", 0)

        matches_played = victories + draws + defeats

        if matches_played == 0:
            return 0

        # Aproveitamento: vitória = 3, empate = 1, derrota = 0
        points = victories * 3 + draws
        max_points = matches_played * 3

        performance = points / max_points

        # Converte aproveitamento para escala de -100 a 100
        popularity = (performance * 200) - 100

        # Bônus por gols marcados
        goals_per_match = goals / matches_played
        goals_bonus = min(15, goals_per_match * 2)

        popularity += goals_bonus

        return round(max(-100, min(100, popularity)))

    team_1_new_popularity = calculate_popularity(team_1_statistics)
    team_2_new_popularity = calculate_popularity(team_2_statistics)

    # Salva estatísticas e popularidade
    db.post_team_data("statistics", team_1, json.dumps(team_1_statistics))
    db.post_team_data("statistics", team_2, json.dumps(team_2_statistics))

    db.post_team_data("popularity", team_1, team_1_new_popularity)
    db.post_team_data("popularity", team_2, team_2_new_popularity)

    stadium_statistics = json.loads(db.get_stadium_data("statistics", stadium_id))
    stadium_statistics["matches"] = stadium_statistics.get("matches", 0) + 1
    stadium_statistics["goals"] = stadium_statistics.get("goals", 0) + goals_1 + goals_2
    stadium_statistics["collected"] = stadium_statistics.get("collected", 0) + profit
    stadium_statistics["visitors"] = stadium_statistics.get("visitors", 0) + tickets_sold
    db.post_stadium_data("statistics", stadium_id, json.dumps(stadium_statistics))

    return {
        "tickets_sold": tickets_sold,
        "revenue": revenue,
        "expenses": expenses,
        "tax": tax_value,
        "profit": profit,
        "team_1_popularity": team_1_new_popularity,
        "team_2_popularity": team_2_new_popularity
    }
