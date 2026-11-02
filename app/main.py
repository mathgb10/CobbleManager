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

app = FastAPI(title="Cobbleverse API")

# Adicionando Middleware da Sessão
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET"))

# Configuração de Arquivos estáticos
app.mount("/static",StaticFiles(directory="app/static",html=True),name="static")

BASE_DIR = Path(__file__).resolve().parent

# Status da API
@app.get("/api/status")
async def health():
    return{
        "status":"ok"
    }

@app.get("/login")
def login_page(request: Request):
    if "usuario" in request.session:
        return RedirectResponse(url="/dashboard",status_code=status.HTTP_303_SEE_OTHER)
        
    return FileResponse(path=BASE_DIR / "static/login.html")

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

# Status do servidor
@app.get("/api/server/status")
def server_status(request: Request):
    if not "usuario" in request.session:
        raise HTTPException(status_code=401, detail="Não autorizado.")

    
