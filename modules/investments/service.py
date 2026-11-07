import json
from pathlib import Path

market = {}
#=======================
BASE_DIR = Path(__file__).resolve().parent
MARKET_FILE = BASE_DIR/"investments.json"

def load_market():
    try:
        with open(MARKET_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", MARKET_FILE)
        with open(MARKET_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
def save_market(data):
    with open(MARKET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)