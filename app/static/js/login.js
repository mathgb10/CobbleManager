// Muda a visibilidade da senha
function viewPass(){
    const btn = document.getElementById("view-pass");
    const inp = document.getElementById("senha");

    // Caso o input seja do tipo text, mudo o icon e altero o tipo para password
    // Caso contrário altero o tipo para text e mudo o icon
    if (inp.type === "text") {
        btn.innerHTML = `<i class="bi bi-eye-slash"></i>`
        inp.type = "password"
    } else {
        btn.innerHTML = `<i class="bi bi-eye"></i>`
        inp.type = "text"
    }   
}

// Quando o usuário clicar no botão de login, o evento  na chamar uma função assíncrona
// Que realizará a validação do login
document.querySelector(".login-form").addEventListener("submit", async (e)=>{
    e.preventDefault();

    // Valores dos inputs
    const u = document.getElementById("usuario").value;
    const p = document.getElementById("senha").value;

    try {
        // Envia o payload para rota de login
        const resp = await fetch("/api/auth/login",{
            method: 'POST',
            headers: {
                'Content-Type':'application/json'
            },
            body: JSON.stringify({
                usuario: u,
                senha: p
            })
        })

        // Caso aconteça algum erro vou exibir uma mensagem ao usuário
        if (!resp.ok){
            const errorData = await resp.json();
            alert(errorData.detail);
            return;
        }

        // Se o login for realizado com sucesso, vou mandar ele para rota principal
        // Aonde trato se ele está logado ou não
        const dados = await resp.json();

        window.location.href = "/";
    } catch (error){
        // Caso aconteça algum erro ao realizar o fetch vou exibir ao usuário
        console.log("Error: ",error);
        alert("Erro ao tentar logar.");
    }
})