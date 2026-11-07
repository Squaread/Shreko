from discord.ext import commands, tasks
from datetime import time
from zoneinfo import ZoneInfo

from modules.economy import service as EconomyService

from core.user_data import db

from core.logger import logger

from config import banco_central, money_icon

BRASILIA = ZoneInfo("America/Sao_Paulo")

# Imposto sobre saldo excedente
def ImpostoSobreSaldo():
    data = db.get_all_data()
    data = [row for row in data if row[0] != banco_central]
    data = sorted(data, key=lambda x: x[1] + x[2] + x[5], reverse=True)
    i = 0
    total_collected = 0

    economy = EconomyService.economy

    tax_saldo = economy.get("tax_saldo")
    tax_minsaldo = economy.get("tax_minsaldo")
    tax_saldofactor = economy.get("tax_saldofactor")
    tax_saldomax = economy.get("tax_saldomax")

    if tax_saldo <= 0:
        return i, int(total_collected)

    for pos, row in enumerate(data[:10], start=1):
        user_id = row[0]
        saldo = row[5]

        if saldo <= tax_minsaldo:
            continue

        excedente = saldo - tax_minsaldo
        restante = excedente
        imposto = 0
        faixa = 0

        while restante > 0:
            valor = min(restante, tax_saldofactor)
            faixa += 1
            taxa = min(faixa * tax_saldo, tax_saldomax)

            imposto += valor * taxa
            restante -= valor

        total_collected+=imposto
        saldo = int(saldo - imposto)

        db.post_user_data("bank", user_id, saldo)
        EconomyService.add_user_bank(banco_central, imposto)
        i+=1
    return i, int(total_collected)

class Economy_tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.cycle.start()

    @tasks.loop(time=time(hour=0, minute=0, tzinfo=BRASILIA))
    async def cycle(self):
        try:
            i_PSE, total_collected = ImpostoSobreSaldo()
            await logger(self.bot, "Cycle concluido", f"Finalizado 24h\nPSE: `{i_PSE}` `{money_icon}{total_collected}`")

        except Exception as e:
                print(f"Erro cycle: {e}")

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Tasks economy loaded")
    await bot.add_cog(Economy_tasks(bot))