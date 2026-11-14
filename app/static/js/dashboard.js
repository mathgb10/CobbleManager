function atualizarRelogio() {
    const agora = new Date();

    const h = agora.getHours().toString().padStart(2, '0');
    const m = agora.getMinutes().toString().padStart(2, '0');

    const horarioFormatado = `${h}:${m}`;
    document.getElementById('relogio').innerText = horarioFormatado;
}

// Ao clicar no botão de logout, chamo a função de encerrar sessão
document.getElementById("logout-btn").addEventListener("click", async () => {
    try {
        const resp = await fetch("/api/auth/logout", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })

        if (!resp.ok) {
            alerta("Erro ao tentar realizar o logout.");
        }

        window.location.href = "/";
    } catch (error) {
        console.log("Error: ", error);
        alert("Erro ao tentar deslogar.");
    }
})

// Função que da fetch na rota de API do servidor e retorna os dados
async function getInfos(rota) {
    const api = `/api/server/${rota}`;

    try {
        const resp = await fetch(api)

        if (!resp.ok) {
            alert("Erro ao tentar consultar dados da rota: " + rota)
            return;
        }

        const data = await resp.json();
        return data;
    } catch (error) {
        console.log("Error: ", error);
        alert("Erro ao tentar consultar dados.")
    }

}

// Variável global para armazenar a instância do gráfico
let ramChartInstance = null;
let cpuChartInstance = null;

