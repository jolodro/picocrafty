import os
import uuid

from app import app
from app.config import PATH_SERVERS
from .utils.eula import criar_eula
from .utils.downloader import baixar_servidor_java, baixar_servidor_bedrock, versoes
from .models import Servidor, Configuracao, db
from .api_server.manager import add_server
from flask import render_template, request, redirect, jsonify



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/config')
def configuracoes():
    config = Configuracao.query.first()
    ftp_ativo = config.ftp_ativo if config else False
    return render_template("configuracoes.html", ftp_ativo=ftp_ativo)

@app.route('/criar_servidor', methods=['GET', 'POST'])
def criar_servidor():
    if request.method == 'POST':
        while True:
            nome_pasta = str(uuid.uuid4())[:8]  # nome curto e aleatório
            caminho = os.path.join(PATH_SERVERS, nome_pasta)

            if not os.path.exists(caminho):
                os.makedirs(caminho)
                break

        nome = request.form['nome']
        tipo = request.form['tipo']
        versao = request.form['versao']
        ram = int(request.form['ram'])
        porta = int(request.form['porta'])
        path = caminho

        servidor = Servidor(
            path=caminho,
            nome=request.form['nome'],
            tipo=request.form['tipo'],
            versao=request.form['versao'],
            ram=int(request.form['ram']),
            porta=int(request.form['porta'])
        )


        db.session.add(servidor)
        db.session.commit()

        if tipo == "java":
            baixar_servidor_java(versao, path)
        elif tipo == "bedrock":
            baixar_servidor_bedrock(versao, path)

        criar_eula(path)
        
        add_server(servidor)

        return redirect(f'/painel_informacoes/{servidor.id}')

    return render_template('criar_servidor.html', versoes=versoes())

@app.route('/painel_informacoes/<int:id>')
def painel_informacoes_id(id):
    servidor = Servidor.query.get_or_404(id)
    return render_template(
        'painel_informacoes_id.html',
        servidor=servidor
    )

@app.route("/servidores")
def servidores_web():
    return render_template("servidores.html")

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('404.html'), 404