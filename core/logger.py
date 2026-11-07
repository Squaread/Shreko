import discord

from config import LOG_CHANNEL

async def logger(bot, title, description, footer=0, color=discord.Color.blue()):
    if LOG_CHANNEL == 0: return
    channel = bot.get_channel(LOG_CHANNEL)

    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=f"SERVER: {footer}")
    await channel.send(embed=embed)