from discord.ext import commands

from core.errors import CommandOnCooldown
from config import ERROR_HANDLING

class Errors(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    if ERROR_HANDLING:
        @commands.Cog.listener()
        async def on_command_error(self, ctx, error):
            if isinstance(error, commands.CommandInvokeError):
                error = error.original

            if isinstance(error, commands.CommandNotFound):
                return

            if isinstance(error, (commands.CommandOnCooldown, CommandOnCooldown)):
                s = int(error.retry_after)
                h = s // 3600
                m = (s % 3600) // 60
                s = s % 60

                if h: cooldown = f"{h}h {m}min"
                elif m: cooldown = f"{m}min {s}s"
                else: cooldown = f"{s}s"

                return await ctx.reply(f":hourglass_flowing_sand: Espere {cooldown}")

            if isinstance(error, commands.MissingPermissions):
                return await ctx.reply("ii voce nao tem permissao!")

            if isinstance(error, (commands.MissingRequiredArgument, commands.BadArgument, commands.TooManyArguments)):
                return await ctx.reply("Comando incompleto/errado `;help`")

            print(error)
            await ctx.send(f"A ALGO HORRIVEL ACONTECEU\n`{error}`")


async def setup(bot: commands.Bot):
    print("[+] Core error_handling loaded")
    await bot.add_cog(Errors(bot))