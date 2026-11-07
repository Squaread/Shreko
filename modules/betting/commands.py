# apostas
import discord
from discord.ext import commands
import asyncio 
from core.user_data import db

from modules.economy import service as EconomyService
from modules.betting import service as BettingService
from modules.admin import service as AdminService

from core.logger import logger

from utils.helpers import interpret_input_value

from config import bot_prefix, money_icon, banco_central

async def format_votes(bot, vote, aposta_data):
        votes_list = aposta_data["votes"].get(vote)
        if not votes_list:
            return "Nenhum voto"

        payouts = aposta_data.get("payouts")
        winner = aposta_data.get("winner")
        
        lines = []
        for v in votes_list:
            user_id = int(v["user"])
            amount = v["amount"]

            user = bot.get_user(user_id)

            name = user.display_name if user else f"{await bot.fetch_user(user_id)}"

            if winner == vote and str(user_id) in payouts:
                lines.append(f"• {name}: `{money_icon}{amount}` `🏆{money_icon}{payouts[str(user_id)]}`")
            else:
                lines.append(f"• {name}: `{money_icon}{amount}`")

        return "\n".join(lines)

async def update_aposta(bot, aposta_data, aposta_id):
        #print(aposta_data)
        channel = bot.get_channel(aposta_data["channel_id"])
        message = await channel.fetch_message(aposta_data["message_id"])

        option_C = aposta_data['options'].get('C')
        option_D = aposta_data['options'].get('D')

        votes_a = await format_votes(bot, "A", aposta_data)
        votes_b = await format_votes(bot, "B", aposta_data)
        if option_C: votes_c = await format_votes(bot, "C", aposta_data)
        if option_D: votes_d = await format_votes(bot, "D", aposta_data)
        

        embed = discord.Embed(
        title=f"APOSTA | {aposta_data['title']}", description=f"**Acumulado:** `{money_icon}{aposta_data["fund"]}`/**Código:** `{aposta_id}`")
        winner = ''
        if aposta_data["open"] == False: text_status = "TRANCADA"
        if aposta_data["open"] == True: text_status = "ABERTA"
        if aposta_data["status"] == False: 
            text_status = "FINALIZADA"
            winner = aposta_data.get("winner")

        embed.add_field(
            name=f"A) {aposta_data['options']['A']}{' 🏆' if winner == 'A' else ''}",
            value=votes_a,
            inline=True
        )
        embed.add_field(
            name=f"B) {aposta_data['options']['B']}{' 🏆' if winner == 'B' else ''}",
            value=votes_b,
            inline=True
        )

        if option_C:
            embed.add_field(
            name=f"C) {option_C}{' 🏆' if winner == 'C' else ''}",
            value=votes_c,
            inline=False)
        
        if option_D:
            embed.add_field(
            name=f"D) {option_D}{' 🏆' if winner == 'D' else ''}",
            value=votes_d,
            inline=True)

        embed.set_footer(text=f"Owner: {aposta_data["creator"]}/status: {text_status}")
        embed.color = 0xe91e63

        await message.edit(embed=embed)

def calculate_payout(aposta, winning_option):
        winners = aposta["votes"][winning_option]

        if not winners:
            return {}

        total_pool = aposta["fund"]

        total_winning_amount = sum(v["amount"] for v in winners)
        if total_winning_amount == 0:return {}

        payouts = {}

        for v in winners:
            user = v["user"]
            amount = v["amount"]

            share = amount / total_winning_amount
            payout = int(total_pool * share)

            payouts[user] = payout

        return payouts

