import json
from pathlib import Path

from core.user_data import db

from config import banco_central

economy = {}

#=======================
BASE_DIR = Path(__file__).resolve().parent
ECONOMY_FILE = BASE_DIR/"economy.json"

def load_economy():
    try:
        with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except FileNotFoundError:
        print("[!] File not found. Creating:", ECONOMY_FILE)
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
def save_economy(data):
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#=======================


def get_user_money(user_id: int):
    user_money = db.get_user_data("money", user_id)
    return user_money

def get_user_bank(user_id: int):
    user_bank = db.get_user_data("bank", user_id)
    return user_bank

def get_user_vault(user_id: int):
    user_vault = db.get_user_data("vault", user_id)
    return user_vault

def get_user_vault_tier(user_id: int):
    user_vault_tier = db.get_user_data("vault_tier", user_id)
    return user_vault_tier

def get_user_aura(user_id: int):
    user_aura = db.get_user_data("aura", user_id)
    return user_aura

def get_user_password(user_id: int):
    user_password = db.get_user_data("password", user_id)
    return user_password

def set_user_password(user_id: int, password: str):
    db.post_user_data("password", user_id, password)

def add_user_money(user_id: int, amount: int):
    db.post_user_data("money", user_id, db.get_user_data("money", user_id)+amount)

def add_user_bank(user_id: int, amount: int):
    db.post_user_data("bank", user_id, db.get_user_data("bank", user_id)+amount)

def add_user_vault(user_id: int, amount: int):
    db.post_user_data("vault", user_id, db.get_user_data("vault", user_id)+amount)

def add_user_aura(user_id: int, amount: int):
    db.post_user_data("aura", user_id, db.get_user_data("aura", user_id)+amount)

def money_transaction(user_sender_id: int, user_receiver_id: int, amount: int):
    if user_sender_id == banco_central:
        add_user_bank(user_sender_id, -amount)
    else:
        add_user_money(user_sender_id, -amount)

    if user_receiver_id == banco_central:
        add_user_bank(user_receiver_id, amount)
    else:
        add_user_money(user_receiver_id, amount)

def bank_transaction(user_sender_id: int, user_receiver_id: int, amount: int):
    add_user_bank(user_sender_id, -amount)
    add_user_bank(user_receiver_id, amount)

def aura_transaction(user_sender_id: int, user_receiver_id: int, amount: int):
    add_user_aura(user_sender_id, -amount)
    add_user_aura(user_receiver_id, amount)

def user_deposit_bank(user_id: int, amount: int):
    add_user_money(user_id, -amount)
    add_user_bank(user_id, amount)

def user_withdraw_bank(user_id: int, amount: int):
    add_user_bank(user_id, -amount)
    add_user_money(user_id, amount)

def user_deposit_vault(user_id: int, amount: int):
    add_user_money(user_id, -amount)
    add_user_vault(user_id, amount)

def user_withdraw_vault(user_id: int, amount: int):
    add_user_vault(user_id, -amount)
    add_user_money(user_id, amount)

def upgrade_user_vault_tier(user_id: int, factor: int = 1):
    vault_tier = get_user_vault_tier(user_id)
    db.post_user_data("vault_tier", user_id, vault_tier+factor)