// Muda a visibilidade da senha
function viewPass(){
    const btn = document.getElementById("view-pass");
    const inp = document.getElementById("senha");

    if (inp.type === "text") {
        btn.innerHTML = `<i class="bi bi-eye-slash"></i>`
        inp.type = "password"
    } else {
        btn.innerHTML = `<i class="bi bi-eye"></i>`
        inp.type = "text"
    }   
}

document.querySelector(".login-form").addEventListener("submit", async (e)=>{
    e.preventDefault();

    const u = document.getElementById("usuario").value;
    const p = document.getElementById("senha").value;

    try {
        const resp = await fetch("/api/auth/me",{
            method: 'POST',
            headers: {
                'Content-Type':'application/json'
            },
            body: JSON.stringify({
                usuario: u,
                senha: p
            })
        })
    } catch (error){
        return error;
    }
})