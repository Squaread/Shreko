import json
from pathlib import Path

#=======================
BASE_DIR = Path(__file__).resolve().parent
ADMIN_FILE = BASE_DIR/"admins.json"

def load_admins(int_converter: bool=True):
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if int_converter: return {role: [int(user_id) for user_id in user_ids] for role, user_ids in data.items()}
            else: return data
    except FileNotFoundError:
        print("[!] File not found. Creating:", ADMIN_FILE)
        with open(ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
def save_admins(data):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#=======================