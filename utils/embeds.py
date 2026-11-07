import discord

def base_embed_template(user, title, description, color=discord.Color.blurple()):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text=f"{user.display_name}/{user.id}")

    return embed

def thumb_embed_template(user, title, description, thumbnail, color=discord.Color.blurple()):
    embed = discord.Embed(
        title=title,
        description=description,
        color=color
    )

    embed.set_thumbnail(url=thumbnail)
    embed.set_footer(text=f"{user.display_name}/{user.id}")

    return embed