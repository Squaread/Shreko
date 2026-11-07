import random
import json

from core.user_data import db

from modules.economy import service as EconomyService

from config import aura_icon

equipment_default =  {
    "damage": 4,
    "agility": 60,
    "accuracy": 98,
    "style": "hand",
    "icon": "🥊"
    }

def combat(user1, user2):
        if not user1["equipment"]: user1["equipment"] = equipment_default
        if not user2["equipment"]: user2["equipment"] = equipment_default
        #print(user1["equipment"]["agility"], user2["equipment"]["agility"])
        user1_start_chance = user1["equipment"]["agility"] * random.uniform(0.5, 1.2)
        user2_start_chance = user2["equipment"]["agility"] * random.uniform(0.5, 1.2)

       # actions = ["indo pra cima", "posicionando...", "coberto"]
        states = ["ferido"]
       # user1_state = random.choice(states)
       # user2_state = random.choice(states)

        events = ""

        def simulate(atk, dfs):
            mentioned = False
            message = "\n"
        
            hit_chance = atk["equipment"]["accuracy"] - (dfs["equipment"]["agility"] * 0.5)
            hit_chance = max(15, min(95, hit_chance))
            if (random.uniform(0, 100) <= hit_chance and not 'atordoado' in atk['state']) or 'atordoado' in dfs['state']:
                # Dano com variação de ±15%
                damage = int(atk["equipment"]["damage"] * random.uniform(0.85, 1.15))

                def thrust():
                    msg = f'💥 **{dfs["user_name"]}** levou um golpe!'
                    return msg

                if atk["equipment"]["style"] == "firearm":
                    bullet_type = atk["equipment"]["bullet"]
                    bullet = bullet_type
                    user_inventory = json.loads(db.get_user_data("inventory", atk["user_id"]))
                    ammunition = user_inventory.get(bullet)
                    if ammunition:
                        if atk["equipment"]["model"] == "pistol":
                            gunshots = min(random.randint(1, atk["equipment"]["capacity"]), ammunition)
                        elif atk["equipment"]["model"] == "rifle":
                            gunshots = min(random.randint(2, atk["equipment"]["capacity"]), ammunition)

                        if user_inventory[bullet] - gunshots <= 0:
                            del user_inventory[bullet]
                        else:
                            user_inventory[bullet] -= gunshots
                        db.post_user_data("inventory", atk["user_id"], json.dumps(user_inventory))

                        gunshots = int(min(max(0, min(gunshots * atk["equipment"]["accuracy"] * random.uniform(0.2, 1) / 100, gunshots)), ammunition))
                        if gunshots == 0:
                            message += f'**{atk["user_name"]}** errou todos os tiros!'
                            return message
                        damage = damage*gunshots
                        message += f'💥 **{dfs["user_name"]}** levou {gunshots} tiros!' 
                    else:
                        message += f'**{atk["user_name"]}** ficou sem munição!'
                        atk["equipment"] = equipment_default
                        return message
                else:
                    message += thrust()

                # Chance de crítico baseada em precisão
                crit_chance = atk["equipment"]["accuracy"] / 10  # 4~5%
                if random.uniform(0, 100) <= crit_chance:
                    damage = int(damage*1.5)
                    if not 'atordoado' in dfs['state']: dfs['state'].append('atordoado')
                    message += f'\n> 💣 Ataque certeiro! `-💚{damage}` `atordoado`' 
        
                else:
                    message += f'\n> `-💚{damage}`'

                dfs["hp"] -= round(damage)
                atk["damage_dealt"] += round(damage)

                if damage >= 70 or ('mijado' in dfs['state'] and dfs['hp'] < 20):
                    lost_aura = random.randint(10, 60)
                    message += f'\n**{dfs["user_name"]}** se mijou inteiro... `-{aura_icon}{lost_aura}`'
                    EconomyService.add_user_aura(dfs['user_id'], -lost_aura)
                  # db.post_user_data("xp", dfs['user_id'], db.get_user_data("xp", dfs['user_id'])-lost_aura)
                    if not 'mijado' in dfs['state']: dfs['state'].append('mijado')
            else:
                message+=f"💨 **{dfs["user_name"]}** esquivou-se do ataque!"
                if 'atordoado' in atk['state']:
                    wakeup_chance = random.randint(1, 3)
                    if wakeup_chance == 1: 
                        atk['state'].remove('atordoado')
                        message += f"\n**{atk['user_name']}** recuperou-se!"
            return message
        if user2_start_chance>user1_start_chance:
            atk=user2
            dfs = user1
        else: 
            atk=user1
            dfs = user2
        event = simulate(atk, dfs)
      #  print("PRIMEIRO ATAQUE:", event)
        events += event
        atk, dfs = dfs, atk
        event = simulate(atk, dfs)
       # print("SEGUNDO ATAQUE:", event)
        events += event

      #  print(user1, user2, events)
        return user1, user2, events