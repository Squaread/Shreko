from config import BANCO_CENTRAL, MONEY_ICON

from modules.economy import service as EconomyService

def pix_tax(user_sender_id: int, user_receiver_id: int, amount: int):
    economy = EconomyService.economy
    tax_pix = economy.get("tax_pix")
    tax_minpix = economy.get("tax_minpix")
    tax = 0
    tax_msg = ""

    if amount > tax_minpix and tax_pix > 0 and user_receiver_id != BANCO_CENTRAL:
        tax = int(max(0, amount - tax_minpix) * tax_pix)
        tax_msg = f"> `Imposto sobre pix: -{MONEY_ICON}{tax} (descontado do seu saldo)`"

        EconomyService.money_transaction(user_sender_id, BANCO_CENTRAL, tax)

    return tax, tax_msg

def dep_tax(user_id:int, amount:int):
    economy = EconomyService.economy
    tax_dep = economy.get("tax_dep")
    tax_mindep = economy.get("tax_mindep")
    tax = 0
    tax_msg = ""

    if amount > tax_mindep and tax_dep > 0:
        tax = int(max(0, amount - tax_mindep) * tax_dep)
        tax_msg = f"\n> `Imposto sobre dep: -{MONEY_ICON}{tax} (descontado direto)`"

        if user_id: EconomyService.bank_transaction(user_id, BANCO_CENTRAL, tax)

    return tax, tax_msg

def item_tax(user_id: int, amount: int):
    economy = EconomyService.economy
    tax_item = economy.get("tax_item")
    tax_minitem = economy.get("tax_minitem")
    tax = 0

    if amount > tax_minitem and tax_item > 0:
        tax = int(max(0, amount - tax_minitem) * tax_item)

        if user_id: EconomyService.bank_transaction(user_id, BANCO_CENTRAL, tax)

    return tax

def rent_tax(user_id: int, amount: int):
    economy = EconomyService.economy
    tax_rent = economy.get("tax_rent")
    tax_minrent = economy.get("tax_minrent")
    tax = 0
    tax_msg = ""

    if amount > tax_minrent and tax_rent > 0:
        tax = int(max(0, amount - tax_minrent) * tax_rent)
        tax_msg = f"\n> `Imposto de renda: -{MONEY_ICON}{tax}`"

        if user_id: EconomyService.bank_transaction(user_id, BANCO_CENTRAL, tax)

    return tax, tax_msg