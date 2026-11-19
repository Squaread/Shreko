import json
from pathlib import Path
import random

from core import logging as logger

from utils.helpers import count_vowels, count_consonants

wordle = {}

#=======================
BASE_DIR = Path(__file__).resolve().parent
WORDLE_FILE = BASE_DIR/"wordle.json"

def load_wordle():
    try:
        with open(WORDLE_FILE, "r", encoding="utf-8") as f:
            logger.system(f"{WORDLE_FILE} loaded")
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", WORDLE_FILE)
        with open(WORDLE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
            logger.system(f"{WORDLE_FILE} not found, created!")
        return {}
    
def save_wordle(data):
    with open(WORDLE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        logger.system(f"{WORDLE_FILE} saved")
#=======================

def new_wordle(word: str, author=None):
    hit_chance = random.randint(1, 5)
    if hit_chance == 1:
        h = count_vowels(word)
        hint = f"A palavra tem {h} vogais!"
    elif hit_chance == 2:
        h = count_consonants(word)
        hint = f"A palavra tem {h} consoantes!"
    elif hit_chance == 3 and (author and hasattr(author, 'display_name')):
        hint = f"A palavra foi dita por {author.display_name}!"
    elif hit_chance == 4:
        h = len(word)
        hint = f"A palavra tem {h} letras!"
    else:
        hint = "Nenhuma kkkkkkkkk"

    wordle["word"] = word
    wordle["hint"] = hint
    wordle["discovered"] = False
    wordle["winner"] = ""
    save_wordle(wordle)
    logger.info(f"New wordle: {wordle}")

def wordle_winner(user_name: str):
    wordle["discovered"] = True
    wordle["winner"] = user_name
    save_wordle(wordle)
    logger.info(f"Wordle discovered by: {user_name}")