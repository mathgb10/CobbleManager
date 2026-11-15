import os
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import docker
from pathlib import Path
import json
from app.dependencies import verificar_login, verifica_docker, docker_client

router = APIRouter(prefix="/api/server", tags=["Servidor Minecraft"])

DATA_DIR = Path("/data")

@router.get("/players")
def players(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        caminho = DATA_DIR/"usercache.json"
        with open(caminho, "r", encoding="utf-8") as arq:
            dados = json.load(arq)

        dados_form = []
        for i in dados:
            name = i.get("name")
            uuid = i.get("uuid")

            dados_form.append({
                "name": name,
                "uuid": uuid,
                "skin": f"https://crafthead.net/avatar/{uuid}"
            })
        return {
            "sucesso": True,
            "msg": "Arquivo lido com sucesso.",
            "dados": dados_form
        }
    except Exception as e: 
        raise HTTPException(status_code=500,detail=f"Erro ao acessar usercache.json, erro: {e}")