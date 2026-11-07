import discord
from discord.ext import commands
import asyncio
import random
import re

from modules.economy import service as EconomyService
from modules.items import service as ItemsService
from modules.jobs import service as JobsService
from modules.investments import service as InvestmentsService
from modules.fun import service as FunService
#====================
from config import BOT_PREFIX, DISCORD_BOT_TOKEN, SERVERS_ID

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)
bot.help_command = commands.MinimalHelpCommand(sort_commands=True)

EconomyService.economy = EconomyService.load_economy()
ItemsService.items = ItemsService.load_items()
JobsService.jobs = JobsService.load_jobs()
InvestmentsService.market = InvestmentsService.load_market()
FunService.wordle = FunService.load_wordle()

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user: return
    if message.guild is None: return
    if not message.guild.id in SERVERS_ID: return

    memory_commands = ["tigrinho", "pix", "sacar", "sac", "depositar", "dep", "trab", "saldo"]
    aura_words = ["67", "siriboy", "skibidi", "cityboy", "resenh", "borabill", "xuxa", "sixseven", "sus", "clube", "slk", "seloko", "42", "41", "amogus", "bigode", "sahur", "epstein", "orelha", "69", "tung", "sigma", "chad", "patapim", "ez", "bandido", "tuff", "gul", "based", "baseado", "yara", "tiki"]
    if any(re.search(rf"\b{word}\b", message.content.lower()) for word in memory_commands):
        if ".." in message.content: return await message.channel.send("kkkkkkkkkkkkkkkkkk olha o idiota usando prefixo do dreamteam")
    
    if not ";" in message.content: # Caso a mensagem nao tenha o prefixo do bot (significando q n se trata de um comando)
     if str(f"<@"+str(bot.user.id)+">") in message.content:
        input = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not input or len(input) <= 1: return await message.channel.send("Q")

     if message.author.bot: return
     msg = message.content.lower().replace(" ", "")
     if any(word in msg for word in aura_words) or any(p.endswith("x") for p in msg.split()):
            chance = random.randint(1, 2)
            if chance == 1:
                author_id = message.author.id
                EconomyService.add_user_aura(author_id, 1) #db.post_user_data("xp", author_id, db.get_user_data("xp", author_id)+1)
                return
            else: return

    await bot.process_commands(message)

async def load_cogs():
    print("[...] Loading cogs")
    initial_extensions = ['core.error_handling', 'modules.jobs.tasks', 'modules.economy.tasks', 'modules.fun.tasks', 'modules.economy.commands', 'modules.items.commands', 'modules.admin.commands', 'modules.jobs.commands', 'modules.betting.commands', 'modules.investments.commands', 'modules.fun.commands']
    for extension in initial_extensions:
        await bot.load_extension(extension)

async def main():
    await load_cogs()

asyncio.run(main())

bot.run(DISCORD_BOT_TOKEN)