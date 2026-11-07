import random

from modules.items import service as ItemsService

def open_box(box_name):
    items = ItemsService.items

    box = items.get(box_name)
    if not box or not box.get("category") == "lootbox": return None, None, None
    income = box.get("income")

    nomes = []
    pesos = []

    item = None
    money = None
    aura = None
    escolhido = None

    money = random.randint(income.get("min_money"), income.get("max_money"))
    aura = random.randint(income.get("min_xp"), income.get("max_xp"))
    box_type = box.get("type")

    if box.get("style") == "unsafe":
        loss_chance = random.randint(1, 4)
        if loss_chance == 1:
            money = money*(-1)
            aura = aura*(-1)
            return escolhido, money, aura
        
    if box.get("factor"):
        for nome, item in items.items():

            if not box_type == "all":
                if not item.get("category") == box_type and not item.get("category") == "lootbox": continue
            if item.get("category") == "award" or item.get("category") == "course": continue
            chance = item.get("lootbox_chance")

            if chance:
                raridade = item.get("rarity", "common")

                peso_final = chance * box.get("factor").get(raridade, 1)

                nomes.append(nome)
                pesos.append(peso_final)


        escolhido = random.choices(
            nomes,
            weights=pesos,
            k=1
        )[0]
        item = items[escolhido]
    return escolhido, money, aura