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

// Coloco na tela as informações de acordo com a tela
async function setScreen(tela) {
    const data = await getInfos('status');
    switch (tela) {
        case 'dashboard':
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
            const places = {
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
        default:
            break;
    }

    // Chamo a função que adicionara alguns valores a certos placeholders na sidebar
    setSidebar(data.dominio, data.jogadores.atual, data.jogadores.max)
}

// Atualiza a tela com as informações
setInterval(() => setScreen('dashboard'), 5000);
setScreen('dashboard');

// Atualiza o relógio a cada 1000ms (1 segundo)
setInterval(atualizarRelogio, 1000);
atualizarRelogio();