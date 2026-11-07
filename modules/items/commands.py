import discord
from discord.ext import commands
import json
import random

from modules.economy import service as EconomyService
from modules.items import service as ItemsService
from modules.items import lootbox
from modules.jobs import service as JobsService

from core.logger import logger

from utils import taxes

from config import bot_prefix, money_icon, aura_icon, banco_central

class items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#------------------------------------------
    @commands.hybrid_command(name="inventario", aliases=["inv"], description="Veja seus itens")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def inventario(self, ctx):
        user_id = ctx.author.id

        inventory = ItemsService.get_user_inventory(user_id)

        items = ItemsService.items

        description = "\n".join(
            f"{items[item]['icon']} **{item}** x{quantidade}"
            for item, quantidade in inventory.items()
            if quantidade > 0
        )

        if not description:
            description = ""

        embed = discord.Embed(
            title="Seu inventário",
            description=description
        )

        embed.set_footer(text=f"{ctx.author.display_name}/{user_id}")
        await ctx.reply(embed=embed, mention_author=False)

#------------------------------------------
    @commands.hybrid_command(name="comprar", description="Compre itens [item_name quant, ex: glock 17 2]")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def comprar(self, ctx, *, item_nq: str):
        parts = item_nq.rsplit(" ", 1)
        query_item = parts[0].lower()
        quant = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 1

        if quant <= 0: return await ctx.reply("morre")

        user_id = ctx.author.id
        items = ItemsService.items
        economy = EconomyService.economy

        # Procurar item
        item_name = next((name for name in items if query_item == name.lower() or query_item in name.lower().split()), None)

        if not item_name:
            return await ctx.reply(f"`{query_item}` não encontrado `{bot_prefix}comprar <item_name> <quant(opcional)>`")

        item = items[item_name]
        category = item["category"]

        # Cursos
        if category == "course":
            quant = 1

            if item_name in JobsService.get_user_courses(user_id):
                return await ctx.reply("Você já comprou esse curso!")

        # Categorias compraveis
        elif category not in ("equipment", "ammo"):
            return await ctx.reply("Esse item não pode ser comprado!")

        # Calcular preço e imposto
        price = int(item["price"] * economy["items_price_coefficient"]) * quant
        tax = taxes.item_tax(None, price)
        full_price = price + tax

        # Verificar saldo
        user_money = EconomyService.get_user_money(user_id)
        if full_price > user_money: return await ctx.reply("Você não tem dinheiro suficiente!")

        # Pagamento e recebimento
        EconomyService.add_user_money(user_id, -full_price)

        if category == "course": JobsService.add_user_courses(user_id, item_name)
        else: ItemsService.add_user_inventory(user_id, item_name, quant)

        # Repassar imposto pro banco central
        if tax: EconomyService.add_user_bank(banco_central, tax)

        await ctx.reply(f"Você comprou **{item_name}** {f'({quant}x) ' if category != 'course' else ''} por `{money_icon}{full_price}`")
        await logger(self.bot, "comprar", f"`{ctx.author.name}/{user_id}` comprou `{item_name} {quant}x` por `{money_icon}{full_price}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x0cff00)

#------------------------------------------
    @commands.hybrid_command(name="vender", description="Venda seus itens")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def vender(self, ctx, *, item_nq: str):
        parts = item_nq.rsplit(" ", 1)
        query_item = parts[0].lower()
        quant = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 1

        if quant <= 0: return await ctx.reply("morre")

        user_id = ctx.author.id
        inventory = ItemsService.get_user_inventory(user_id)
        items = ItemsService.items
        economy = EconomyService.economy

        # Procurar item no inventario
        item_name = next((name for name in inventory if query_item == name.lower() or query_item in name.lower().split()), None)

        if not item_name:
            return await ctx.reply(f"`{query_item}` não encontrado no inventário `{bot_prefix}vender <item_name> <quant(opcional)>`")

        item = items.get(item_name)

        if not item:
            return await ctx.reply("Item não encontrado")

        category = item["category"]

        # Categorias protegidas de venda
        if category in ("award", "course"):
            return await ctx.reply("Espertinho vc n pode vender isso")

        # Verificar quantidade que o usuario tem
        item_quant = inventory[item_name]

        if quant > item_quant:
            return await ctx.reply("Você nem tem tudo isso...")

        # Calcular valor da venda
        price_coefficient = economy["items_price_coefficient"]

        price = round(item["price"] * price_coefficient * 0.7 * quant)

        tax = taxes.item_tax(None, price)
        final_value = price - tax

        ItemsService.add_user_inventory(user_id, item_name, -quant)
        EconomyService.add_user_money(user_id, final_value)

        # Repassar imposto ao banco central
        if tax: EconomyService.add_user_bank(banco_central, tax)

        tax_msg = (f"\n> `Imposto sobre venda: -{money_icon}{tax}`"if tax else "")

        await ctx.reply(f"Você vendeu **{item_name}** ({quant}x) por `{money_icon}{final_value}`{tax_msg}")
        await logger(self.bot, "vender", f"`{ctx.author.name}/{user_id}` vendeu `{item_name} {quant}x` por `{money_icon}{final_value}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x0add00)

#------------------------------------------
    @commands.hybrid_command(name="dar", description="Dê itens para alguém")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def dar(self, ctx, member: discord.Member, *, item_nq: str):
        parts = item_nq.rsplit(" ", 1)
        query_item = parts[0].lower()
        quant = int(parts[1]) if len(parts) == 2 and parts[1].isdigit() else 1

        giver_id = ctx.author.id
        receiver_id = member.id

        if giver_id == receiver_id or member.bot:
            return await ctx.reply("noob")

        if quant <= 0:
            return await ctx.reply("morre")

        # Procurar item no inventario
        inventory = ItemsService.get_user_inventory(giver_id)

        item_name = next((name for name in inventory if query_item == name.lower() or query_item in name.lower().split()), None)

        if not item_name:
            return await ctx.reply(f"`{query_item}` não encontrado no seu inventário...")

        # Transferir item
        success = ItemsService.transfer_item(giver_id, receiver_id, item_name, quant)
        if not success: return

        await ctx.reply(f"Você deu **{item_name}** ({quant}x) para {member.mention}!")
        await logger(self.bot, "dar", f"`{ctx.author.name}/{giver_id}` deu `{item_name} {quant}x` para `{member.name}/{receiver_id}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x0add00)

#------------------------------------------
    @commands.hybrid_command(name="equipar", description="Equipe um item")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def equipar(self, ctx, *,item_namep):
        user_id = ctx.author.id
        inventory = ItemsService.get_user_inventory(user_id)
        query_item = item_namep.lower()
        items = ItemsService.items

        for item_name in list(inventory.keys()):
            if item_name.lower() == query_item or query_item in item_name.lower().split():
                if not items.get(item_name).get("category") == "equipment": return await ctx.reply("Vai botar no cu?")

                ItemsService.user_equip_item(user_id, item_name)
                return await ctx.reply("equipado", mention_author=False)
            
        await ctx.reply(f"`{query_item}` não encontrado no seu inventário `{bot_prefix}inventario` `{bot_prefix}equipar <item_name>`")

#------------------------------------------
    @commands.hybrid_command(name="desequipar", description="Desequipe seu equipamento")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def desequipar(self, ctx):
        user_id = ctx.author.id
        
        user_equipment = ItemsService.get_user_equipment(user_id)
        if not user_equipment: 
            return await ctx.reply("vc tem nada equipado noob...")
        
        ItemsService.user_unequip_item(user_id)
            
        await ctx.reply(f"Você desequipou **{user_equipment}**")

#------------------------------------------
    @commands.hybrid_command(name="usar", description="Use um item utilizável")
    @commands.cooldown(1, 2, commands.BucketType.user)
    async def usar(self, ctx, *, item_name):
        user_id = ctx.author.id
        user_inventary = ItemsService.get_user_inventory(user_id)

        item = None

        for nome, quant in user_inventary.items():
                    if nome.lower() == item_name.lower():
                        item = nome
                        #item_quant = quant
                        break

        if item:
            items = ItemsService.items
            category = items.get(item).get("category")
            type = items.get(item).get("type")
            #rarity = items.get(item).get("rarity")
            item_gain_quant_factor = items.get(item).get("income")
            if item_gain_quant_factor: item_gain_quant_factor = item_gain_quant_factor.get("item_gain_quant_factor")
            if not item_gain_quant_factor: item_gain_quant_factor = 0
            item_gain_quant = 1

            if category == "lootbox":
                    gains = ""
                    item_claim, money, aura = lootbox.open_box(item)
                    print(item_claim)

                    if item_claim and item_gain_quant_factor > 0:
                        if items.get(item_claim).get("category") == "ammo": item_gain_quant = random.randint(5*item_gain_quant_factor, 50*item_gain_quant_factor)
                        ItemsService.add_user_inventory(user_id, item_claim, item_gain_quant)
                        gains += f'\n> {f"**{item_gain_quant}x**" if item_gain_quant > 1 else ""}{items.get(item_claim).get("icon")}**{item_claim}**'
                    if money:
                        EconomyService.add_user_money(user_id, money)
                        gains = gains + f"\n> `{money_icon}{money}`"
                    if aura:
                        EconomyService.add_user_aura(user_id, aura)
                        gains = gains + f"\n> `{aura_icon}{aura}`"

                    ItemsService.add_user_inventory(user_id, item, -1)
    
                    if money > 0 and aura > 0:
                        lootbox_embed = discord.Embed(title="Lootbox", description=f"Você abriu **{items.get(item).get("icon")}{item}** e recebeu:{gains}", color=0xdcc400)
                    else:
                        lootbox_embed = discord.Embed(title="Lootbox", description=f"Você abriu **{items.get(item).get("icon")}{item}** e TINHA UMA BOMBA DENTRO {gains}", color=0xe50000)

                    lootbox_embed.set_footer(text=f"{ctx.author.display_name}/{user_id}")
                    await ctx.reply(embed=lootbox_embed)
                    return await logger(self.bot, "lootbox", f"`{ctx.author.name}/{user_id}` abriu `{item}` e ganhou: {gains}", f"{ctx.guild.name}/{ctx.guild.id}", 0x79f8ff)
            
            elif category == "random":
                return await ctx.reply(f"Você usou **{items.get(item).get("icon")}{item}** {items.get(item).get("use_message")}")

            elif category == "upgrader":
                if type == "vault":
                    vault_tier = EconomyService.get_user_vault_tier(user_id)
                    EconomyService.upgrade_user_vault_tier(user_id)
                    ItemsService.add_user_inventory(user_id, item, -1)
                    return await ctx.reply(f"Você melhorou seu cofre `{vault_tier}LV -> {vault_tier+1}LV`")


            return await ctx.reply(f'`{item}` não é utilizável...')
        await ctx.reply(f'`{item_name}` não encontrado `{bot_prefix}usar <item_name>`')

#------------------------------------------
    @commands.hybrid_command(name="loja", description="Abra o painel da loja [armas, cursos]")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def loja(self, ctx, type=None):
        if not isinstance(type, str): type = "cu"
        economy = EconomyService.economy
        price_coefficient = economy.get("items_price_coefficient")
        items = ItemsService.items

        if type.lower() == "armas":
            loja_embed = discord.Embed(
                title="Loja de Armas",description=f'`{bot_prefix}comprar <item_name> <quant(opcional)>`',
                color=discord.Color.blue())

            melee = []
            pistols = []
            rifles = []
            ammo = []

            for name, data in items.items():
                if not data.get('price'): continue
                price = data['price']*price_coefficient
                tax = taxes.item_tax(None, price)
                price += tax

                if data.get("style") == "melee":
                    melee.append(
                        f"{data['icon']}**{name}** `{money_icon}{price}`\n"
                        f"`💥{data['damage']} ⚡{data['agility']} 🎯{data['accuracy']}`"
                    )

                elif data.get("model") == "pistol":
                    pistols.append(
                        f"{data['icon']}**{name}** `{money_icon}{price}`\n"
                        f"`🔸{data['bullet']}/{data['capacity']}\n"
                        f"💥{data['damage']} ⚡{data['agility']} 🎯{data['accuracy']}`"
                    )

                elif data.get("model") == "rifle":
                    rifles.append(
                        f"{data['icon']}**{name}** `{money_icon}{price}`\n"
                        f"`🔸{data['bullet']}/{data['capacity']}\n"
                        f"💥{data['damage']} ⚡{data['agility']} 🎯{data['accuracy']}`"
                    )

                elif data.get("category") == "ammo":
                    ammo.append(
                        f"{data['icon']}**{name}** `{money_icon}{price}`"
                    )

            if melee:
                loja_embed.add_field(
                    name="Armas Brancas",
                    value="\n\n".join(melee),
                    inline=True
                )

            if pistols:
                loja_embed.add_field(
                    name="Pistolas",
                    value="\n\n".join(pistols),
                    inline=True
                )

            if rifles:
                loja_embed.add_field(
                    name="Rifles",
                    value="\n\n".join(rifles),
                    inline=True
                )

            if ammo:
                loja_embed.add_field(
                    name="Munições",
                    value=" ".join(ammo),
                    inline=False
                )

            return await ctx.send(embed=loja_embed)

        if type.lower() == "cursos":
            loja_embed = discord.Embed(
                title="Loja de Cursos",description=f'`{bot_prefix}comprar <item_name> <quant(opcional)>`',
                color=discord.Color.blue())
            for name, data in items.items():
                if data.get('category') == "course":
                    price = data.get('price')*price_coefficient
                    tax = taxes.item_tax(None, price)
                    price += tax
                    loja_embed.add_field(name=f"{data.get('icon')}{name}", value=f"`{money_icon}{price}`")
            return await ctx.send(embed=loja_embed)
        
        else:
            loja_embed=discord.Embed(title="Loja", description=f"Seja bem vindo(a), selecione uma categoria:\n`{bot_prefix}loja armas\n{bot_prefix}loja cursos`")
            await ctx.send(embed=loja_embed)

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module items loaded")
    await bot.add_cog(items(bot))