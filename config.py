import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

BOT_PREFIX = "!"

MONEY_ICON = "🪙"
AURA_ICON = "✨"
VAULT_ICON = "<:safe:1179377954032201749>"
VAULT_DEFAULT_LIMIT = 2000

BANCO_CENTRAL = 1130974954205225041 # Id da conta usada como BANCO CENTRAL (nesse caso o ID do proprio bot)

SERVERS_ID = [1514453067574284432, 1021078777385730049] # Servidores nos quais o bot vai aceitar interagir
LOG_CHANNEL = 1021078777830322176 # Canal onde serao enviadas as logs
GENERAL_CHANNEL = 1021078777830322176 # Canal onde o wordle vai escolher a palavra diaria

ERROR_HANDLING = True # Pra debug é melhor deixar como false pois ficara mais claro onde estao os erros