import discord
from discord.ext import commands
import random
import asyncio

from modules.economy import service as EconomyService
from modules.items import service as ItemsService
from modules.jobs import service as JobsService

from core.logger import logger
from core.cooldown import check_and_apply_cooldown
from core.errors import *
from core.user_data import db

from utils.embeds import *
from utils.helpers import interpret_input_value, encrypt
from utils import taxes
from utils.combat import combat

from config import BOT_PREFIX, BANCO_CENTRAL, MONEY_ICON, AURA_ICON, VAULT_ICON, VAULT_DEFAULT_LIMIT

class economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
#------------------------------------------
    @commands.hybrid_command(name="conta", aliases=["carteira", "money", "cofre", "saldo", "perfil"])
    async def conta(self, ctx, user: discord.Member | None):
        equipment_icon = ""

        if not user: user = ctx.author
        user_id = user.id

        if user_id == BANCO_CENTRAL: 
            bank = EconomyService.get_user_bank(user_id)

            bank_embed = base_embed_template(user,
                title="Banco Central",
                description=f"> 🏦 `{MONEY_ICON}{bank}`",
                color=0x7289da)
        
            return await ctx.send(embed=bank_embed)
        
        if user.bot: return

        user_money = EconomyService.get_user_money(user_id)
        user_bank = EconomyService.get_user_bank(user_id)
        user_vault = EconomyService.get_user_vault(user_id)
        user_aura = EconomyService.get_user_aura(user_id)
        user_equipment = ItemsService.get_user_equipment(user_id)
        user_job = JobsService.get_user_job(user_id)

        if user_equipment:
            items = ItemsService.items
            if user_equipment in items: equipment_icon = f"\n{items[user_equipment]['icon']}"

        if not user_job: user_job = "Vagabundo"
        else: 
            user_job = f"{user_job['company']}\n"+user_job['job']

        wallet_embed = base_embed_template(user, 
            title="Conta", 
            description=f"> 💼 `{MONEY_ICON}{user_money}`\n> 🏦 `{MONEY_ICON}{user_bank}`\n{VAULT_ICON} `{MONEY_ICON}{user_vault}`{equipment_icon}\n`{user_job} / {AURA_ICON}{user_aura}`",
            color=0x7289da)

        await ctx.send(embed=wallet_embed)

#------------------------------------------
    @commands.hybrid_command(name="daily", description="Saque seu bolsa família")
    async def daily(self, ctx):
        user = ctx.author
        user_id = user.id

        await check_and_apply_cooldown(user_id, ctx.command.name)

        economy = EconomyService.economy

        income = int(economy.get("money_assistance_value")*(1+random.uniform(-economy.get("money_assistance_variance"), economy.get("money_assistance_variance"))))
        user_money = EconomyService.get_user_money(user_id)
        user_bank = EconomyService.get_user_bank(user_id)

        if user_money+user_bank >= economy.get("money_assistance_maxmoney"):
            return await ctx.reply("Você não tem mais direito ao bolsa família vagabundo")

        banco_central_balance = EconomyService.get_user_bank(BANCO_CENTRAL)
        if banco_central_balance < income:
            return await ctx.reply("O Banco Central não consegue pagar...")
        
        EconomyService.add_user_bank(BANCO_CENTRAL, -income)
        EconomyService.add_user_money(user_id, income)

        bolsa_familia = base_embed_template(user, 
            title="Bolsa Família", 
            description=f"{user.mention} sacou `{MONEY_ICON}{income}`",
            color=0x3498db)

        await ctx.send(embed=bolsa_familia)
        await logger(self.bot, "daily", f"`{user.name}/{user_id}` pegou `{MONEY_ICON}{income}`", f"{ctx.guild.name}/{ctx.guild.id}", 0xcee800)

