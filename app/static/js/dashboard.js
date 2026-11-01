
const usernameElement = document.getElementById('admin-username');

const statusElement = document.getElementById('server-status');
const playersElement = document.getElementById('server-players');
const tpsElement = document.getElementById('server-tps');

const logoutButton = document.getElementById('logout-button');


async function verificarSessao() {

    const resposta = await fetch('/api/auth/me', {
        credentials: 'same-origin'
    });

    if (!resposta.ok) {
        window.location.href = '/login';
        return false;
    }

    const usuario = await resposta.json();

    usernameElement.textContent = usuario.username;

    return true;
}


async function carregarStatusServidor() {

    try {

        const resposta = await fetch('/api/server/status', {
            credentials: 'same-origin'
        });

        if (!resposta.ok) {
            throw new Error('Não foi possível consultar o servidor.');
        }

        const dados = await resposta.json();

        statusElement.textContent = dados.status;
        playersElement.textContent = dados.players ?? '--';
        tpsElement.textContent = dados.tps ?? '--';

    } catch (error) {

        statusElement.textContent = 'Indisponível';
        console.error(error);

    }
}


async function logout() {

    const resposta = await fetch('/api/auth/logout', {
        method: 'POST',
        credentials: 'same-origin'
    });

    if (resposta.ok) {
        window.location.href = '/login';
    }

}


logoutButton.addEventListener('click', logout);


document.addEventListener('DOMContentLoaded', async () => {

    const autenticado = await verificarSessao();

    if (!autenticado) return;

    await carregarStatusServidor();

});
