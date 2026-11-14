# Carregando .env
import os
from dotenv import load_dotenv

from pathlib import Path

# FastAPI
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles  import StaticFiles
from fastapi.responses import RedirectResponse, FileResponse

# Middleware de Sessão do FastAPI => session_start do PHP
from starlette.middleware.sessions import SessionMiddleware

# BaseModel para validar JSON
from pydantic import BaseModel

# Docker
import docker

# Inicializa o cliente do Docker (ele conversa automaticamente com o Docker Desktop no Windows/Linux/Mac)
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Aviso: Não foi possível conectar ao Docker: {e}")
    docker_client = None

app = FastAPI(title="Cobbleverse API")

# Adicionando Middleware da Sessão
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))

# Configuração de Arquivos estáticos
app.mount("/static",StaticFiles(directory="app/static",html=True),name="static")

BASE_DIR = Path(__file__).resolve().parent

# Válida se o usuário está logado
def verificar_login(request: Request):
    if "usuario" not in request.session:
        raise HTTPException(status_code=401, detail="Não autorizado.")

# Válida se o Docker está rodando
def verifica_docker():
    if docker_client is None:
        raise HTTPException(status_code=500, detail="Cliente do Docker não disponível.")

# Tela de Login
@app.get("/login")
def login_page(request: Request):
    if "usuario" in request.session:
        return RedirectResponse(url="/dashboard",status_code=status.HTTP_303_SEE_OTHER)
        
    return FileResponse(path=BASE_DIR / "static/login.html")

# Tela de Dashboard
@app.get("/dashboard")
def dashboard_page(request: Request):
    if "usuario" not in request.session:
        return RedirectResponse(url="/login",status_code=status.HTTP_303_SEE_OTHER)
        
    return FileResponse(path=BASE_DIR / "static/dashboard.html")

# Rota principal
@app.get("/")
def principal(request: Request):
    # Caso a sessão não exista mando o usuário para tela de login
    if "usuario" in request.session:
        return RedirectResponse(url="/dashboard",status_code=status.HTTP_303_SEE_OTHER)
    else:
        return RedirectResponse(url="/login",status_code=status.HTTP_303_SEE_OTHER)
    
# Login e Logout
class Login(BaseModel):
    usuario: str
    senha: str

# Login
@app.post("/api/auth/login")
async def login(usuario:Login, request: Request):
    # Valores esperados
    usuario_esp = os.getenv("ADMIN_USERNAME")
    senha_esp = os.getenv("ADMIN_PASSWORD")

    # Valida o Login
    if usuario_esp == usuario.usuario:
        if senha_esp == usuario.senha:
            # Criando a sessão
            request.session["usuario"] = usuario.usuario

            return {
                "login":"true",
                "msg":"O login foi realizado com sucesso."
            }
    # Retorno erro 401 e uma mensagem de erro
        else:
            raise HTTPException(status_code=401, detail="Senha incorreta.")
    else:
        raise HTTPException(status_code=401, detail="Usuário incorreto.")

# Logout
@app.post("/api/auth/logout")
async def logout(request: Request):
    # Limpo a sessão
    request.session.clear()
    return {
        "msg":"Logout realizado com sucesso"
    }

# Servidor

# Todos os dados do container - TEMPORARIO
@app.get("/api/server/tmp")
def server_status(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.reload()

        attrs = container.attrs

        return {
            "data": attrs
        }

    except docker.errors.NotFound:
        return {
            "status": "not_found",
            "message": "O container do containercontainer de Minecraft não foi encontrado."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao consultar o Docker: {str(e)}")
    
# Status do servidor
@app.get("/api/server/status")
def server_status(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        # Escolho o container
        container = docker_client.containers.get("cobbleverse")
        container.reload()
        attrs = container.attrs

        # Saúde
        health_status = "N/A"
        health_logs = []
        if "State" in attrs and "Health" in attrs["State"]:
            health_status = attrs["State"]["Health"].get("Status", "Desconhecido")
            health_logs = attrs["State"]["Health"].get("Log", [])

        # Players ativos
        jogadores_online = 0
        max_jogadores = 20
        if health_logs:
            ultimo_output = health_logs[-1].get("Output", "")
            if "online=" in ultimo_output:
                try:
                    partes = ultimo_output.split("online=")[1]
                    jogadores_online = int(partes.split(" ")[0])
                    max_partes = ultimo_output.split("max=")[1]
                    max_jogadores = int(max_partes.split(" ")[0])
                except Exception:
                    pass

        # Hardware
        ram_used_mb = 0
        ram_limit_mb = 0
        ram_percent = 0
        cpu_percent = 0.0

        try:
            stats = container.stats(stream=False)
            
            # RAM
            mem_stats = stats.get("memory_stats", {})
            used_memory = mem_stats.get("usage", 0)
            if "stats" in mem_stats and "cache" in mem_stats["stats"]:
                used_memory -= mem_stats["stats"]["cache"]
            
            ram_used_mb = round(used_memory / (1024 * 1024), 2)
            limit_memory = mem_stats.get("limit", 0)
            ram_limit_mb = round(limit_memory / (1024 * 1024), 2)
            if limit_memory > 0:
                ram_percent = round((used_memory / limit_memory) * 100, 1)

            # CPU Cálculo seguro
            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
            online_cpus = cpu_stats.get("online_cpus", len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", [1])))
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = round((cpu_delta / system_delta) * online_cpus * 100.0, 2)
        except Exception:
            pass

        # Logs
        logs_brutos = container.logs(tail=10, timestamps=False).decode("utf-8").splitlines()

        return {
            "nome": container.name,
            "status": container.status,
            "saude": health_status,
            "hardware": {
                "cpu_percent": cpu_percent,
                "ram_used_mb": ram_used_mb,
                "ram_limit_mb": ram_limit_mb,
                "ram_percent": ram_percent
            },
            "jogadores": {
                "atual": jogadores_online,
                "max": max_jogadores
            },
            "logs": logs_brutos,
            "dominio": os.getenv("DOMAIN")
        }

    except docker.errors.NotFound:
        return {"status": "not_found", "message": "Container não encontrado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Enviar comando ao servidor
class Comando(BaseModel):
    comando: str

@app.post("/api/server/comando")
def enviar_comando(json: Comando, _ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.reload()

        # Envia o comando para o container
        exec_result = container.exec_run(f"rcon-cli {json.comando}")

        return {
            "sucesso": True,
            "comando": json.comando,
            "saida": exec_result.output.decode("utf-8").strip(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar comando para o Docker: {str(e)}")

@app.get("/api/server/logs")
def terminal(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        # Escolho o container
        container = docker_client.containers.get("cobbleverse")
        container.reload()
        # Logs
        logs_brutos = container.logs(tail=100, timestamps=False).decode("utf-8").splitlines()
        return {
            "logs": logs_brutos,
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail="Erro ao consultar logs")

# Para o container
@app.post("/api/server/stop")
def parar_container(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.stop()

        return {
            "sucesso": True,
            "msg": "O Container foi parado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Não foi possível parar o container, erro:${e}")

# Incia o container
@app.post("/api/server/start")
def iniciar_container(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.start()

        return {
            "sucesso": True,
            "msg": "O Container foi iniciado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Não foi possível iniciar o container, erro:${e}")

# Reinica o container
@app.post("/api/server/restart")
def restart_container(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.restart()

        return {
            "sucesso": True,
            "msg": "O Container foi reinicado com sucesso"
        }
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Não foi possível reiniciar o container, erro:${e}")