class betting(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
   #------------------------------------------
    @commands.hybrid_command(name="criaraposta", aliases=["caposta"], description="Crie apostas [fund é apenas pros admistradores do bot]")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def criaraposta(self, ctx, title=None, option_a=None, option_b=None, option_c=None, option_d=None, fund = 0):
        creator = ctx.author.id
        official = False
        if fund and not creator in AdminService.load_admins().get("economy"): fund = 0
        else:
            if fund > 0:
                banco_central_fund = EconomyService.get_user_bank(banco_central) #db.get_user_data("bank", banco_central)
                if fund > banco_central_fund: return await ctx.reply("O Banco Central não tem dinheiro suficiente...")
                EconomyService.add_user_bank(banco_central, -fund) #db.post_user_data("bank", banco_central, banco_central_fundos-fund)
                official = True
        option_A = option_a
        option_B = option_b
        option_C = option_c
        option_D = option_d

        if not title or not option_A or not option_B:
            return await ctx.send(f'`{bot_prefix}criaraposta "<title>" "<option_A>" "<option_B>" "<option_C>" "<option_D>"`')
        
        if isinstance(option_C, str):
            if option_C.lower() == "none": option_C = None
        if isinstance(option_D, str):
            if option_D.lower() == "none": option_D = None
        
        data = BettingService.load_betting()
        aposta_id = str(len(data) + 1)
        
        aposta_embed = discord.Embed(title=f"APOSTA | {title}", description=f"**Acumulado:** `{money_icon}{fund}`/**Código:** `{aposta_id}`")
        aposta_embed.add_field(name=f"A) {option_A}", value="", inline=True)
        aposta_embed.add_field(name=f"B) {option_B}", value="", inline=True)
        if option_C != None: aposta_embed.add_field(name=f"C) {option_C}", value="", inline=False)
        if option_D != None: aposta_embed.add_field(name=f"D) {option_D}", value="", inline=True)
        aposta_embed.set_footer(text=f"Owner: {creator}/status: ABERTA")
        aposta_embed.color = 0xe91e63

        msg = await ctx.send(embed=aposta_embed)
        message_id = msg.id
        channel_id = msg.channel.id
        server_id = msg.guild.id

        data[aposta_id] = {
        "title": title,
        "options": {
            "A": option_A,
            "B": option_B,
            "C": option_C,
            "D": option_D
        },
        "creator": creator,
        "votes": {
            "A": [],
            "B": [],
            "C": [],
            "D": []
        },
        "status": True,
        "open": True,
        "message_id": message_id,
        "channel_id": channel_id,
        "server_id": server_id,
        "official": official,
        "fund": fund
        }

        BettingService.save_betting(data)
        await logger(self.bot, "criaraposta", f"`{ctx.author.name}/{creator}` criou `{aposta_id}` `{data[aposta_id]}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x61602C)
    #------------------------------------------

    @commands.hybrid_command(name="votaraposta", aliases=["vaposta"], description="Vote numa aposta")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def votaraposta(self, ctx, aposta_id=None, option=None, amount=None):
        if not aposta_id or not option or not amount: return await ctx.send(f"`{bot_prefix}votaraposta <apostaCode> <option> <amount>`")
        amount = interpret_input_value(amount)

        data = BettingService.load_betting()

        aposta = data.get(aposta_id)
        if not aposta: return
        if not aposta.get("server_id") == ctx.guild.id: return await ctx.reply("A aposta não é desse servidor")
        if aposta["status"] == False: return await ctx.reply("Essa aposta já foi terminada.")
        if aposta["open"] == False: return await ctx.reply("Essa aposta está trancada.")
        user_id = str(ctx.author.id)

        user_money = db.get_user_data("money", ctx.author.id)
        if amount == "all": amount = int(user_money)
 
        # impedir voto duplo
        if any(v["user"] == user_id for v in aposta["votes"]["A"]) or \
        any(v["user"] == user_id for v in aposta["votes"]["B"]) or \
        any(v["user"] == user_id for v in aposta["votes"]["C"]) or \
        any(v["user"] == user_id for v in aposta["votes"]["D"]):
            return await ctx.send("voce ja votou noob")

        if isinstance(option, str): 
            option = option.upper()
        else: return

        if aposta["options"].get(option) == None: return
        if amount > user_money: return await ctx.send("tu nem tem esse valor noob")
        if amount < 1: return await ctx.send(f"Tá duro? Valor mínimo: `{money_icon}2`")
    #-------------------------------------------------------------------------------------------
        EconomyService.add_user_money(ctx.author.id, -amount) #db.post_user_data("money", ctx.author.id, user_money-amount)
        aposta["fund"] = aposta["fund"] + amount
        aposta["votes"][option].append({
            "user": user_id,
            "amount": amount
        })

        BettingService.save_betting(data)

        await update_aposta(self.bot, aposta, aposta_id)

        if ctx.interaction: await ctx.send("Votado computado", ephemeral=True)
        else: await ctx.message.add_reaction("✅")

    #------------------------------------------
    @commands.hybrid_command(name="finalizaraposta", aliases=["faposta"], description="Finalize uma aposta")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def finalizaraposta(self, ctx, aposta_id, option):
        user_id = ctx.author.id
        data = BettingService.load_betting()

        aposta = data.get(aposta_id)
        if not aposta: return

        if aposta["creator"] != user_id and not user_id in AdminService.load_admins().get("economy"): return

        if isinstance(option, str): 
            option = option.upper()
        else: return
        if not aposta["options"].get(option): return

        if not aposta["status"]:
            return await ctx.send("essa aposta já foi finalizada")

        official = bool(aposta["official"])

        # calcular payout
        payouts = calculate_payout(aposta, option)

        # pagar usuarios
        for user, amount in payouts.items():
            EconomyService.add_user_money(int(user), amount)
            if official:
                aura = round((amount/1000)*5)
                EconomyService.add_user_aura(int(user), aura)

        if not payouts: # aposta sem vencedores vai tudo pro banco central
            income = int(aposta['fund'])
            EconomyService.add_user_bank(banco_central, income)

        # fechar aposta
        aposta["status"] = False
        aposta["winner"] = option
        aposta["payouts"] = payouts

        BettingService.save_betting(data)

        await update_aposta(self.bot, aposta, aposta_id)

        try: await ctx.message.delete()
        except: pass
        if ctx.interaction: await ctx.send("Finalizada", ephemeral=True)

        await logger(self.bot, "finalizaraposta", f"`{ctx.author.name}/{user_id}` finalizou `{aposta_id}` `{option}` acumulado: `{money_icon}{aposta["fund"]}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x61602C)
           
    #------------------------------------------
    @commands.hybrid_command(name="reexibiraposta", aliases=["raposta"], description="Reexiba uma aposta")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def reexibiraposta(self, ctx, aposta_id):
        user_id = ctx.author.id
        data = BettingService.load_betting()
        aposta = data.get(aposta_id)
        if not aposta: return
        if not aposta["creator"] == user_id and not user_id in AdminService.load_admins().get("economy"): return await ctx.reply("Você não é o criador dessa aposta")
        embed = discord.Embed(title="Carregando...")
        msg = await ctx.send(embed=embed)
        aposta["message_id"] = msg.id
        aposta["channel_id"] = msg.channel.id

        BettingService.save_betting(data)
        await asyncio.sleep(2)
        await update_aposta(self.bot, aposta, aposta_id)

    #------------------------------------------
    @commands.hybrid_command(name="trancaraposta", aliases=["taposta"], description="Tranque uma aposta")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def trancaraposta(self, ctx, aposta_id):
        user_id = ctx.author.id
        data = BettingService.load_betting()
        aposta = data.get(aposta_id)
        if not aposta: return
        if not aposta["creator"] == user_id and not user_id in AdminService.load_admins().get("economy"): return await ctx.reply("Você não é o criador dessa aposta")
        if not aposta["status"]: return

        if aposta["open"] == False: return
        aposta["open"] = False
        BettingService.save_betting(data)
        await update_aposta(self.bot, aposta, aposta_id)

        try: await ctx.message.delete()
        except: pass
        if ctx.interaction: await ctx.send("Trancada", ephemeral=True)

    #------------------------------------------
    @commands.hybrid_command(name="abriraposta", aliases=["aaposta"], description="Destranque uma aposta")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def abriraposta(self, ctx, aposta_id):
        user_id = ctx.author.id
        data = BettingService.load_betting()
        aposta = data.get(aposta_id)
        if not aposta: return
        if not aposta["creator"] == user_id and not user_id in AdminService.load_admins().get("economy"): return await ctx.reply("Você não é o criador dessa aposta")
        if not aposta["status"]: return

        if aposta["open"] == True: return
        aposta["open"] = True
        BettingService.save_betting(data)
        await update_aposta(self.bot, aposta, aposta_id)

        try: await ctx.message.delete()
        except: pass
        if ctx.interaction: await ctx.send("Aberta", ephemeral=True)

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module betting loaded")
    await bot.add_cog(betting(bot))