#------------------------------------------
    @commands.hybrid_command(name="tigrinho", description="Aposte dinheiro, faça ;tigrinho pra ver as chances")
    @commands.cooldown(3, 5, commands.BucketType.user)
    async def tigrinho(self, ctx, amount : str = None):
        if not amount : return await ctx.send(f"`{BOT_PREFIX}tigrinho <amount>`\n**Chances**: `20% loss total`, `40% 0.5x`, `20% 1.5x`, `15% 2x`, `5% 3x`")
        amount = interpret_input_value(amount)

        user = ctx.author
        user_id = user.id

        user_money = EconomyService.get_user_money(user_id)

        if amount > user_money: return await ctx.send("tu nem tem esse valor noob")
        if amount < 2: return await ctx.send(f"Tá duro? Valor mínimo: `{MONEY_ICON}2`")
        EconomyService.add_user_money(user_id, -amount)

        chance = random.randint(1, 100)

        if chance <= 20: # 20% perder tudo
            multiplier = 0
            text = "**MEU DEUS SOBROU NADA**"
            color = 0xe74c3c
            image = "https://media.discordapp.net/attachments/1021220802357629059/1514653446886920262/671c77f75f2df.png"
        elif chance <= 60: # 40% perder metade
            multiplier = 0.5
            text = "**SUPER PERDA**"
            color = 0xa84300
            image = "https://media.discordapp.net/attachments/1021220802357629059/1514653446886920262/671c77f75f2df.png"
        elif chance <= 80: # 20% ganhar 1.5x
            multiplier = 1.5
            text = "**SUPER GANHO**"
            color = 0x2ecc71
            image = "https://media.discordapp.net/attachments/1021220802357629059/1514654042259980350/image.png"
        elif chance <= 95: # 15% ganhar 2x
            multiplier = 2
            text = "**MEGA GANHO**"
            color = 0x2ecc71
            image = "https://media.discordapp.net/attachments/1021220802357629059/1514654042259980350/image.png"
        elif chance <= 100: # 5% ganhar 3x
            multiplier = 3
            text = "**ULTRA GANHO**"
            color = 0xf1c40f
            image = "https://media.discordapp.net/attachments/1021220802357629059/1514654042259980350/image.png"

        income = round(amount * multiplier)

        tigrinho_embed = thumb_embed_template(user, 
            title="Tigrinho", 
            description="Processando...", 
            thumbnail="https://media.discordapp.net/attachments/1021216019328552971/1514657406368485446/maxresdefault.png", 
            color=0xe67e22)
        
        msg = await ctx.send(embed=tigrinho_embed)
        await asyncio.sleep(5)

        tigrinho_embed = thumb_embed_template(user,
            title="Tigrinho",
            description=f"{text}\n`{MONEY_ICON}{amount} * {multiplier}x` = `{MONEY_ICON}{income}`",
            thumbnail=image,
            color=color)        

        EconomyService.add_user_money(user_id, income)
  
        if income < amount: # USUARIO PERDEU
            EconomyService.add_user_bank(BANCO_CENTRAL, amount-income)
        else: # USUARIO GANHOU
            EconomyService.add_user_bank(BANCO_CENTRAL, -income)
        await msg.edit(embed=tigrinho_embed)
        await logger(self.bot, "tigrinho", f"`{user.name}/{user_id}` tigrinhou `{MONEY_ICON}{amount} * {multiplier}x` = `{MONEY_ICON}{income}`", f"{ctx.guild.name}/{ctx.guild.id}", 0xcee800)

