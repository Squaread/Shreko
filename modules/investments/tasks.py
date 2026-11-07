from discord.ext import commands, tasks

import random
import math
import yfinance as yf

from modules.investments import service as InvestmentsService

def simulate_value(market, data):
    market_volatility = market["volatility"]      
    item_volatility = data.get("default_volatility") 
    item_value = data.get("value")

    # Combina a volatilidade do mercado com a do ativo
    total_volatility = market_volatility + item_volatility

    # Sorteia uma variação entre -vol e +vol
    variation = random.uniform(-total_volatility, total_volatility)

    # Novo valor
    value = round(item_value * (1 + variation), 4)

    return value

def update_market():
    market = InvestmentsService.market

    tickers = [
        "USDBRL=X",
        "EURBRL=X",
        "GBPBRL=X",
        "ARSBRL=X",
        "RBLX",
    ]

    data = yf.download(
        tickers=tickers,
        period="1d",
        interval="1d",
        group_by="ticker",
        auto_adjust=True,
        progress=False,
    )

    USB_value = round(data["USDBRL=X"]["Close"].iloc[-1], 4)
    if not math.isnan(USB_value):
        market["Dólar americano"]["last_value"] = market["Dólar americano"]["value"]
        market["Dólar americano"]["value"] = USB_value

    EUR_value = round(data["EURBRL=X"]["Close"].iloc[-1], 4)
    if not math.isnan(EUR_value):
        market["Euro"]["last_value"] = market["Euro"]["value"]
        market["Euro"]["value"] = EUR_value

    GBP_value = round(data["GBPBRL=X"]["Close"].iloc[-1], 4)
    if not math.isnan(GBP_value):
        market["Libra esterlina"]["last_value"] = market["Libra esterlina"]["value"]
        market["Libra esterlina"]["value"] = GBP_value

    ARS_value = round(data["ARSBRL=X"]["Close"].iloc[-1], 4)
    if not math.isnan(ARS_value):
        market["Peso argentino"]["last_value"] = market["Peso argentino"]["value"]
        market["Peso argentino"]["value"] = ARS_value

    RBLX_value = round(data["RBLX"]["Close"].iloc[-1], 4)
    if not math.isnan(RBLX_value):
        market["Roblox"]["last_value"] = market["Roblox"]["value"]
        market["Roblox"]["value"] = RBLX_value
    
    for name, data in market.items(): 
        if data.get("type") == "fake": 
            new_value = simulate_value(market["MERCADO"], data)
            market[name]["last_value"] = market[name]["value"]
            market[name]["value"] = new_value

    index_volatility = random.randint(-3, 3) / 10
    new_market_volatility = market["MERCADO"]["volatility"] + index_volatility
    new_market_volatility = max(0.1, min(0.7, new_market_volatility))

    market["MERCADO"]["volatility"] = new_market_volatility

    print("MERCADO DE INVESTIMENTOS ATUALIZADO")
    InvestmentsService.market = market
    InvestmentsService.save_market(market)
    return market
                  

class Market_tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
           self.up_market.start()
    
    @tasks.loop(hours=3)
    async def up_market(self):
            try:
                 update_market()
                 pass
            except Exception as e:
                    print(f"[!] Erro ao atualizar mercado modules.investments.tasks: {e}")

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Tasks investments loaded")
    await bot.add_cog(Market_tasks(bot))