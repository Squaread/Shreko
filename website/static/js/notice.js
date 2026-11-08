document.addEventListener("DOMContentLoaded", function () {
    const noticeHTML = `
    <div>
    <strong>AQUI ESTÁ UM AVISO (LEIA ATENTAMENTE) | ANÚNCIO DE EMERGÊNCIA</strong>
    <p>
        Recebemos este aviso e estamos compartilhando para que todos possam ter cuidado. Leia com atenção. Envie para todos os servidores que você participa, 
        pois é muito importante. Não aceite solicitações de amizade de "vidroyous", "dogyous" ou "lucluca2011_.". A foto de perfil deles é de desenho animado
        pra disfarçar e o outro é uam foto de um rato. Esse grupo são de h@ckers/3stpr4drs. Avise a todos da sua lista de amigos, porque se alguém da sua lista
        dicioná-lo, ele aparecerá na sua também. Eles encontrarão seu endereço de IP e endereço do computador, então copie e cole esta mensagem sempre que puder. 
        Ele está enviando solicitações de amizade para usuários aleatórios do Discord, e aqueles que aceitarem terão suas contas e endereços de IP expostos. 
        Compartilhe esta informação e envie para todos os servidores do Discord que puder. Se você vir este usuário, NÃO ACEITE SUA SOLICITAÇÃO DE AMIZADE e
        denuncie-o imediatamente! Tenha cuidado com as solicitações de amizade no Discord. Por favor, copie e cole esta mensagem em outro servidor, 
        para que outras pessoas podessem ver esse aviso.
    </p>
    </div>
    `;
    document.querySelector(".notice-panel").insertAdjacentHTML('beforeend', noticeHTML);
});