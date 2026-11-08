import discord
from discord.ext import commands 
import json
import random

from modules.economy import service as EconomyService
from modules.items import service as ItemsService
from modules.jobs import service as JobsService

from core.cooldown import check_and_apply_cooldown
from core.logger import logger

from utils import taxes

from config import BOT_PREFIX, BANCO_CENTRAL, MONEY_ICON, AURA_ICON

class jobs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#------------------------------------------
    @commands.hybrid_command(name="empregos", description="Veja vagas abertas")
    @commands.cooldown(1, 20, commands.BucketType.user)
    async def empregos(self, ctx):
        vagas = JobsService.available_jobs
        economy = EconomyService.economy
        if not vagas:
            return await ctx.send("Nenhuma vaga disponível no momento")

        texto = ""
        i=0
        for vaga in vagas:
            i+=1
            courses = vaga['courses']
            if not courses: courses = ""
            else: courses=("\n" + str(courses)).replace("[", "").replace("]", "").replace("'", "").replace(",", "\n")
            texto += (
                f"{i}. **{vaga['job']}** em **{vaga['company']}**\n`Salário: {MONEY_ICON}{int((vaga['salary']*economy.get("private_salary_coefficient"))+(economy.get("private_salary_parity_base")-(vaga['salary']*economy.get("private_salary_coefficient")))*economy.get("private_salary_parity"))} ~{AURA_ICON}{vaga['xp']*economy.get("aura_coefficient")}`\n`Requisitos: {AURA_ICON}{vaga["rxp"]}`{courses}\n\n"
            )
        empregos_embed = discord.Embed(
            title="📢 Empregos Disponíveis",
            description=f"`{BOT_PREFIX}enviarcurriculo <job_number>`\n{texto}",
            color=discord.Color.green()
        )
        empregos_embed.set_footer(text="A lista atualiza a cada 1 hora")
        await ctx.send(embed=empregos_embed)

#------------------------------------------
    @commands.hybrid_command(name="enviarcurriculo", description="Tente entrar num emprego")
    async def enviarcurriculo(self, ctx, job_number: int):
        user_id = ctx.author.id
        i=0
        for vaga in JobsService.available_jobs:
            i+=1
            if i==job_number:
                
                await check_and_apply_cooldown(user_id, ctx.command.name)
                
                user_aura = EconomyService.get_user_aura(user_id)
                user_courses = JobsService.get_user_courses(user_id)
                vaga_rxp = vaga["rxp"]
                vaga_courses = vaga["courses"]


                user_job = JobsService.get_user_job(user_id)
                if user_job:
                    if user_job.get("company") == "Governo":
                        return await ctx.reply("Você já trabalha pro governo N pode....")
                if vaga_rxp>user_aura:
                    phrases = ["voce se mijou no meio da entrevista pois exalou cheiro de beta kkkkkkkkkkk (sem aura)",
                               "voce se cagou no meio das perguntas por ser BETA kkkkkkkkkkkkkk (sem aura)", "voce se demostrou um BETINHA e pro betinha sobra NADA (sem aura)"]
                    return await ctx.reply(f"Rejeitado: {random.choice(phrases)}")
                if vaga_courses:
                    if not set(vaga_courses).issubset(user_courses):
                        phrases = ["voce se mijou no meio da entrevista pois não soube responder nenhuma pergunta kkkkkkkkkkk (falta curso)",
                               "voce se cagou no meio das perguntas kkkkkkkkkkkkkk (falta curso)"]
                        return await ctx.reply(f"Rejeitado: {random.choice(phrases)}")
                    
                JobsService.set_user_job(user_id, vaga)
                await ctx.reply("Carteira assinada!")
                await logger(self.bot, "enviarcurriculo", f"`{ctx.author.name}/{user_id}` agora trabalha de `{vaga}`", f"{ctx.guild.name}/{ctx.guild.id}", 0x665b20)

#------------------------------------------
    @commands.hybrid_command(name="clt", description="Veja sua CLT e cursos")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def clt(self, ctx, user: discord.Member=None):
        if not user: user=ctx.author
        if user.bot: return
        economy = EconomyService.economy

        user_id = user.id
        user_job = JobsService.get_user_job(user_id)
        if not user_job: return await ctx.send(f"Sua carteira ainda não é assinada... VAGAS ABERTAS `{BOT_PREFIX}empregos`")
        job_name = user_job['job']
        job_salary = user_job['salary']
        job_company = user_job['company']

        if not job_company == "Governo":
            job_salary = job_salary*economy.get("private_salary_coefficient")
            job_salary = int(job_salary+(economy.get("private_salary_parity_base")-job_salary)*economy.get("private_salary_parity"))
        else:
            jobs = JobsService.jobs
            job_salary = jobs.get("public_ofices").get(job_name).get("salary_base")

        job_xp = user_job['xp']*economy.get("aura_coefficient")
        user_courses = JobsService.get_user_courses(user_id)

        clt_embed=discord.Embed(title="CARTEIRA DE TRABALHO", description=f"NOME: `{user.name}`\nCPF: `{user_id}`\nAURA: `{AURA_ICON}{EconomyService.get_user_aura(user_id)}`")
        clt_embed.add_field(name=f"{job_company}", value=f"**{job_name}**\nSalário: `{MONEY_ICON}{job_salary} ~{AURA_ICON}{job_xp}`")
        if user_courses:
         user_courses=(str(user_courses)).replace("[", "").replace("]", "").replace("'", "").replace(",", "\n")
        else: user_courses = ""
        clt_embed.add_field(name="Cursos", value=user_courses)
        clt_embed.color = 0x3498db
        clt_embed.set_footer(text=f"{ctx.author.display_name}/{ctx.author.id}")
        await ctx.reply(embed=clt_embed, mention_author=False)

