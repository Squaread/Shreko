from discord.ext import commands

class CommandOnCooldown(commands.CommandError):
    def __init__(self, retry_after):
        self.retry_after = retry_after
        super().__init__(f"Cooldown: {retry_after}")