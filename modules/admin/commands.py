import discord
from discord.ext import commands, tasks
from discord import ui
import psutil
import os
import time
import json
import subprocess

from modules.economy import service as EconomyService
from modules.admin import service as AdminService
from modules.items import service as ItemsService
from modules.jobs import service as JobsService

from core.user_data import db

from config import BANCO_CENTRAL, MONEY_ICON, AURA_ICON

# Embed -> Economy config
def build_painel_embed(economy, jobs):
    public_offices = jobs.get("public_ofices")

    painel = discord.Embed(title="Painel Econômico")
    painel.add_field(
        name="Geral",
        value=(
            f"Banco Central: `{MONEY_ICON}{db.get_user_data('bank', BANCO_CENTRAL)}`\n"
            f"Coeficiente valor dos itens: `{economy.get('items_price_coefficient')}`\n"
            f"Coeficiente ganho de aura: `{economy.get('aura_coefficient')}`"
        ),
        inline=False
    )
    painel.add_field(
        name="Salários privados",
        value=(
            f"Coeficiente geral: `{economy.get('private_salary_coefficient')}`\n"
            f"Pariedade base: `{MONEY_ICON}{economy.get('private_salary_parity_base')}`\n"
            f"Coeficiente de pariedade: `{economy.get('private_salary_parity')}`"
        ),
        inline=False
    )
    painel.add_field(
        name="Salários públicos",
        value=(
            f"Presidente: `{MONEY_ICON}{public_offices.get('Presidente').get('salary_base')}`\n"
            f"STF: `{MONEY_ICON}{public_offices.get('STF').get('salary_base')}`\n"
            f"Ministro da Economia: `{MONEY_ICON}{public_offices.get('Ministro da Economia').get('salary_base')}`\n"
            f"Presidente da CGF: `{MONEY_ICON}{public_offices.get('Presidente da CGF').get('salary_base')}`\n"
            f"Conselheiro: `{MONEY_ICON}{public_offices.get('Conselheiro').get('salary_base')}`"
        ),
        inline=True
    )
    painel.add_field(
        name="Bolsa família",
        value=(
            f"Valor base: `{MONEY_ICON}{economy.get('money_assistance_value')}`\n"
            f"Variança: `{economy.get('money_assistance_variance')*100}%`\n"
            f"Recebe apenas quem tem menos de: `{MONEY_ICON}{economy.get('money_assistance_maxmoney')}`"
        ),
        inline=False
    )
    painel.add_field(
        name="Impostos",
        value=(
            f"**Imposto de renda:** `{economy.get('tax_rent')*100}%`\n"
            f"Isenção até: `{MONEY_ICON}{economy.get('tax_minrent')}`\n"
            f"**Imposto sobre compra/venda:** `{economy.get('tax_item')*100}%`\n"
            f"Isenção até: `{MONEY_ICON}{economy.get('tax_minitem')}`\n"
            f"**Imposto sobre pix:** `{economy.get('tax_pix')*100}%`\n"
            f"Isenção até: `{MONEY_ICON}{economy.get('tax_minpix')}`\n"
            f"**Imposto sobre deposito:** `{economy.get('tax_dep')*100}%`\n"
            f"Isenção até: `{MONEY_ICON}{economy.get('tax_mindep')}`\n"
            f"**Imposto PSE (saldo):** `{economy.get('tax_saldo')*100}%`\n"
            f"Isenção até: `{MONEY_ICON}{economy.get('tax_minsaldo')}`\n"
            f"Dobra taxa a cada: `{MONEY_ICON}{economy.get('tax_saldofactor')}`\n"
            f"Taxa máxima: `{economy.get('tax_saldomax')*100}%`"
        ),
        inline=False
    )
    return painel

def parse_numero(texto: str):
    """Converte a string do modal em int ou float automaticamente."""
    texto = texto.strip().replace(",", ".")
    if "." in texto:
        return float(texto)
    return int(texto)

