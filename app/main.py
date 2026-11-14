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

from app.routers import auth, server

app.include_router(auth.router)
app.include_router(server.router)