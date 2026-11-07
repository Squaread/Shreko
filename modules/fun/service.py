import json
from pathlib import Path

wordle = {}

#=======================
BASE_DIR = Path(__file__).resolve().parent
WORDLE_FILE = BASE_DIR/"wordle.json"

def load_wordle():
    try:
        with open(WORDLE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", WORDLE_FILE)
        with open(WORDLE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
        return {}
    
def save_wordle(data):
    with open(WORDLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#=======================

def new_wordle(word: str):
    wordle["word"] = word
    wordle["discovered"] = False
    wordle["winner"] = ""
    save_wordle(wordle)

def wordle_winner(user_name: str):
    wordle["discovered"] = True
    wordle["winner"] = user_name
    save_wordle(wordle)