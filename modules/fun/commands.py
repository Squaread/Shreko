import discord
from discord.ext import commands
import asyncio
import random
from collections import Counter

from modules.fun import service as FunService
from modules.items import service as ItemsService

from utils.combat import combat

class DuelInviteView(discord.ui.View):
    def __init__(self, invited_user):
        super().__init__(timeout=60)
        self.invited_user = invited_user
        self.accepted = None

    @discord.ui.button(label="Dar uma lição", emoji="⚔️", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.invited_user.id:
            return await interaction.response.send_message("?", ephemeral=True)

        self.accepted = True
        self.stop()

        await interaction.response.defer()
        await interaction.message.delete()

class fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

#------------------------------------------
    @commands.hybrid_command(name="duelo", description="Duele com alguém haha")
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def duelo(self, ctx, member: discord.Member):
        if member.id == ctx.author.id or member.bot:
           return await ctx.reply("?")

        view = DuelInviteView(member)

        invite_embed = discord.Embed(title="Duelo", description=(f"{member.mention} ele te chamou de viado!\n\n"))

        invite_msg = await ctx.reply(embed=invite_embed, view=view)

        # Espera a pessoa clicar
        await view.wait()

        if view.accepted is None:
            return await invite_msg.edit(content="Expirado...", embed=None, view=None)

        if view.accepted is False: return
    
        author = ctx.author
        author_id = author.id
        member_id = member.id

        events = ""

        items = ItemsService.items
        #===============================
        equipment_user1 = items.get(ItemsService.get_user_equipment(author_id))
        #===============================
        equipment_user2 = items.get(ItemsService.get_user_equipment(member_id))
        
        user1 = {"hp": 100,
                 "user_name": author.name,
                 "user_id": author_id,
                 "equipment": equipment_user1,
                 "state": [],
                 "damage_dealt": 0}
        user2 = {"hp": 100,
                 "user_name": member.name,
                 "user_id": member_id,
                 "equipment": equipment_user2,
                 "state": [],
                 "damage_dealt": 0}

        duel_embed = discord.Embed(title="Duelo", description="Começando...")
        msg = await ctx.reply(embed=duel_embed)

        while True:
            await asyncio.sleep(6)

            user1, user2, message = combat(user1, user2)
            events += message
    

            hp1 = user1["hp"]
            hp2 = user2["hp"]

            if hp1 <= 0 or hp2 <=0:
                if hp1 <= 0:
                    hp1 = 0
                    events += f'\n💀 **{user1["user_name"]}** sobrou nada...'
                if hp2 <= 0:
                    hp2 = 0
                    events += f'\n💀 **{user2["user_name"]}** sobrou nada...'

            events = "\n".join(events.splitlines()[-20:])

            if user1["equipment"].get("style") == "firearm":
                equip_bullet = user1['equipment']['bullet']
                user_bullet = ItemsService.get_user_inventory(user1['user_id']).get(equip_bullet)
                if not user_bullet: 
                    user_bullet = 0
                equip1_text = f"{user1['equipment']['icon']} {items[equip_bullet]['icon']}`{user_bullet}x {equip_bullet}`"
            else:
                equip1_text = f"{user1['equipment']['icon']}"
            
            if user2["equipment"].get("style") == "firearm":
                equip_bullet = user2['equipment']['bullet']
                user_bullet = ItemsService.get_user_inventory(user2['user_id']).get(equip_bullet)
                if not user_bullet: 
                    user_bullet = 0
                equip2_text = f"{user2['equipment']['icon']} {items[equip_bullet]['icon']}`{user_bullet}x {equip_bullet}`"
            else:
                equip2_text = f"{user2['equipment']['icon']}"

            user1_state = " ".join(f"`{x}`" for x in user1['state'])
            user2_state = " ".join(f"`{x}`" for x in user2['state'])

            duel_embed.description = (
                f"**{user1['user_name']}:** `[💚{hp1}/100]`\n{equip1_text} `💥{user1['damage_dealt']}` {user1_state}\n**{user2['user_name']}:** `[💚{hp2}/100]`\n{equip2_text} `💥{user2['damage_dealt']}` {user2_state}\n"
                f"\n{events}"
            )
            duel_embed.set_footer(text=f"{ctx.author.display_name}/{author_id}")

            await msg.edit(content="", embed=duel_embed)
            if hp1 <= 0 or hp2 <= 0:
                break

#------------------------------------------
    @commands.hybrid_command(name="wordle", description="Adivinhe uma palavra a cada 24h")
    @commands.cooldown(1, 1, commands.BucketType.user)
    async def wordle(self, ctx, word: str):
        user = ctx.author
        user_id = user.id

        correct_word = FunService.wordle["word"].upper()
        word = word.upper()

        if len(word) > len(correct_word):
            return await ctx.send(f"Você botou mais letras que a correta hein haha")

        if word == correct_word:
            if not FunService.wordle["discovered"]:
                FunService.wordle_winner(user.display_name)
                chance = random.randint(1, 100)

                if chance > 60: item_name = "Caixa de merda" #40%
                elif chance > 30: item_name = "Caixa gulosa" #30%
                elif chance > 15: item_name = "Caixa 67" #15%
                else: item_name = "Caixa de pro" #15%
                ItemsService.add_user_inventory(user_id, item_name)
                item = ItemsService.items.get(item_name)
                msg = f"**🎉 Você acertou!**\n> Você ganhou uma **{item.get("icon")}{item_name}**!"
            else:
                msg = "**🎉 Você acertou!**"

        else:
            result = ["⬛"] * len(correct_word)
            remaining = Counter(correct_word)

            # Verificar letras na posição correta
            for i, letter in enumerate(word):
                if letter == correct_word[i]:
                    result[i] = "🟩"
                    remaining[letter] -= 1

            # Verificar letras na posição errada
            for i, letter in enumerate(word):
                if result[i] == "🟩":
                    continue

                if remaining[letter] > 0:
                    result[i] = "🟨"
                    remaining[letter] -= 1

            # Preencher espaços vazios
            for i in range(len(word), len(correct_word)):
                result[i] = "⬜"

            msg = "".join(result)

        wordle_hint = FunService.wordle["hint"]
        wordle_discovered = FunService.wordle["discovered"]
        wordle_winner = FunService.wordle["winner"]
        wordle_embed = discord.Embed(title="Wordle",description=f"**Dica:** {wordle_hint}\n{f"`Descoberta por {wordle_winner}`" if wordle_discovered else "`Não descoberta`"}\n\n{msg}", color=discord.Color.green())

        await ctx.reply(embed=wordle_embed, mention_author=False)

# ======================================================================
async def setup(bot: commands.Bot):
    print("[+] Module fun loaded")
    await bot.add_cog(fun(bot))