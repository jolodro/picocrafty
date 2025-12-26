from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer


def criar_servidor_ftp(pasta, usuario="picocrafty", senha="12345678", host="0.0.0.0", porta=2121):
    authorizer = DummyAuthorizer()
    authorizer.add_user(usuario, senha, pasta, perm="elradfmw")

    handler = FTPHandler
    handler.authorizer = authorizer

    server = FTPServer((host, porta), handler)
    return server  # 🔑 apenas cria e retorna
