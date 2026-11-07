import json
from pathlib import Path

#=======================
BASE_DIR = Path(__file__).resolve().parent
ADMIN_FILE = BASE_DIR/"admins.json"

def load_admins():
    try:
        with open(ADMIN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", ADMIN_FILE)
        with open(ADMIN_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
def save_admins(data):
    with open(ADMIN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#=======================