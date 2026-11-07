import discord

from config import log_channel

async def logger(bot, title, description, footer=0, color=discord.Color.blue()):
    if log_channel == 0: return
    channel = bot.get_channel(log_channel)

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"SERVER: {footer}")
    await channel.send(embed=embed)