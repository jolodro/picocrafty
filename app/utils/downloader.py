import os
import requests
import zipfile, tarfile, io


MANIFEST_URL_JAVA = "https://piston-meta.mojang.com/mc/game/version_manifest.json"
MANIFEST_URL_BEDROCK = "https://raw.githubusercontent.com/kittizz/bedrock-server-downloads/main/bedrock-server-downloads.json"

def baixar_servidor_java(versao, pasta):
    manifest = requests.get(MANIFEST_URL_JAVA).json()

    versao_info = next(v for v in manifest["versions"] if v["id"] == versao)
    version_data = requests.get(versao_info["url"]).json()

    server_url = version_data["downloads"]["server"]["url"]

    destino = os.path.join(pasta, "server.jar")
    with open(destino, "wb") as f:
        f.write(requests.get(server_url).content)

    return destino

def versoes():
    manifest_J = requests.get(MANIFEST_URL_JAVA).json()
    manifest_B = requests.get(MANIFEST_URL_BEDROCK).json()

    versoes_J = []
    versoes_B = []

    #JAVA MANIFEST
    for vj in manifest_J["versions"]:
        if vj['type'] == 'release':
            versoes_J.append(vj['id'])
    
    #BEDROCK MANIFEST
    for vb in manifest_B['release']:
        versoes_B.append(vb)
    
    return {"java":versoes_J, "bedrock":versoes_B}

def baixar_servidor_bedrock(versao, pasta):

    manifest_B = requests.get(MANIFEST_URL_BEDROCK).json()
    
    server_url = manifest_B['release'][versao]['linux']['url']
    
    try:
        response = requests.get(server_url, stream=True, headers={"User-Agent": "Mozilla/5.0"})
    except:
        return False
    response.raise_for_status()

    conteudo = io.BytesIO(response.content)
    
    with zipfile.ZipFile(conteudo) as zip_ref:
        zip_ref.extractall(pasta)
    
    return True