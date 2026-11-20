import os
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import docker
from pathlib import Path
import json
from app.dependencies import verificar_login, verifica_docker, docker_client
from app.routers.server import enviar_comando

router = APIRouter(prefix="/api/server", tags=["Servidor Minecraft"])

DATA_DIR = Path("/data")

@router.get("/players")
def players(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        caminho = DATA_DIR/"usercache.json"
        caminho2 = DATA_DIR/"ops.json"
        
        with open(caminho, "r", encoding="utf-8") as arq:
            dados = json.load(arq)

        with open(caminho2, "r", encoding="utf-8") as arq:
            dados2 = json.load(arq)

        # Permissões
        perm_form = {} # Dicionário
        for i in dados2:
            perm_form[i.get("uuid")] = {
                "level":i.get("level"),
                "bypass":i.get("bypassesPlayerLimit")
            }

        # Jogadores
        players_form = []
        for i in dados:
            name = i.get("name")
            uuid = i.get("uuid")

            permissao = perm_form.get(uuid)

            players_form.append({
                "name": name,
                "uuid": uuid,
                "skin": f"https://crafthead.net/avatar/{uuid}",
                "op": permissao is not None,
                "level": permissao.get("level") if permissao else 0,
                "bypass": permissao.get("bypass") if permissao else False
            })


        return {
            "sucesso": True,
            "msg": "Arquivo lido com sucesso.",
            "dados": players_form
        }
    except Exception as e: 
        raise HTTPException(status_code=500,detail=f"Erro ao acessar usercache.json, erro: {e}")

class Op(BaseModel):
    name: str
    op: bool

@router.post("/players/op")
def mudar_permissao(req: Op,_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        permissao = "op" if req.op else "deop"
        comando = f"{permissao} {req.name}"

        container = docker_client.containers.get("cobbleverse")
        container.reload()
        exec_result = container.exec_run(f"rcon-cli {comando}")

        return {
            "sucesso": True,
            "msg": exec_result
        }
    except Exception as e: 
        raise HTTPException(status_code=500,detail=f"Erro ao acessar executar comando, erro: {e}")
