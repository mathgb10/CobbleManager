# app/routers/auth.py
import os
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["Autenticação"])

class Login(BaseModel):
    usuario: str
    senha: str

@router.post("/login")
async def login(usuario: Login, request: Request):
    usuario_esp = os.getenv("ADMIN_USERNAME")
    senha_esp = os.getenv("ADMIN_PASSWORD")

    if usuario_esp == usuario.usuario:
        if senha_esp == usuario.senha:
            request.session["usuario"] = usuario.usuario
            return {
                "login": "true",
                "msg": "O login foi realizado com sucesso."
            }
        else:
            raise HTTPException(status_code=401, detail="Senha incorreta.")
    else:
        raise HTTPException(status_code=401, detail="Usuário incorreto.")

@router.post("/logout")
async def logout(request: Request):
    request.session.clear()
    return {"msg": "Logout realizado com sucesso"}