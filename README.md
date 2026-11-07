# Shreko
O pior bot de toda a humanidade

Cada módulo tem as suas próprias funções num arquivo `service.py` tipo: 

`
from modules.economy import service as EconomyService`<br>`
EconomyService.add_user_money(user_id, amount)`

Quaisquer módulos podem chamar o service do outro isso faz com que seja tudo uma grande teia (não delete nada)

O código todo ainda é meio gore mas era bem pior antes da reescrita...

Qualquer alteração aqui ele atualiza sozinho no server -> Isso quer dizer que tenho que aprovar antes

**COMO RODAR LOCALMENTE**

Feito na versão Python 3.14.6 (quase certeza que funciona nas outras próximas)
1. Baixe os arquivos e o descompacte
2. Crie um arquivo `.env` e adicione nele `DISCORD_BOT_TOKEN=o token do seu bot de teste`
3. Abre o terminal no diretório raiz do bot
4. Execute `pip install -r requirements.txt` no terminal para baixar as dependências
5. Rode com `python main.py`

Se você fizer alguma alteração e quiser botar no Shreko principal é só mandar um Pull requests