# Modal -> Economy config
class EditModal(ui.Modal):
    def __init__(self, title, fields, on_submit_callback, get_message):
        super().__init__(title=title)
        self.field_keys = []
        self.on_submit_callback = on_submit_callback
        self.get_message = get_message

        for key, label, default in fields:
            ti = ui.TextInput(label=label, default=str(default), required=True, max_length=100)
            self.field_keys.append(key)
            setattr(self, f"input_{key}", ti)
            self.add_item(ti)

    async def on_submit(self, interaction: discord.Interaction):
        values = {}
        try:
            for key in self.field_keys:
                ti: ui.TextInput = getattr(self, f"input_{key}")
                values[key] = parse_numero(ti.value)
        except ValueError:
            await interaction.response.send_message(
                "❌ Valor inválido, use apenas números (ex: 100 ou 0.05).", ephemeral=True
            )
            return

        self.on_submit_callback(values)

        economy = EconomyService.economy
        jobs = JobsService.jobs
        novo_embed = build_painel_embed(economy, jobs)

        msg = self.get_message()
        await msg.edit(embed=novo_embed)
        await interaction.response.send_message("✅ Dados atualizados com sucesso haha!\n-# Dados perigosos são ignorados então confira...", ephemeral=True)

# PainelSelect -> Economy config
class PainelSelect(ui.Select):
    def __init__(self, author_id, get_message):
        self.author_id = author_id
        self.get_message = get_message

        options = [
            discord.SelectOption(label="Geral", value="geral", description="Coeficientes de itens e aura"),
            discord.SelectOption(label="Salários privados", value="privados"),
            discord.SelectOption(label="Salários públicos", value="publicos"),
            discord.SelectOption(label="Bolsa família", value="bolsa"),
            discord.SelectOption(label="Imposto de renda", value="tax_rent"),
            discord.SelectOption(label="Imposto de compra/venda", value="tax_item"),
            discord.SelectOption(label="Imposto de pix", value="tax_pix"),
            discord.SelectOption(label="Imposto de depósito", value="tax_dep"),
            discord.SelectOption(label="Imposto PSE (saldo)", value="tax_saldo"),
        ]
        super().__init__(placeholder="Selecione o que deseja editar...", options=options, min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message("sai", ephemeral=True)
            return

        economy = EconomyService.economy
        jobs = JobsService.jobs
        public_offices = jobs.get("public_ofices")
        escolha = self.values[0]

        if escolha == "geral":
            def salvar(v):
                economy["items_price_coefficient"] = v["items_price_coefficient"]
                economy["aura_coefficient"] = v["aura_coefficient"]
                EconomyService.save_economy(economy)

            fields = [
                ("items_price_coefficient", "Coef. valor dos itens", economy.get("items_price_coefficient")),
                ("aura_coefficient", "Coef. ganho de aura", economy.get("aura_coefficient")),
            ]
            modal = EditModal("Editar Geral", fields, salvar, self.get_message)

        elif escolha == "privados":
            def salvar(v):
                economy["private_salary_coefficient"] = v["private_salary_coefficient"]
                economy["private_salary_parity_base"] = v["private_salary_parity_base"]
                economy["private_salary_parity"] = v["private_salary_parity"]
                EconomyService.save_economy(economy)

            fields = [
                ("private_salary_coefficient", "Coeficiente geral", economy.get("private_salary_coefficient")),
                ("private_salary_parity_base", "Pariedade base", economy.get("private_salary_parity_base")),
                ("private_salary_parity", "Coeficiente de pariedade", economy.get("private_salary_parity")),
            ]
            modal = EditModal("Editar Salários Privados", fields, salvar, self.get_message)

        elif escolha == "publicos":
            def salvar(v):
                public_offices["Presidente"]["salary_base"] = v["presidente"]
                public_offices["STF"]["salary_base"] = v["stf"]
                public_offices["Ministro da Economia"]["salary_base"] = v["ministro"]
                public_offices["Presidente da CGF"]["salary_base"] = v["cgf"]
                public_offices["Conselheiro"]["salary_base"] = v["conselheiro"]
                jobs["public_ofices"] = public_offices
                JobsService.save_jobs(jobs)

            fields = [
                ("presidente", "Presidente", public_offices.get("Presidente").get("salary_base")),
                ("stf", "STF", public_offices.get("STF").get("salary_base")),
                ("ministro", "Ministro da Economia", public_offices.get("Ministro da Economia").get("salary_base")),
                ("cgf", "Presidente da CGF", public_offices.get("Presidente da CGF").get("salary_base")),
                ("conselheiro", "Conselheiro", public_offices.get("Conselheiro").get("salary_base")),
            ]
            modal = EditModal("Editar Salários Públicos", fields, salvar, self.get_message)

        elif escolha == "bolsa":
            def salvar(v):
                economy["money_assistance_value"] = v["money_assistance_value"]
                economy["money_assistance_variance"] = v["money_assistance_variance"]
                economy["money_assistance_maxmoney"] = v["money_assistance_maxmoney"]
                EconomyService.save_economy(economy)

            fields = [
                ("money_assistance_value", "Valor base", economy.get("money_assistance_value")),
                ("money_assistance_variance", "Variança (0.05 = 5%)", economy.get("money_assistance_variance")),
                ("money_assistance_maxmoney", "Renda máx. p/ receber", economy.get("money_assistance_maxmoney")),
            ]
            modal = EditModal("Editar Bolsa Família", fields, salvar, self.get_message)

        elif escolha == "tax_rent":
            def salvar(v):
                if v["tax_rent"] > 1: return
                economy["tax_rent"] = v["tax_rent"]
                economy["tax_minrent"] = v["tax_minrent"]
                EconomyService.save_economy(economy)

            fields = [
                ("tax_rent", "Imposto de renda (0.05 = 5%)", economy.get("tax_rent")),
                ("tax_minrent", "Isenção até", economy.get("tax_minrent")),
            ]
            modal = EditModal("Editar Imposto de Renda", fields, salvar, self.get_message)

        elif escolha == "tax_item":
            def salvar(v):
                if v["tax_item"] > 1: return
                economy["tax_item"] = v["tax_item"]
                economy["tax_minitem"] = v["tax_minitem"]
                EconomyService.save_economy(economy)

            fields = [
                ("tax_item", "Imposto compra/venda (0.05 = 5%)", economy.get("tax_item")),
                ("tax_minitem", "Isenção até", economy.get("tax_minitem")),
            ]
            modal = EditModal("Editar Imposto de Compra/Venda", fields, salvar, self.get_message)

        elif escolha == "tax_pix":
            def salvar(v):
                if v["tax_pix"] > 1: return
                economy["tax_pix"] = v["tax_pix"]
                economy["tax_minpix"] = v["tax_minpix"]
                EconomyService.save_economy(economy)

            fields = [
                ("tax_pix", "Imposto sobre pix (0.05 = 5%)", economy.get("tax_pix")),
                ("tax_minpix", "Isenção até", economy.get("tax_minpix")),
            ]
            modal = EditModal("Editar Imposto de Pix", fields, salvar, self.get_message)

        elif escolha == "tax_dep":
            def salvar(v):
                if v["tax_dep"] > 1: return
                economy["tax_dep"] = v["tax_dep"]
                economy["tax_mindep"] = v["tax_mindep"]
                EconomyService.save_economy(economy)

            fields = [
                ("tax_dep", "Imposto sobre depósito (0.05 = 5%)", economy.get("tax_dep")),
                ("tax_mindep", "Isenção até", economy.get("tax_mindep")),
            ]
            modal = EditModal("Editar Imposto de Depósito", fields, salvar, self.get_message)

        elif escolha == "tax_saldo":
            def salvar(v):
                if v["tax_saldo"] > 1 or v["tax_saldomax"] > 1: return
                if v["tax_saldomax"] < v["tax_saldo"]: return
                economy["tax_saldo"] = v["tax_saldo"]
                economy["tax_minsaldo"] = v["tax_minsaldo"]
                economy["tax_saldofactor"] = v["tax_saldofactor"]
                economy["tax_saldomax"] = v["tax_saldomax"]
                EconomyService.save_economy(economy)

            fields = [
                ("tax_saldo", "Imposto PSE (0.05 = 5%)", economy.get("tax_saldo")),
                ("tax_minsaldo", "Isenção até", economy.get("tax_minsaldo")),
                ("tax_saldofactor", "Dobra taxa a cada", economy.get("tax_saldofactor")),
                ("tax_saldomax", "Taxa máxima (0.05 = 5%)", economy.get("tax_saldomax")),
            ]
            modal = EditModal("Editar Imposto de Depósito", fields, salvar, self.get_message)

        await interaction.response.send_modal(modal)

# View -> Economy config
class PainelView(ui.View):
    def __init__(self, author_id):
        super().__init__(timeout=300)
        self.message = None
        self.add_item(PainelSelect(author_id, lambda: self.message))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return True 
    
class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#------------------------------------------
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def editdata(self, ctx, user: discord.Member, parameter, data):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("moderation"): return
        user_id = user.id
        if isinstance(parameter, str): parameter = parameter.lower()
        else: return
        if isinstance(data, str):
            print(data)
            if data.lower == ("none"): 
                data=None
                print(data)
        db.post_user_data(parameter, user_id, data)

#------------------------------------------
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def sql(self, ctx, *, command):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("owner"): return
    
        db.sql_command(command)
        await ctx.reply("pronto")

#------------------------------------------
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def botinfo(self, ctx):
       # if not ctx.author.id in admins_id: return
        process = psutil.Process(os.getpid())

        latency = round(self.bot.latency * 1000)
        cpu = process.cpu_percent(interval=1)
        memoria_mb = process.memory_info().rss / 1024 / 1024

        embed = discord.Embed(
            title="Bot info",
        )

        embed.add_field(name="CPU", value=f"{cpu:.1f}%")
        embed.add_field(name="RAM", value=f"{memoria_mb:.2f} MB")
        embed.add_field(name="PING", value=f"{latency}ms")

        await ctx.send(embed=embed)

#------------------------------------------
    @commands.command()
    async def systeminfo(self, ctx):
        if ctx.author.id != 634908192404668426: return

        disk = psutil.disk_usage("/")
        disk_total = round(disk.total / 1024 / 1024 / 1024, 2)
        disk_used = round(disk.used / 1024 / 1024 / 1024, 2)
        disk_percent = disk.percent

        cpu_total = psutil.cpu_percent(interval=0.5)

        mem = psutil.virtual_memory()
        ram_total = mem.total / 1024 / 1024
        ram_used = mem.used / 1024 / 1024
        ram_percent = mem.percent

        uptime = time.time() - psutil.boot_time()

        embed = discord.Embed(title="Sistema")

        embed.add_field(name="CPU", value=f"{cpu_total:.1f}%")
        embed.add_field(name="RAM", value=f"{ram_used:.0f}/{ram_total:.0f} MB ({ram_percent}%)")
        embed.add_field(name="SSD", value=f"{disk_used}/{disk_total} GB ({disk_percent}%)")
        embed.add_field(name="Uptime", value=f"{uptime/3600:.2f} horas")

        await ctx.send(embed=embed)

#------------------------------------------
    @commands.command()
    async def addmoney(self, ctx, user: discord.User, data: int):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("economy"): return
        user_id = user.id
            
        user_money = db.get_user_data("money", user_id)
        db.post_user_data("money", user_id, user_money+data)
 
        await ctx.reply(f"Adicionado `{MONEY_ICON}{data}` usuário já tinha `{MONEY_ICON}{user_money}` ficando com `{MONEY_ICON}{user_money+data}`")

#------------------------------------------
    @commands.command()
    async def addbank(self, ctx, user: discord.User, data: int):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("economy"): return
        user_id = user.id
            
        user_bank = db.get_user_data("bank", user_id)
        db.post_user_data("bank", user_id, user_bank+data)
 
        await ctx.reply(f"Adicionado `{MONEY_ICON}{data}` usuário já tinha `{MONEY_ICON}{user_bank}` ficando com `{MONEY_ICON}{user_bank+data}`")

#------------------------------------------
    @commands.command()
    async def addaura(self, ctx, user: discord.User, data: int):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("economy"): return
        user_id = user.id
        
        user_aura = db.get_user_data("aura", user_id)
        db.post_user_data("aura", user_id, user_aura+data)
        await ctx.reply(f"Adicionado `{AURA_ICON}{data}` usuário já tinha `{AURA_ICON}{user_aura}` ficando com `{AURA_ICON}{user_aura+data}`")

#------------------------------------------
    @commands.command()
    async def multar(self, ctx, user: discord.User, data: int):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("moderation"): return
        user_id = user.id
        data = -abs(data)
        
        user_money = db.get_user_data("money", user_id)
        db.post_user_data("money", user_id, user_money+data)
        bancocentral_money = db.get_user_data("bank", BANCO_CENTRAL)
        db.post_user_data("bank", BANCO_CENTRAL, bancocentral_money+abs(data))
        
        await ctx.reply(f"{user.mention} recebeu uma multa de `-{MONEY_ICON}{abs(data)}` usuário já tinha `{MONEY_ICON}{user_money}` ficando com `{MONEY_ICON}{user_money+data}`")

#------------------------------------------
    @commands.command()
    async def additem(self, ctx, user: discord.User, data: str, quant: int=1):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("economy") and not author.id in AdminService.load_admins().get("moderation"): return
        user_id = user.id
        items = ItemsService.load_items()
        if not data in items: return await ctx.reply(f"`{data}` não encontrado")

        user_inventory = json.loads(db.get_user_data("inventory", user_id))

        if data in user_inventory: user_inventory[data] += quant
        else: user_inventory[data] = quant

        db.post_user_data("inventory", user_id, json.dumps(user_inventory))
        await ctx.reply(f"Feito `{user.id}` `{data} {quant}x`")

#-----------------------------------------
    @commands.command()
    async def pixdobanco(self, ctx, user: discord.Member, data: int):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("economy"): return
        user_id = user.id
        
        user_money = db.get_user_data("money", user_id)
        bancocentral_money = db.get_user_data("bank", BANCO_CENTRAL)
        if data > bancocentral_money: await ctx.reply(f"o banco não tem tudo isso!")
        db.post_user_data("money", user_id, user_money+data)
        db.post_user_data("bank", BANCO_CENTRAL, bancocentral_money-data)
        await ctx.reply(f"`{MONEY_ICON}{data}` transferido do banco central para {user.display_name}")

#-----------------------------------------
    @commands.command()
    async def sicronizar(self, ctx):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("owner"): return
        await self.bot.tree.sync()
        print("[*] SICRONIZACAO DE SLASH COMMANDS")
        await ctx.reply("Sicronizado!")

#-----------------------------------------
    @commands.command()
    async def economia(self, ctx):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("economy"):
            return

        economy = EconomyService.economy
        jobs = JobsService.jobs

        embed = build_painel_embed(economy, jobs)
        view = PainelView(author.id)

        msg = await ctx.send(embed=embed, view=view)
        view.message = msg  # Modal mensagem

#-----------------------------------------
    @commands.command() # Comando perigoso
    async def shell(self, ctx, *, code):
        author = ctx.author
        if not author.id in AdminService.load_admins().get("owner"): return
        try:
            result = subprocess.run(code, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr

            if not output:
                output = "No response [OK]"

            await ctx.send(f"```bash\n{output[:1900]}\n```")

        except subprocess.TimeoutExpired:
            await ctx.send("Timeout")
        except Exception as e:
            await ctx.send(f"Error: `{e}`")

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module admin loaded")
    await bot.add_cog(admin(bot))
