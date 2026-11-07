from discord.ext import commands, tasks
import random

from modules.jobs import service as JobsService

def choose_company(job, companys):
    job_companys = job["company"]

    names = []
    weights = []

    for c in job_companys:
        names.append(c)
        weights.append(companys[c]["chance"])

    return random.choices(names, weights=weights, k=1)[0]

def generate_jobs(data):
    jobs = data["jobs"]
    companys = data["companys"]

    vagas = set()
    result = []

    while len(result) < 5:
        job_name = random.choice(list(jobs.keys()))
        job_data = jobs[job_name]

        company = choose_company(job_data, companys)

        vaga_id = (job_name, company)

        if vaga_id in vagas:
            continue

        vagas.add(vaga_id)
        salary = (job_data["salary_base"] * companys[company]["salary_factor"])
        result.append({
            "job": job_name,
            "company": company,
            "salary": int(salary),
            "xp": int(job_data["xp_base"] * companys[company]["xp_factor"]),
            "courses": job_data["requirements"]["courses"],
            "phrases": job_data["phrases"],
            "rxp": int(job_data["requirements"]["rxp_base"] * companys[company]["rxp_factor"])
        })

    return result

class Jobs_tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
       self.update_jobs.start()

    @tasks.loop(hours=1)
    async def update_jobs(self):
        try:
           # print("LOOP RODANDO")

            data = JobsService.jobs
            JobsService.available_jobs = generate_jobs(data)

           # print(self.vagas)
        except Exception as e:
            print(f"[!] Erro ao gerar empregos modules.jobs.tasks: {e}")

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Tasks jobs loaded")
    await bot.add_cog(Jobs_tasks(bot))