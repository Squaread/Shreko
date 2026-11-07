import discord
from discord.ext import commands
import asyncio

from modules.economy import service as EconomyService
from modules.items import service as ItemsService
from modules.jobs import service as JobsService
from modules.investments import service as InvestmentsService
from modules.fun import service as FunService
#====================
from config import bot_prefix, DISCORD_BOT_TOKEN

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=bot_prefix, intents=intents, help_command=None)

EconomyService.economy = EconomyService.load_economy()
ItemsService.items = ItemsService.load_items()
JobsService.jobs = JobsService.load_jobs()
InvestmentsService.market = InvestmentsService.load_market()
FunService.wordle = FunService.load_wordle()

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

async def load_cogs():
    print("[...] Loading cogs")
    initial_extensions = ['core.error_handling', 'modules.jobs.tasks', 'modules.economy.tasks', 'modules.fun.tasks', 'modules.economy.commands', 'modules.items.commands', 'modules.admin.commands', 'modules.jobs.commands', 'modules.betting.commands', 'modules.investments.commands', 'modules.fun.commands']
    for extension in initial_extensions:
        await bot.load_extension(extension)

async def main():
    await load_cogs()

asyncio.run(main())

bot.run(DISCORD_BOT_TOKEN)