import os

def criar_eula(server_path):
    eula_path = os.path.join(server_path, "eula.txt")

    with open(eula_path, "w") as f:
        f.write("eula=true\n")