import os
from fastapi import HTTPException, Request
# Docker
import docker

# Inicializa o cliente do Docker (ele conversa automaticamente com o Docker Desktop no Windows/Linux/Mac)
try:
    docker_client = docker.from_env()
except Exception as e:
    print(f"Aviso: Não foi possível conectar ao Docker: {e}")
    docker_client = None

# Válida se o usuário está logado
def verificar_login(request: Request):
    if "usuario" not in request.session:
        raise HTTPException(status_code=401, detail="Não autorizado.")

# Válida se o Docker está rodando
def verifica_docker():
    if docker_client is None:
        raise HTTPException(status_code=500, detail="Cliente do Docker não disponível.")
