import psutil
from app.api_server.minecraft import MinecraftServer  # assume minecraft.py exporta MinecraftServer
from app.models import Servidor, Configuracao, db

servers = {}


def load_servers_from_db():
    servidores = Servidor.query.all()
    config = Configuracao.query.first()
    if not config:
        config = Configuracao()

    config.ftp_ativo = False

    db.session.add(config)
    db.session.commit()

    for s in servidores:
        # s.tipo deve ser "java" ou "bedrock"
        if getattr(s, "tipo", "java").lower() == "bedrock":
            servers[s.id] = MinecraftServer(
                server_path=s.path,
                jar=None,
                ram_mb=0,
                port=s.porta,
                server_type="bedrock",
                executable=getattr(s, "executable", "./bedrock_server")
            )
        else:
            servers[s.id] = MinecraftServer(
                server_path=s.path,
                jar=getattr(s, "jar", "server.jar"),
                ram_mb=s.ram * 1024,
                port=s.porta,
                server_type="java"
            )

        # Verificar se estava rodando antes
        if s.pid and psutil.pid_exists(s.pid):
            servers[s.id].pid = s.pid
            servers[s.id].start_time = s.start_time
        else:
            s.status = "parado"
            s.pid = None

    # commit caso tenhamos mudado algo em s
    db.session.commit()


def add_server(s):
    if getattr(s, "tipo", "java").lower() == "bedrock":
        servers[s.id] = MinecraftServer(
            server_path=s.path,
            jar=None,
            ram_mb=0,
            port=s.porta,
            server_type="bedrock",
            executable=getattr(s, "executable", "./bedrock_server")
        )
    else:
        servers[s.id] = MinecraftServer(
            server_path=s.path,
            jar=getattr(s, "jar", "server.jar"),
            ram_mb=s.ram * 1024,
            port=s.porta,
            server_type="java"
        )

    if s.pid and psutil.pid_exists(s.pid):
        servers[s.id].pid = s.pid
        servers[s.id].start_time = s.start_time
    else:
        s.status = "parado"
        s.pid = None
        db.session.commit()


def start_server(server_id):
    server = servers.get(server_id)
    servidor_db = Servidor.query.get(server_id)

    if not server or server.is_running():
        return False

    ok = server.start()
    if not ok:
        return False

    servidor_db.pid = server.pid
    servidor_db.status = "rodando"
    servidor_db.start_time = server.start_time
    db.session.commit()

    return True


def stop_server(server_id):
    server = servers.get(server_id)
    servidor_db = Servidor.query.get(server_id)

    if not server or not server.is_running():
        return False

    ok = server.stop()
    if not ok:
        return False

    servidor_db.pid = None
    servidor_db.status = "parado"
    servidor_db.start_time = None
    db.session.commit()

    return True


def get_status(server_id):
    server = servers.get(server_id)
    if not server:
        return None
    return server.status()


def get_logs(server_id):
    server = servers.get(server_id)
    if not server:
        return []
    return server.logs


def send_command(server_id, cmd):
    server = servers.get(server_id)
    if not server:
        return False
    try:
        server.send_command(cmd)
    except Exception:
        return False
    return True
