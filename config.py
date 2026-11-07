import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")

bot_prefix = "!"

money_icon = "🪙"
aura_icon = "✨"
vault_icon = "<:safe:1179377954032201749>"
vault_default_limit = 2000

banco_central = 1130974954205225041

log_channel = 1021218243974795335
general_channel = 1021078777830322176

error_handling = True