#------------------------------------------
    @commands.hybrid_command(name="pix", description="Mande dinheiro para alguém")
    @commands.cooldown(5, 2, commands.BucketType.user)
    async def pix(self, ctx, receiver: discord.Member, amount):
        if not receiver or not amount: return await ctx.send(f"`{BOT_PREFIX}pix <@member> <amount>`")
        amount = interpret_input_value(amount)

        author = ctx.author
        author_id = author.id
        
        if (receiver.id == author_id or receiver.bot) and receiver.id != BANCO_CENTRAL: return await ctx.send(f"noob")

        author_money = EconomyService.get_user_money(author_id)
        if amount > author_money: return await ctx.send("tu nem tem esse valor noob")
        if amount < 1: return await ctx.send("noob")
    
        tax, tax_msg = taxes.pix_tax(author_id, receiver.id, amount)

        EconomyService.money_transaction(author_id, receiver.id, amount)

        pix_embed = thumb_embed_template(author, 
            title="Transfência Pix", 
            description=f"{author.display_name} enviou `{MONEY_ICON}{amount}` para {receiver.display_name}{tax_msg}", 
            thumbnail="https://media.discordapp.net/attachments/1021216019328552971/1514664708613865492/marca-pix-1-.png",
            color=0x2d9fc3)

        await ctx.send(embed=pix_embed)
        await logger(self.bot, "pix", f"`{author.name}/{author_id}` fez pix de `{MONEY_ICON}{amount}` para `{receiver.name}/{receiver.id}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x00ffe0)

#------------------------------------------
    @commands.hybrid_command(name="depositar", aliases=["dep"], description="Deposite dinheiro no banco")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def depositar(self, ctx, amount):
        user_id = ctx.author.id
        user_money = EconomyService.get_user_money(user_id)

        amount = interpret_input_value(amount)

        if isinstance(amount, int):
            if amount <= 0: return
            if amount > user_money: return await ctx.reply("voce nem tem isso noob")
        else:
            if isinstance(amount, str):
                if amount.lower() == "all": amount = user_money
                if user_money <=0: return await ctx.reply("kkkkkkkkkkk nem tem dinheiro pra depositar")
            else: return

        user_password = EconomyService.get_user_password(user_id)
        if not user_password: return await ctx.reply("Defina a senha da sua conta bancaria `/definirsenha <password>`")

        tax, tax_msg = taxes.dep_tax(user_id, amount) # Verificar e aplicar imposto

        EconomyService.user_deposit_bank(user_id, amount)
        await ctx.reply(f"Você depositou `{MONEY_ICON}{amount-tax}` no banco{tax_msg}", mention_author=False)

#------------------------------------------
    @commands.hybrid_command(name="sacar", aliases=["sac"], description="Saque dinheiro do banco")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def sacar(self, ctx, amount):
        user_id = ctx.author.id
        user_bank = EconomyService.get_user_bank(user_id)

        amount = interpret_input_value(amount)
        if isinstance(amount, int):
            if amount <= 0: return
            if amount > user_bank: return await ctx.reply("voce nem tem isso noob")
        else:
            if isinstance(amount, str): 
                if amount.lower() == "all": amount = user_bank
                if user_bank <=0: return await ctx.reply("kkkkkkkkkkk nem tem dinheiro pra sacar")
            else: return

        EconomyService.user_withdraw_bank(user_id, amount)
       
        await ctx.reply(f"Você sacou `{MONEY_ICON}{amount}` do banco", mention_author=False)

#------------------------------------------
    @commands.hybrid_command(name="guardar", aliases=["gua"], description="Guarde dinheiro no cofre de forma segura")
    async def guardar(self, ctx, amount):
        user_id = ctx.author.id

        await check_and_apply_cooldown(user_id, ctx.command.name)

        user_money = EconomyService.get_user_money(user_id)

        amount = interpret_input_value(amount)
        if isinstance(amount, int):
            if amount <= 0: return
            if amount > user_money: return await ctx.reply("voce nem tem isso noob")
        else:
            if isinstance(amount, str):
                if amount.lower() == "all": amount = user_money
                if user_money <=0: return await ctx.reply("kkkkkkkkkkk nem tem dinheiro pra guardar")
            else: return
    
        user_vault = EconomyService.get_user_vault(user_id)
        vault_tier = EconomyService.get_user_vault_tier(user_id)
  
        vault_limit = round(VAULT_DEFAULT_LIMIT*(2 ** vault_tier))

        if user_vault+amount > vault_limit: amount = vault_limit - user_vault
        if amount <= 0: return await ctx.reply("Seu cofre está cheio")

        EconomyService.user_deposit_vault(user_id, amount)

        await ctx.reply(f"Você guardou `{MONEY_ICON}{amount}` no cofre", mention_author=False)

#------------------------------------------
    @commands.hybrid_command(name="pegar", aliases=["peg"], description="Pegue dinheiro do cofre")
    async def pegar(self, ctx, amount):
        user_id = ctx.author.id

        await check_and_apply_cooldown(user_id, ctx.command.name)
        
        user_vault = EconomyService.get_user_vault(user_id)

        amount = interpret_input_value(amount)
        if isinstance(amount, int):
            if amount <= 0: return
            if amount > user_vault: return await ctx.reply("voce nem tem isso noob")
        else:
            if isinstance(amount, str):
                if amount.lower() == "all": amount = user_vault
                if user_vault <=0: return await ctx.reply("kkkkkkkkkkk nem tem dinheiro pra pegar")
            else: return
        
        EconomyService.user_withdraw_vault(user_id, amount)

        await ctx.reply(f"Você pegou `{MONEY_ICON}{amount}` do cofre", mention_author=False)


#------------------------------------------
    @commands.hybrid_command(name="definirsenha", description="Defina a senha do seu banco, não conte a ninguém!")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def definirsenha(self, ctx, password: str):
        user_id = ctx.author.id

        if not ctx.interaction: return await ctx.reply("Utilize slash para esse comando `/definirsenha`")
        if not password.isascii() or not password.isalnum(): return await ctx.send("Sua senha deve conter apenas caracteres alfanuméricos", ephemeral=True)
        if len(password) > 10 or len(password) < 5: return await ctx.send("Sua senha tem que ter entre 5 a 10 caracteres", ephemeral=True)

        password_shas256 = encrypt(password)
        EconomyService.set_user_password(user_id, password_shas256)
        await ctx.send("Senha definida", ephemeral=True)

#------------------------------------------
    @commands.hybrid_command(name="roubar", aliases=["assaltar", "rob"], description="Assalte alguém")
    async def roubar(self, ctx, vitima: discord.Member):
        author = ctx.author
        author_id = author.id

        member = vitima
        user_id = member.id
        if member.bot or author_id == user_id: return await ctx.reply("?")

        await check_and_apply_cooldown(author_id, ctx.command.name)

        economy = EconomyService.economy

        items = ItemsService.items
        equipment_user1 = items.get(ItemsService.get_user_equipment(author_id))
        equipment_user2 = items.get(ItemsService.get_user_equipment(user_id))
        
        user1 = {"hp": 100,
                    "user_name": author.name,
                    "user_id": author_id,
                    "equipment": equipment_user1,
                    "state": [],
                    "damage_dealt": 0}
        user2 = {"hp": 100,
                    "user_name": member.name,
                    "user_id": member.id,
                    "equipment": equipment_user2,
                    "state": [],
                    "damage_dealt": 0}

        #winner, p_user1, p_user2, eq_user1, eq_user2 = duel_simulator(author_id, user_id) --> FUNÇÃO ANTIGA NAO MAIS EXISTENTE
        while True: # SIMULAÇÃO DOS ROUNDS DA LUTA ATÉ ALGUÉM MORRER
            user1, user2, m = combat(user1, user2)
            if user1['hp'] <= 0 or user2['hp'] <= 0: break

        if user1['hp'] > user2['hp']: winner = user1['user_id']
        else: winner = user2['user_id']
        p_user1 = user1["damage_dealt"]
        p_user2 = user2["damage_dealt"]
        eq_user1 = user1["equipment"]
        eq_user2 = user2["equipment"]

        aura_coefficient = economy.get("aura_coefficient")

        aura_msg = ""
        aura = 0
        if winner == author_id: # Caso o ladrao vença
            user_money = EconomyService.get_user_money(user_id)
            ratio = p_user1 / (p_user1 + p_user2)
            steal_percent = 0.10 + (ratio * 0.40)
            money_seized = round(user_money*steal_percent)

            if user_money <= 200 and user_money > 0: money_seized=user_money
            money_text = f"e levou `{MONEY_ICON}{money_seized}`"

            if money_seized <= 0: money_text = f"mas não achou nada na carteira kkkkkkkkkkkk `{MONEY_ICON}{money_seized}`"
            else: 
                aura = round((money_seized/200)*10*aura_coefficient)
                if aura < 2: aura = 0

                if money_seized <= 10: money_text = f"e levou uma merrequinha `{MONEY_ICON}{money_seized}`"
                if money_seized >= user_money: money_text = f"e levou TODO O DINHEIRO DELE `{MONEY_ICON}{money_seized}`"
                
                if aura > 0: aura_msg = f"além de `{AURA_ICON}{aura}` aura por moggar esse betinha haha ele perdeu `{AURA_ICON}-{round(aura*0.8)}`"

                EconomyService.money_transaction(user_id, author_id, money_seized)
                EconomyService.add_user_aura(author_id, aura)
                EconomyService.add_user_aura(user_id, -round(aura*0.8))

            await ctx.reply(f"{member.display_name} tentou resistir ({eq_user1['icon']}{p_user1}x{eq_user2['icon']}{p_user2}) você se saiu bem {money_text} {aura_msg}")
            await logger(self.bot, "roubar", f"`{author.name}/{author_id}` `{AURA_ICON}+{aura}` roubou `{MONEY_ICON}{money_seized}` de `{vitima.name}/{user_id}` `{AURA_ICON}-{round(aura*0.8)}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x009152)
        else: # Caso a vitima vença
            fine = random.randint(100, 800)
            aura = (p_user2-p_user1)*aura_coefficient

            EconomyService.money_transaction(author_id, BANCO_CENTRAL) # Ladrao levando multa e multa indo pro banco central
            EconomyService.aura_transaction(author_id, user_id, aura) # Ladrao moggado teve uma parte de sua aura absolvida pela vitima

            #---
            await ctx.reply(f"{member.display_name} resistiu ({eq_user1['icon']}{p_user1}x{eq_user2['icon']}{p_user2}) e você levou uma surra gastando `{MONEY_ICON}-{fine}` no hospital kkkkkkk foi moggado perdeu `{AURA_ICON}-{aura}` enquanto ele ganhou aura por te dar uma lição!")
            await logger(self.bot, "roubar", f"`{author.name}/{author_id}` `{AURA_ICON}-{aura}` falhou em roubar `{vitima.name}/{user_id}` `{AURA_ICON}+{aura}` gastando `{MONEY_ICON}-{fine}`", f"{ctx.guild.name}/{ctx.guild.id}", 0xb20006)

#------------------------------------------
    @commands.hybrid_command(name="hackear", description="Invada a conta de um otário e pegue todo seu dinheiro!")
    async def hackear(self, ctx, usuario: discord.User, password: str):
        author = ctx.author
        author_id = author.id

        await check_and_apply_cooldown(author_id, ctx.command.name)
        
        victim_id = usuario.id

        if author_id == victim_id or usuario.bot: return await ctx.reply("noob")

        victim_password = EconomyService.get_user_password(victim_id)
        guess_password = encrypt(password)
        terminal = f"{author.display_name}@{author.name}: ~$ "
        terminal = terminal + f"clonarcartao.py --user {usuario.name} --password {password}"
        msg = await ctx.reply(f"`{terminal}`")
        await asyncio.sleep(5)
        if victim_password != guess_password:
            return await msg.edit(content=f"Usuário ou senha incorretos.")
        else:
            victim_bank = db.get_user_data("bank", victim_id)
            message = ""
            if victim_bank > 0:
                EconomyService.bank_transaction(victim_id, author_id, victim_bank)

                message = f"Você conseguiu sacar todo o dinheiro `{MONEY_ICON}{victim_bank}` de {usuario.mention} que botou `{password}` como senha KKKKKKKKKKKKKKKKKKKKK"
            else: 
                message = f"Você conseguiu acessar a conta de `{usuario.mention}` `{password}` mas encontrou nem 1 real lá..."
            await logger(self.bot, "hackear", f"`{author.name}/{author_id}` pegou `{MONEY_ICON}{victim_bank}` de `{usuario.name}/{victim_id}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x000000)
            await msg.edit(content=message)

#------------------------------------------
    @commands.hybrid_command(name="leaderboard", aliases=["rank"], description="Veja os mais ricos")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def leaderboard(self, ctx):
        data = db.get_all_data()
        author = ctx.author

        msg = ""

    # Montar o rank desconsiderando o banco central
        data = [row for row in data if row[0] != BANCO_CENTRAL]
        data = sorted(data, key=lambda x: x[1] + x[2] + x[5], reverse=True)

        for pos, row in enumerate(data[:10], start=1):
            user_id = row[0]

            total = row[1] + row[2] + row[5]  # money + vault + bank

            member = ctx.guild.get_member(user_id) or ctx.bot.get_user(user_id)
            if member is None:
                try:
                    member = await self.bot.fetch_user(user_id)
                except:
                    continue

            name = getattr(member, "display_name", member.name)

            msg += f"> `{pos}. {name} - {MONEY_ICON}{total:,}`\n"

        leaderboard_embed = base_embed_template(author,
            title="🎖️ | Top 10 riquezas",
            description=msg,
            color=0x7289da)
        
        await ctx.send(embed=leaderboard_embed)

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module economy loaded")
    await bot.add_cog(economy(bot))