#------------------------------------------
    @commands.hybrid_command(name="trabalhar", aliases=["trab"], description="Trabalhe em troca de dinheiro")
    async def trabalhar(self, ctx):
        user_id = ctx.author.id

        await check_and_apply_cooldown(user_id, ctx.command.name)

        user_job = JobsService.get_user_job(user_id)
        economy = EconomyService.economy
        jobs = JobsService.jobs
        banco_central_saldo = EconomyService.get_user_bank(BANCO_CENTRAL)

        if banco_central_saldo < 0 and user_job: # Caso economia em crise ha chance de demissao
            if not user_job.get('company') == "Governo":
                index_collapse = 0.5*(abs(banco_central_saldo)/1000)
                fired_chance = random.randint(1, 100)

                if index_collapse>=fired_chance:
                    JobsService.set_user_job(user_id, None)

                    carta_demissao = discord.Embed(title="Carta de demissão", description=f"**{user_job.get("company")}**\nDecorrente da crise atual, tomamos a difícil decisão de desliga-lo xD...")
                    carta_demissao.set_footer(text=f"{ctx.author.display_name}/{user_id}")
                    carta_demissao.color = 0xFF0000
                    await ctx.reply(embed=carta_demissao)
                    return

        if not user_job:
            job_name = "Vagabundagem"
            phrases = ["Você pediu dinheiro no semáforo", "Você pegou umas latinhas na rua para vender", "Você entrou num canal para caçar umas moedas", "Você defecou e vendeu como esterco", "Você vendeu foto na internet", "Você achou umas moedas na rua", "Você vendeu sua conta do Free Fire", "Você vendeu uns itens usados", "Vendeu pack no Instagram", "Levou umas coisas pro ferro-velho", "Pediu dinheiro pra mãe", "Pediu dinheiro pra vó", "Pediu dinheiro pro pai", "Pediu dinheiro pro tio", "Alguém usou seu código do TikTok"]
            income = random.randint(80, 220)
            xp_income = random.randint(1, 5)
            company = None
        else:
            job_name = user_job['job']
            phrases = user_job['phrases']
            company = user_job['company']
            income = int(user_job['salary'])

            if not company == "Governo":
                income = income * economy.get("private_salary_coefficient")
                income = int(income+(economy.get("private_salary_parity_base")-income)*economy.get("private_salary_parity"))
            else:
                income = jobs.get("public_ofices").get(job_name).get("salary_base")

                banco_central_saldo = EconomyService.get_user_bank(BANCO_CENTRAL)
                if income > banco_central_saldo:
                    return await ctx.reply("O Banco Central não tem dinheiro suficiente...")
                EconomyService.add_user_bank(BANCO_CENTRAL, -income)

            xp_income = round(random.uniform(user_job['xp']*0.8, user_job['xp']*1.2)*economy.get("aura_coefficient"))

        base = income
        tax, tax_msg = taxes.rent_tax(None, income) # Calcular o imposto
        income -= tax

        item = None
        box_message = ""
        item_chance = random.randint(1, 100)
        if item_chance <= 2:
            item = "Caixa de pro"
        elif item_chance <= 4:
            item = "Caixa 67"
        elif item_chance <= 8:
            item = "Caixa misteriosa"
        elif item_chance <= 14:
            item = "Caixa gulosa"
        elif item_chance <= 24:
            item = "Caixa de merda"
        item_name = item
        item = ItemsService.items.get(item)
        if item:
            ItemsService.add_user_inventory(user_id, item_name)
            box_message = f"\n> Você ganhou uma **{item.get("icon")}{item_name}**!"
        
        EconomyService.add_user_money(user_id, income)
        EconomyService.add_user_aura(user_id, xp_income)

        trab_embed = discord.Embed(title=job_name, description=f"{random.choice(phrases)}\n> `{MONEY_ICON}{base}` `{AURA_ICON}{xp_income}`{tax_msg}{box_message}")
        trab_embed.set_footer(text=f"{ctx.author.display_name}/{user_id}")
        trab_embed.color = 0x2ecc71
        await ctx.reply(embed=trab_embed)
        await logger(self.bot, "trab", f"`{ctx.author.name}/{user_id}` pegou `{MONEY_ICON}{income}` {item_name}", f"{ctx.guild.name}/{ctx.guild.id}", 0x75ff7a)

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module jobs loaded")
    await bot.add_cog(jobs(bot))