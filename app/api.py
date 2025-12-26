import os
import shutil
import threading

from flask import jsonify, render_template, request, Blueprint
from .models import Servidor, Configuracao, db
from app import app
from app.config import BASE_DIR
from app.utils.ftp import criar_servidor_ftp
from .api_server.manager import start_server, stop_server, get_status, get_logs, send_command

api_bp = Blueprint('api', __name__)

ftp_server = None
ftp_thread = None


def _run_ftp():
    global ftp_server
    ftp_server.serve_forever()


@api_bp.route("/configuracoes", methods=["POST"])
def salvar_configuracoes():
    global ftp_server, ftp_thread

    data = request.json

    config = Configuracao.query.first()
    if not config:
        config = Configuracao()

    config.ftp_ativo = data.get("ftp_ativo", False)

    db.session.add(config)
    db.session.commit()

    if config.ftp_ativo:
        print("FTP ATIVADO")

        if not ftp_server:
            ftp_server = criar_servidor_ftp(f"{BASE_DIR}/servers")

            ftp_thread = threading.Thread(
                target=_run_ftp,
                daemon=True
            )
            ftp_thread.start()

    else:
        print("FTP DESATIVADO")

        if ftp_server:
            ftp_server.close_all()
            ftp_server = None
            ftp_thread = None

    return jsonify({"msg": "Configurações salvas com sucesso"})

@api_bp.route("/servidores")
def servidores():
    dados = Servidor.query.all()
    servidores = [servidor.to_dict() for servidor in dados]
    return jsonify(servidores)

@api_bp.route('/servidores/<int:id>', methods=['DELETE'])
def deletar_servidor(id):
    servidor = Servidor.query.get(id)

    if not servidor:
        return jsonify({"sucesso": False}), 404
    
    if get_status(id)["running"] != False:
        return jsonify({"sucesso": False}), "Servidor Rodando"
    
    if os.path.isdir(servidor.path):
        shutil.rmtree(servidor.path)
    
    db.session.delete(servidor)
    db.session.commit()

    return jsonify({"sucesso": True})


@api_bp.route("/servidor/<int:id>/start", methods=["POST"])
def api_start_servidor(id):
    servidor = Servidor.query.get_or_404(id)

    start_server(id)

    servidor.status = "rodando"
    db.session.commit()

    return jsonify({"success": True})


@api_bp.route("/servidor/<int:id>/stop", methods=["POST"])
def api_stop_servidor(id):
    servidor = Servidor.query.get_or_404(id)

    stop_server(id)

    servidor.status = "parado"
    db.session.commit()

    return jsonify({"success": True})


@api_bp.route("/servidor/<int:id>/status")
def api_status_servidor(id):
    status = get_status(id)
    return jsonify(status or {})

@api_bp.route("/servidor/<int:id>/logs")
def api_logs(id):
    return jsonify(get_logs(id))

@api_bp.route("/servidor/<int:id>/command", methods=["POST"])
def api_command(id):
    data = request.get_json()
    cmd = data.get("cmd")

    if not cmd:
        return {"error": "Comando vazio"}, 400

    if not send_command(id, f"/{cmd}"):
        return {"error": "Servidor não encontrado"}, 404

    return {"success": True}