import discord
from discord.ext import commands
import asyncio
import random
import re

from core import logging as logger
from core import user_data
from core.user_data import db

from modules.economy import service as EconomyService
from modules.items import service as ItemsService
from modules.jobs import service as JobsService
from modules.investments import service as InvestmentsService
from modules.fun import service as FunService
#====================
from config import BOT_PREFIX, DISCORD_BOT_TOKEN, SERVERS_ID, ON_MESSAGE_BYPASS_EXCEPTIONS_ID

logger.system("--- BOT STARTUP ---")

intents = discord.Intents.all()

bot = commands.Bot(command_prefix=BOT_PREFIX, intents=intents)
bot.help_command = commands.MinimalHelpCommand(sort_commands=True)

EconomyService.economy = EconomyService.load_economy()
ItemsService.items = ItemsService.load_items()
JobsService.jobs = JobsService.load_jobs()
InvestmentsService.market = InvestmentsService.load_market()
FunService.wordle = FunService.load_wordle()
user_data.blacklist.extend(user[0] for user in db.filter_users("blacklist", 1))

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.event
async def on_guild_join(guild: discord.Guild):
    logger.info(f"on_guild_join -> bot adicionado a um servidor: {guild.name}/{guild.id}")
    await logger.send_discord(bot, title="on_guild_join", description=f"Fui adicionado a um novo servidor: {guild.name}/{guild.id}")

@bot.event
async def on_guild_remove(guild: discord.Guild):
    logger.info(f"on_guild_remove -> bot removido de um servidor: {guild.name}/{guild.id}")

@bot.event
async def on_message(message):
    if not message.author.id in ON_MESSAGE_BYPASS_EXCEPTIONS_ID: 
        if message.author.bot: return
        if message.guild is None: return
        if not message.guild.id in SERVERS_ID: return
    if message.author.id in user_data.blacklist: return

    memory_commands = ["tigrinho", "pix", "sacar", "sac", "depositar", "dep", "trab", "saldo"]
    aura_words = ["67", "siriboy", "skibidi", "cityboy", "resenh", "borabill", "xuxa", "sixseven", "sus", "clube", "slk", "seloko", "42", "41", "amogus", "bigode", "sahur", "epstein", "orelha", "69", "tung", "sigma", "chad", "patapim", "ez", "bandido", "tuff", "gul", "based", "baseado", "yara", "tiki"]
    if any(re.search(rf"\b{word}\b", message.content.lower()) for word in memory_commands):
        if ".." in message.content: return await message.channel.send("kkkkkkkkkkkkkkkkkk olha o idiota usando prefixo do dreamteam")
    
    if not ";" in message.content: # Caso a mensagem nao tenha o prefixo do bot (significando q n se trata de um comando)
     if str(f"<@"+str(bot.user.id)+">") in message.content:
        input = message.content.replace(f"<@{bot.user.id}>", "").strip()
        if not input or len(input) <= 1: return await message.channel.send("Q")

     msg = message.content.lower().replace(" ", "")
     if any(word in msg for word in aura_words) or any(p.endswith("x") for p in msg.split()):
            chance = random.randint(1, 2)
            if chance == 1:
                author_id = message.author.id
                EconomyService.add_user_aura(author_id, 1) #db.post_user_data("xp", author_id, db.get_user_data("xp", author_id)+1)
                return
            else: return

    if message.author.bot:
        ctx = await bot.get_context(message)
        if ctx.valid:
            await bot.invoke(ctx)
    else:
        await bot.process_commands(message)

async def load_cogs():
    print("[...] Loading cogs")
    initial_extensions = ['core.error_handling', 'modules.jobs.tasks', 'modules.economy.tasks', 'modules.fun.tasks', 'modules.economy.commands', 'modules.items.commands', 'modules.admin.commands', 'modules.jobs.commands', 'modules.betting.commands', 'modules.investments.commands', 'modules.fun.commands', 'modules.admin.roles_repo']
    for extension in initial_extensions:
        await bot.load_extension(extension)

async def main():
    await load_cogs()

asyncio.run(main())

bot.run(DISCORD_BOT_TOKEN)
