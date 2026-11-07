from discord.ext import commands, tasks
import random
import unicodedata
import re
from datetime import time
from zoneinfo import ZoneInfo

from core.logger import logger

from config import GENERAL_CHANNEL

from modules.fun import service as FunService

BRASILIA = ZoneInfo("America/Sao_Paulo")

async def wordle_choose_word(bot):
    channel = bot.get_channel(GENERAL_CHANNEL)

    if channel is None:
        channel = await bot.fetch_channel(GENERAL_CHANNEL)

    valid_words = []

    async for message in channel.history(limit=1000):
        if message.author.bot:
            continue

        # Separar as palavras da mensagem
        words = message.content.split()

        for word in words:
            # Ignorar acentuação
            if unicodedata.normalize("NFC", word) != word:
                pass

            # Remover acentos para verificar se existem
            normalized = unicodedata.normalize("NFD", word)
            without_accent = "".join(
                c for c in normalized
                if unicodedata.category(c) != "Mn"
            )

            # Só aceitar letras A-Z
            if not re.fullmatch(r"[a-zA-Z]+", without_accent):
                continue

            # Entre 3 e 10 letras
            if not 3 <= len(without_accent) <= 10:
                continue

            # Ignorar palavras acentuadas
            if word.lower() != without_accent.lower():
                continue

            valid_words.append((without_accent.lower(), message.author))

    if not valid_words: return None
    return random.choice(valid_words)

class Fun_tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
           self.update_wordle.start()
    
    @tasks.loop(time=time(hour=12, minute=0, tzinfo=BRASILIA))
    async def update_wordle(self):
            try:
                 wordle_word, wordle_author = await wordle_choose_word(self.bot)
                 FunService.new_wordle(wordle_word, wordle_author)
                 await logger(self.bot, "Wordle", "Wordle atualizado")
            except Exception as e:
                    print(f"[!] Erro ao atualizar wordle modules.fun.tasks: {e}")

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Tasks fun loaded")
    await bot.add_cog(Fun_tasks(bot))