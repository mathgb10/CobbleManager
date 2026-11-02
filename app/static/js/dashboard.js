function atualizarRelogio() {
  const agora = new Date();
  
  const h = agora.getHours().toString().padStart(2, '0');
  const m = agora.getMinutes().toString().padStart(2, '0');
  const s = agora.getSeconds().toString().padStart(2, '0');
  
  const horarioFormatado = `${h}:${m}:${s}`;
  document.getElementById('relogio').innerText = horarioFormatado;
}

// Atualiza o relógio a cada 1000ms (1 segundo)
setInterval(atualizarRelogio, 1000);

// Executa imediatamente ao carregar a página
atualizarRelogio();

// Ao clicar no botão de logout, chamo a função de encerrar sessão
document.getElementById("logout-btn").addEventListener("click", async () => {
    try {
        const resp = await fetch("/api/auth/logout",{
            method: 'POST',
            headers: {
                'Content-Type':'application/json'
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