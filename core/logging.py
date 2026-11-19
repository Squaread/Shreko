
import discord
import asyncio
import os
from datetime import datetime
from pathlib import Path
import warnings

from config import LOG_CHANNEL

BASE_DIR = Path(__file__).resolve().parent.parent

LOG_FILE = BASE_DIR/"logs.txt"
MAX_SIZE_MB = 10


async def send_discord(bot, title, description, footer=0, color=discord.Color.blue()):
    if LOG_CHANNEL == 0: return
    channel = bot.get_channel(LOG_CHANNEL)

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"SERVER: {footer}")
    await channel.send(embed=embed)
#-------------------

def _write_log(level: str, content: str):
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    log = f"[{timestamp}] [{level.upper()}] {content}\n"

    max_size = MAX_SIZE_MB * 1024 * 1024
    log_size = len(log.encode("utf-8"))

    if os.path.exists(LOG_FILE):
        if os.path.getsize(LOG_FILE) + log_size > max_size:
            with open(LOG_FILE, "w", encoding="utf-8"):
                pass

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(log)

def read_logs():
    with open(LOG_FILE, "r", encoding="utf-8") as file:
        return file.read()

def action(content: str):
    _write_log("ACTION", content)

def info(content: str):
    print(f"[INFO] {content}")
    _write_log("INFO", content)

def database(content: str):
    _write_log("DATABASE", content)

def system(content: str):
    print(f"[SYSTEM] {content}")
    _write_log("SYSTEM", content)

def admin(content: str):
    _write_log("ADMIN", content)

def error(content: str):
    _write_log("ERROR", content)
    warnings.warn(content, RuntimeWarning)
