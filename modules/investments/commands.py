import discord
from discord.ext import commands
from discord.ext import commands, tasks
import math

from modules.economy import service as EconomyService
from modules.investments import service as InvestmentsService

from config import bot_prefix, money_icon

class investments(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#---------------------------------------------------------------
    @commands.hybrid_command(name="mercado", description="Veja o mercado de investimentos", aliases=["market"])
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def mercado(self, ctx):
        market = InvestmentsService.market

        currencies = ""
        shares = ""

        for name, data in market.items():
            value = data.get("value", 0)
            last_value = data.get("last_value", 0)

            stonks_emoji = None       
            if value > last_value: stonks_emoji = "<:Stonks:1532493283748614206>"
            elif value < last_value: stonks_emoji = "<:NotStonks:1532493350614335611>"
            else: stonks_emoji = "<:Ice:1532538728244056125>"

            if data.get("category") == "share":
                shares = shares + f"**{name}**\n`{data.get("code")}` `↩️{money_icon}{last_value:.4f}` `{money_icon}{value:.4f}`{stonks_emoji}\n"
            elif data.get("category") == "currency":
                currencies = currencies + f"**{name}**\n`{data.get("code")}` `↩️{money_icon}{last_value:.4f}` `{money_icon}{value:.4f}`{stonks_emoji}\n"

        market_embed = discord.Embed(title="Mercado/Bolsa de valores", description=f"`{bot_prefix}investir <code> <amount>` `{bot_prefix}negociar <code> <amount>` `{bot_prefix}investimentos <@user>`")
        market_embed.add_field(name="Moedas", value=currencies)
        market_embed.add_field(name="Ações", value=shares)
        market_embed.set_footer(text=f"{ctx.author.display_name}/{ctx.author.id} - Atualiza a cada 3 horas")
        await ctx.send(embed=market_embed)

#---------------------------------------------------------------
    @commands.hybrid_command(name="investir", description="Faça investimentos")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def investir(self, ctx, code: str, amount: int):
        if amount <= 0: return
        user_id = ctx.author.id
        market = InvestmentsService.market
        code = code.upper()
        for name, data in market.items():
               item_code = data.get("code")
               if not item_code: continue

               if item_code.upper() == code:
                    value = data.get("value")
                    price = value*amount
                    investors = market[name].get("investors")

                    if price < 1: return await ctx.reply(f"`{money_icon}{price}` o valor final não pode ser menor que `{money_icon}1`")
                    price = math.ceil(price)

                    if price < 100: return await ctx.reply(f"Total: `{money_icon}{price}` você tem que investir pelo menos `{money_icon}100`")
                    user_money = EconomyService.get_user_money(user_id)
                    if user_money < price: return await ctx.reply(f"Você não tem `{money_icon}{price}` pobre")
                    EconomyService.add_user_money(user_id, -price)

                    if not investors.get(str(user_id)): investors[str(user_id)] = amount
                    else: investors[str(user_id)] += amount 

                    InvestmentsService.market = market
                    InvestmentsService.save_market(market)
                    return await ctx.reply(f"Você comprou `{code} {amount}` por `{money_icon}{price}`")

        await ctx.reply(f"`{code}` não encontrado `{bot_prefix}mercado`")

#---------------------------------------------------------------
    @commands.hybrid_command(name="investimentos", description="Faça investimentos")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def investimentos(self, ctx, user: discord.User = None):
        if not user: user = ctx.author
        else: 
            if user.bot == True: return

        user_id = user.id
        market = InvestmentsService.market
        total_value = 0
        total_last = 0
        stonks_emoji = None   

        investments = ""
        for name, data in market.items():
                investors = data.get("investors")
                if not investors: continue

                if str(user_id) in investors:
                    code = data.get("code")
                    amount = investors[str(user_id)]
                    value = math.floor(data.get("value")*amount)
                    last_value = math.floor(data.get("last_value")*amount)
                    total_value += value
                    total_last += last_value
    
                    if value > last_value: stonks_emoji = "<:Stonks:1532493283748614206>"
                    elif value < last_value: stonks_emoji = "<:NotStonks:1532493350614335611>"
                    else: stonks_emoji = "<:Ice:1532538728244056125>"

                    text = f"**{name}** `{code} {amount}x` `↩️{money_icon}{last_value}` `{money_icon}{value}`{stonks_emoji}\n"
                    investments = investments + text

        if not investments: return await ctx.reply("Você não tem investimentos")

        if total_value > total_last: stonks_emoji = "<:Stonks:1532493283748614206>"
        elif total_value < total_last: stonks_emoji = "<:NotStonks:1532493350614335611>"
        else: stonks_emoji = "<:Ice:1532538728244056125>"

        investments = investments + f"\n **TOTAL:** `↩️{money_icon}{total_last}` `{money_icon}{total_value}`{stonks_emoji}"

        investments_embed = discord.Embed(title="Investimentos", description=investments)
        investments_embed.set_thumbnail(url=user.avatar.url)
        investments_embed.set_footer(text=f"{ctx.author.display_name}/{ctx.author.id}")
        await ctx.reply(embed=investments_embed)
        
#---------------------------------------------------------------
    @commands.hybrid_command(name="negociar", description="Venda investimentos")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def negociar(self, ctx, code: str, amount: int):
         if amount <= 0: return 
         user_id = ctx.author.id
         market = InvestmentsService.market
         code = code.upper()

         for name, data in market.items():
            item_code = data.get("code")
            if not item_code: continue
         
            if item_code.upper() == code:
                investors = market[name].get("investors")
                item_value = market[name].get("value")

                value = math.floor(item_value*amount)
                if not investors or not str(user_id) in investors: return await ctx.send(f"Você não tem `{code}`")

                quant = investors[str(user_id)]
                print(quant, amount)
                if quant-amount < 0: return await ctx.reply(f"Você tem apenas `{code} {quant}x`")

                investors[str(user_id)] = quant - amount
                if investors[str(user_id)] <= 0: del investors[str(user_id)]

                EconomyService.add_user_money(user_id, value)
                
                InvestmentsService.market = market
                InvestmentsService.save_market(market)
                return await ctx.reply(f"Você vendeu `{code} {amount}x` por `{money_icon}{value}`")

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module investments loaded")
    await bot.add_cog(investments(bot))