import time
import json
from pathlib import Path

from core.errors import *

Commands = {
    "trabalhar": 7200, 
    "daily": 43200, 
    "hackear": 15,
    "roubar": 1800,
    "pegar": 120,
    "guardar": 120,
    "enviarcurriculo": 7200 
}

#-------------------------------
BASE_DIR = Path(__file__).resolve().parent
COOLDOWN_FILE = BASE_DIR/"cooldown.json"

def load_cooldown():
    try:
        with open(COOLDOWN_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("[!] File not found. Creating:", COOLDOWN_FILE)
        with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
            return {}
        
def save_cooldown(data):
    with open(COOLDOWN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
#-------------------------------

async def check_and_apply_cooldown(user_id: str | int, command: str) -> tuple[bool, int]:
    user_id = str(user_id)
    
    if command not in Commands:
        return True, 0

    cooldowns = load_cooldown() or {}
    now = time.time()

    if user_id not in cooldowns:
        cooldowns[user_id] = {}

    # Timestamp 
    expire_time = cooldowns[user_id].get(command, 0)

    # Se ainda ta em cooldown
    if now < expire_time:
        time_remaining = int(expire_time - now)
        raise CommandOnCooldown(time_remaining)
       #return False, time_remaining

    # Se ja expirou/primeiro uso e definir novo cooldown
    cooldowns[user_id][command] = now + Commands[command]
    
    # Salvar no json
    save_cooldown(cooldowns)
    
    return True, 0