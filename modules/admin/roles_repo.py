
import discord
from discord.ext import commands
import sqlite3
import json
from pathlib import Path

from core.logger import logger

BASE_DIR = Path(__file__).resolve().parent

class roles_repo(commands.Cog):
    def __init__(self, bot):

        self.bot = bot
        self.db = sqlite3.connect(BASE_DIR/"roles_repo.db")
        self.db.execute("""
            CREATE TABLE IF NOT EXISTS roles_repo (
                guild_id INTEGER,
                user_id INTEGER,
                roles TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        """)
        self.db.commit()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        roles = [role.id for role in member.roles
            if not role.is_default() and not role.managed]

        self.db.execute("INSERT OR REPLACE INTO roles_repo (guild_id, user_id, roles) VALUES (?, ?, ?)", 
            (member.guild.id, member.id, json.dumps(roles)))

        self.db.commit()

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        cursor = self.db.execute("SELECT roles FROM roles_repo WHERE guild_id = ? AND user_id = ?", 
            (member.guild.id, member.id))

        result = cursor.fetchone()

        if result is None: return

        saved_roles = json.loads(result[0])

        roles = []

        for role_id in saved_roles:
            role = member.guild.get_role(role_id)

            if role is None: continue
            if role.managed or role.is_default(): continue
            if role >= member.guild.me.top_role: continue

            roles.append(role)

        if roles:
            try: 
                await member.add_roles(*roles, reason="Restaurando cargos")
                await logger(self.bot, title="roles_repo | User roles recovered", description=f"`{member.name}/{member.id}`", footer=f"{member.guild.name}/{member.guild.id}")

            except discord.Forbidden: return # Erro de permissao
            except discord.HTTPException as error:
                print(f"[!] Erro modules/admin/roles_repo: {error}")

        # Apagar
        if not roles:
            self.db.execute("DELETE FROM roles_repo WHERE guild_id = ? AND user_id = ?", 
                (member.guild.id, member.id))
            self.db.commit()

        else:
            current_roles = {role.id for role in member.roles}
            if all(role.id in current_roles for role in roles):
                self.db.execute("DELETE FROM roles_repo WHERE guild_id = ? AND user_id = ?",
                    (member.guild.id, member.id))
                self.db.commit()

    def cog_unload(self):
        self.db.close()

# ==========================================================
async def setup(bot: commands.Bot):
    print("[+] Module admin/roles_repo loaded")
    await bot.add_cog(roles_repo(bot))
