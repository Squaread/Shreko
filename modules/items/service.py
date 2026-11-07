import json
from pathlib import Path

from core.user_data import db

items = {}

#=======================
BASE_DIR = Path(__file__).resolve().parent
ITEMS_FILE = BASE_DIR/"items.json"

def load_items():
    try:
        with open(ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", ITEMS_FILE)
        with open(ITEMS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
def save_items(data):
    with open(ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#=======================

def get_user_equipment(user_id: int):
    user_equipment = db.get_user_data("equipment", user_id)
    return user_equipment

def get_user_inventory(user_id: int):
    user_inventory = db.get_user_data("inventory", user_id)
    if not user_inventory: user_inventory = str('{}')
    return json.loads(user_inventory)

def set_user_inventory(user_id: int, inventory: dict):
    db.post_user_data("inventory", user_id, inventory)

def add_user_inventory(user_id: int, item_name: str, quant: int = 1):
    user_inventory = get_user_inventory(user_id)

    if item_name in user_inventory: user_inventory[item_name] += quant
    else: user_inventory[item_name] = quant
    if user_inventory[item_name] <= 0: del user_inventory[item_name]

    set_user_inventory(user_id, user_inventory)

def transfer_item(user_giver_id: int, user_receiver_id: int, item_name: str, quant: int):
    if user_giver_id == user_receiver_id or quant <= 0: return False

    giver_inventory = get_user_inventory(user_giver_id)

    if item_name not in giver_inventory: return False

    if giver_inventory[item_name] < quant: return False

    receiver_inventory = get_user_inventory(user_receiver_id)

    giver_inventory[item_name] -= quant

    if giver_inventory[item_name] <= 0:
        del giver_inventory[item_name]

    receiver_inventory[item_name] = (receiver_inventory.get(item_name, 0) + quant)

    set_user_inventory(user_giver_id, giver_inventory)
    set_user_inventory(user_receiver_id, receiver_inventory)

    return True

def user_equip_item(user_id, item_name):
    user_equipment = get_user_equipment(user_id)
    user_inventory = get_user_inventory(user_id)

    if user_equipment:
        if user_equipment in user_inventory: user_inventory[user_equipment] += 1
        else: user_inventory[user_equipment] = 1

    user_inventory[item_name] -= 1
    if user_inventory[item_name] <= 0: del user_inventory[item_name]
    
    set_user_inventory(user_id, user_inventory)
    db.post_user_data("equipment", user_id, item_name)

def user_unequip_item(user_id):
    user_equipment = get_user_equipment(user_id)
    user_inventory = get_user_inventory(user_id)

    if user_equipment:
        if user_equipment in user_inventory: user_inventory[user_equipment] += 1
        else: user_inventory[user_equipment] = 1
    
        set_user_inventory(user_id, user_inventory)
        db.post_user_data("equipment", user_id, None)