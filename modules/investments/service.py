import json
from pathlib import Path

from core import logging as logger

market = {}
#=======================
BASE_DIR = Path(__file__).resolve().parent
MARKET_FILE = BASE_DIR/"investments.json"

def load_market():
    try:
        with open(MARKET_FILE, "r", encoding="utf-8") as f:
            logger.system(f"{MARKET_FILE} loaded")
            return json.load(f)
    except FileNotFoundError:
        with open(MARKET_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
            logger.system(f"{MARKET_FILE} not found, created!")
        return {}
    
def save_market(data):
    with open(MARKET_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
        logger.system(f"{MARKET_FILE} saved")