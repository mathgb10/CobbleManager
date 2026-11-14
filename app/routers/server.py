import os
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
import docker
from datetime import datetime
from pathlib import Path
import zipfile
from app.dependencies import verificar_login, verifica_docker, docker_client

router = APIRouter(prefix="/api/server", tags=["Servidor Minecraft"])

DATA_DIR = Path("/data")
BKP_DIR = Path("/backups")

class Comando(BaseModel):
    comando: str

@router.get("/status")
def server_status(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
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
            mem_stats = stats.get("memory_stats", {})
            used_memory = mem_stats.get("usage", 0)
            if "stats" in mem_stats and "cache" in mem_stats["stats"]:
                used_memory -= mem_stats["stats"]["cache"]
            
            ram_used_mb = round(used_memory / (1024 * 1024), 2)
            limit_memory = mem_stats.get("limit", 0)
            ram_limit_mb = round(limit_memory / (1024 * 1024), 2)
            if limit_memory > 0:
                ram_percent = round((used_memory / limit_memory) * 100, 1)

            cpu_stats = stats.get("cpu_stats", {})
            precpu_stats = stats.get("precpu_stats", {})
            cpu_delta = cpu_stats.get("cpu_usage", {}).get("total_usage", 0) - precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
            system_delta = cpu_stats.get("system_cpu_usage", 0) - precpu_stats.get("system_cpu_usage", 0)
            online_cpus = cpu_stats.get("online_cpus", len(cpu_stats.get("cpu_usage", {}).get("percpu_usage", [1])))
            
            if system_delta > 0 and cpu_delta > 0:
                cpu_percent = round((cpu_delta / system_delta) * online_cpus * 100.0, 2)
        except Exception:
            pass

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

@router.post("/comando")
def enviar_comando(json: Comando, _ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.reload()
        exec_result = container.exec_run(f"rcon-cli {json.comando}")
        return {
            "sucesso": True,
            "comando": json.comando,
            "saida": exec_result.output.decode("utf-8").strip(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar comando para o Docker: {str(e)}")

@router.get("/logs")
def terminal(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.reload()
        logs_brutos = container.logs(tail=100, timestamps=False).decode("utf-8").splitlines()
        return {"logs": logs_brutos}
    except Exception as e:
        raise HTTPException(status_code=500, detail="Erro ao consultar logs")

@router.post("/stop")
def parar_container(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.stop()
        return {"sucesso": True, "msg": "O Container foi parado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível parar o container, erro: {e}")

@router.post("/start")
def iniciar_container(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.start()
        return {"sucesso": True, "msg": "O Container foi iniciado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível iniciar o container, erro: {e}")

@router.post("/restart")
def restart_container(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.restart()
        return {"sucesso": True, "msg": "O Container foi reiniciado com sucesso"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Não foi possível reiniciar o container, erro: {e}")

@router.post("/bkp")
def backup(_ = Depends(verificar_login), _1 = Depends(verifica_docker)):
    try:
        container = docker_client.containers.get("cobbleverse")
        container.reload()

        # 1. Força o servidor a salvar o mundo na RAM para o disco
        try:
            container.exec_run("rcon-cli save-all")
        except Exception:
            pass

        # 2. Garante que a pasta de backups existe
        BKP_DIR.mkdir(parents=True, exist_ok=True)

        # 3. Nome único com data e hora
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        zip_path = BKP_DIR / f"cobbleverse_backup_{timestamp}.zip"

        # 4. Seleciona apenas o que é essencial para o backup (ignora mods, libs e caches gigantescos)
        itens_essenciais = [
            "world", 
            "config", 
            "datapacks", 
            "server.properties", 
            "ops.json", 
            "whitelist.json", 
            "usercache.json",
            "banned-ips.json",
            "banned-players.json"
        ]

        # 5. Compacta de forma inteligente e super rápida
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for item_nome in itens_essenciais:
                item_path = DATA_DIR / item_nome
                if item_path.is_dir():
                    for subfile in item_path.rglob("*"):
                        if subfile.is_file():
                            zipf.write(subfile, subfile.relative_to(DATA_DIR))
                elif item_path.is_file():
                    zipf.write(item_path, item_path.relative_to(DATA_DIR))

        return {
            "sucesso": True,
            "msg": "Backup gerado com sucesso!",
            "arquivo": f"data/backups/cobbleverse_backup_{timestamp}.zip"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar backup: {str(e)}")