function criarGraficoRam(usadoMb, limiteMb) {
    const ctx = document.getElementById('ramChart').getContext('2d');
    const livreMb = Math.max(0, limiteMb - usadoMb);

    if (ramChartInstance) {
        // Se o gráfico já existe, apenas atualiza os dados (evita duplicação)
        ramChartInstance.data.datasets[0].data = [usadoMb, livreMb];
        ramChartInstance.update();
        return;
    }

    // Cria o gráfico pela primeira vez
    ramChartInstance = new Chart(ctx, {
        type: 'doughnut', // Gráfico de rosca
        data: {
            labels: ['Usado (MB)', 'Livre (MB)'],
            datasets: [{
                data: [usadoMb, livreMb],
                backgroundColor: ['rgba(0, 255, 102, 0.2)', '#00ff66'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });
}

const maxHistoricoCpu = 10; // Quantos pontos de histórico ficam na tela
const historicoCpu = {
    labels: [],
    dados: []
};

function criarGraficoCpu(cpuPercentAtual) {
    const ctx = document.getElementById('cpuChart').getContext('2d');

    // Pega o horário atual para colocar no eixo X
    const agora = new Date().toLocaleTimeString();

    // Adiciona os novos dados no histórico
    historicoCpu.labels.push(agora);
    historicoCpu.dados.push(cpuPercentAtual);

    // Mantém apenas os últimos X registros para o gráfico não ficar gigante
    if (historicoCpu.labels.length > maxHistoricoCpu) {
        historicoCpu.labels.shift();
        historicoCpu.dados.shift();
    }

    if (cpuChartInstance) {
        // Atualiza os dados do gráfico existente
        cpuChartInstance.data.labels = historicoCpu.labels;
        cpuChartInstance.data.datasets[0].data = historicoCpu.dados;
        cpuChartInstance.update();
        return;
    }
    // Cria o gráfico de linha pela primeira vez
    cpuChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: historicoCpu.labels,
            datasets: [{
                label: 'CPU %',
                data: historicoCpu.dados,
                borderColor: '#00ff66',
                backgroundColor: 'rgba(0, 255, 102, 0.2)',
                borderWidth: 2,
                fill: true,
                tension: 0.3 // Deixa a linha curvada e suave
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    suggestedMax: 100 // Escala de 0% a 100%
                }
            },
            plugins: {
                legend: {
                    display: false
                }
            }
        }
    });
}

// Adiciono alguns valores a sidebar
function setSidebar(v1, v2, v3) {
    const places = {
        // Places de Sidebar
        dominio: document.getElementById("dominio"),
        atual_players: document.getElementById("atual_play"),
        max_players: document.getElementById("max_play")
    }

    // Sidebar
    places.dominio.innerHTML = v1
    places.atual_players.innerHTML = v2
    places.max_players.innerHTML = v3
}

// Adiciono os dados em seus placeholders
async function setContent(tela) {
    let data;

    // Chamo a função que adicionara alguns valores a certos placeholders na sidebar
    switch (tela) {
        case 'dashboard':
            data = await getInfos('status');
            setSidebar(data.dominio, data.jogadores.atual, data.jogadores.max)
            var places = {
                //Header
                header: document.getElementById("pagina"),
                // Cards
                nome: document.getElementById("nome"),
                status: document.getElementById("status"),
                saude: document.getElementById("saude"),
                // Logs
                logs: document.getElementById("logs")
            }

            // Header
            places.header.innerHTML = tela

            // Cards
            places.nome.innerHTML = data.nome
            places.status.innerHTML = data.status
            places.saude.innerHTML = data.saude

            if (data.status == "running") {
                document.querySelector(".card-status").classList.add("ok")
            }

            if (data.saude == "healthy") {
                document.querySelector(".card-saude").classList.add("ok")
            }

            // Gráficos
            criarGraficoRam(data.hardware.ram_used_mb, data.hardware.ram_limit_mb);
            criarGraficoCpu(data.hardware.cpu_percent);

            // Logs
            places.logs.innerHTML = null;
            data.logs.forEach(e => {
                places.logs.innerHTML = places.logs.innerHTML += `<p>${e}</p>`;
            });
            break;
        case 'console':
            data = await getInfos('logs')
            var places = {
                // Logs
                logs: document.getElementById("logs")
            }

            if (places.logs.innerHTML.length > 100) {
                places.logs.innerHTML = null;
            }

            data.logs.forEach(e => {
                places.logs.innerHTML = places.logs.innerHTML += `<p>${e}</p>`;
            })

            break;
        default:
            break;
    }
}

// Preparo a tela (placeholders para os dados)
async function setScreen(tela) {
    switch (tela) {
        case 'dashboard':
            // Header
            document.getElementById("pagina").innerHTML = tela;
            document.querySelector(".content").innerHTML = `
                <div class="cards">
                    <div class="card card-nome">
                        <h2>Nome</h2>
                        <span id="nome">...</span>
                    </div>
                    <div class="card card-status">
                        <h2>Status</h2>
                        <span id="status">...</span>
                    </div>
                    <div class="card card-saude">
                        <h2>Saude</h2>
                        <span id="saude">...</span>
                    </div>
                </div>
                <div class="hardware-cards">
                    <div class="card grafico" style="width: 48%;">
                        <h2>RAM</h2>
                        <canvas id="ramChart"></canvas>
                    </div>
                    <div class="card grafico" style="width: 48%;">
                        <h2>CPU</h2>
                        <canvas id="cpuChart"></canvas>
                    </div>
                </div>
                <div class="logs-box card">
                    <div class="logs-header">
                        <h2>Últimos Logs</h2>
                    </div>
                    <div class="logs-card" id="logs">
                        ...
                    </div>
                </div>
            `
            break;
        case 'console':
            // Header
            document.getElementById("pagina").innerHTML = tela;
            document.querySelector(".content").innerHTML = `
                <div class="logs-box terminal card">
                    <div class="logs-header">
                        <h2>Terminal</h2>
                    </div>
                    <div class="overflow">
                        <div class="logs-card" id="logs">
                        ...
                        </div>
                    </div>
                    <form class="form">
                        <div class="body-form">
                            <label for="comando">></label>
                            <div class="input-box">
                                <input class="input" type="text" name="comando" id="comando"/>
                                <button type="submit">Enviar</button>
                            </div>
                        </div>
                    </form>
                </div>
            `;
            break;
        case 'painel':
            // Header
            document.getElementById("pagina").innerHTML = tela;
            document.querySelector(".content").innerHTML = `
                <div class="btns-header">
                    <button id="iniciar" onclick="action('iniciar')" class="btn-action">
                        <i class="bi bi-play-fill"></i> Iniciar
                    </button>
                    <button id="parar" onclick="action('parar')" class="btn-action">
                        <i class="bi bi-stop-fill"></i> Parar
                    </button>
                    <button id="reiniciar" onclick="action('reiniciar')" class="btn-action">
                        <i class="bi bi-arrow-repeat"></i> Reiniciar
                    </button>
                    <button id="backup" onclick="action('backup')" class="btn-action">
                        <i class="bi bi-cloud-arrow-up"></i> Backup
                    </button>
                </div>
            `;
            break;
        default:
            break;
    }
}

let intervalo = null;
function getRoute() {
    const url = new URLSearchParams(window.location.search);
    const tela = url.get('screen') || 'dashboard';

    const btns = document.querySelectorAll(".link")
    var tela1;

    btns.forEach(e => {
        const conteudo = e.getAttribute("data-links").toLowerCase();
        if (conteudo == tela) {
            e.classList.add("ativo");
            tela1 = conteudo;
        } else {
            e.classList.remove("ativo");
        };
    });
    setScreen(tela1);
    setContent(tela1);

    if (intervalo) clearInterval(intervalo);
    intervalo = setInterval(() => setContent(tela1), 5000);
}

document.querySelectorAll('.link').forEach(e => {
    e.addEventListener('click', () => {
        const destino = e.getAttribute("data-links").toLowerCase();
        history.pushState({}, '', `?screen=${destino}`);
        getRoute(); // Reconfigura para a nova tela
    });
});

window.onload = () => {
    getRoute();
    // Atualiza o relógio a cada 1000ms (1 segundo)
    setInterval(atualizarRelogio, 1000);
    atualizarRelogio();
}

async function action(x) {
    const acao = x; // Vai retornar 'iniciar', 'parar' ou 'reiniciar'

    // Aqui você pode direcionar para a API correspondente com base no ID:
    try {
        let endpoint = "";
        if (acao === "parar") endpoint = "/api/server/stop";
        if (acao === "reiniciar") endpoint = "/api/server/restart";
        if (acao === "iniciar") endpoint = "/api/server/start"; // (caso crie a rota depois)
        if (acao === "backup") endpoint = "/api/server/bkp"; // (caso crie a rota depois)

        if (!endpoint) return;

        const resp = await fetch(endpoint, { method: 'POST' });
        const data = await resp.json();

        if (!resp.ok) {
            alert(data.detail || "Erro ao executar ação.");
            return;
        }

        alert(data.msg || "Ação executada com sucesso!");
    } catch (error) {
        console.log("Erro: ", error);
        alert("Erro ao tentar comunicar com o servidor.");
    }
}

// Captura o submit de qualquer formulário na página de forma segura
document.addEventListener("submit", async (e) => {
    // Se o formulário enviado não for o do comando, ignora
    if (!e.target.classList.contains("form")) return;

    e.preventDefault(); // Impede o recarregamento padrão da página

    const inputComando = document.getElementById("comando");
    if (!inputComando) return;

    const c = inputComando.value.trim();
    if (!c) return;

    try {
        const resp = await fetch("/api/server/comando", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ comando: c })
        });

        if (!resp.ok) {
            const errorData = await resp.json();
            alert(errorData.detail);
            return;
        }

        // Limpa o input e atualiza os logs na hora
        inputComando.value = "";
        setContent('console');

    } catch (error) {
        console.log("Error: ", error);
        alert("Erro ao tentar executar comando.");
    }
});
