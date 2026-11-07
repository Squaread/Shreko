import json
from pathlib import Path

#=======================
BASE_DIR = Path(__file__).resolve().parent
BETTING_FILE = BASE_DIR/"betting.json"

def load_betting():
    try:
        with open(BETTING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", BETTING_FILE)
        with open(BETTING_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}

def save_betting(data):
    with open(BETTING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)