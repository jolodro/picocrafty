import os
import subprocess
import psutil
import time
import threading

LOG_LIMIT = 500

class MinecraftServer:
    """
    Classe única que suporta servidores Java e Bedrock.
    - server_type: "java" ou "bedrock"
    - jar: usado só para java (ex: "server.jar")
    - executable: usado só para bedrock (ex: "./bedrock_server" ou "bedrock_server")
    """

    def __init__(self, server_path, jar=None, ram_mb=0, port=25565, server_type="java", executable=None):
        self.server_path = server_path
        self.jar = jar
        self.ram_mb = ram_mb
        self.port = port
        self.server_type = server_type.lower()
        self.executable = executable or "./bedrock_server"

        self.process = None
        self.pid = None
        self.start_time = None
        self.logs = []

        self._reader_thread = None

    def _read_output(self):
        """
        Lê stdout da subprocess e guarda em self.logs.
        Usa readline para detectar término corretamente.
        """
        try:
            while True:
                if not self.process:
                    break
                line = self.process.stdout.readline()
                if line == "" and self.process.poll() is not None:
                    break
                if not line:
                    # evita loop apertado quando não há saída imediata
                    time.sleep(0.1)
                    continue
                text = line.rstrip("\n")
                self.logs.append(text)
                if len(self.logs) > LOG_LIMIT:
                    self.logs.pop(0)
        except Exception:
            # não quebrar por erro de leitura
            pass

    def is_running(self):
        # considera processo vivo se process existe e não retornou código
        if self.process and self.process.poll() is None:
            return True
        if self.pid:
            return psutil.pid_exists(self.pid)
        return False

    def start(self):
        if self.is_running():
            return False

        # monta comando dependendo do tipo
        if self.server_type == "java":
            if not self.jar:
                raise ValueError("Para servidores Java informe 'jar' (ex: server.jar)")
            cmd = [
                "java",
                f"-Xmx{self.ram_mb}M",
                "-jar",
                self.jar,
                "--port",
                str(self.port),
                "nogui"
            ]
        elif self.server_type == "bedrock":
            # garante que o binário esteja executável
            binary_path = os.path.join(self.server_path, os.path.basename(self.executable))
            try:
                os.chmod(binary_path, 0o755)
            except Exception:
                # permissões podem falhar em alguns ambientes; tentamos seguir em frente
                pass

            cmd = [self.executable]
        else:
            raise ValueError("server_type inválido. Use 'java' ou 'bedrock'.")

        self.process = subprocess.Popen(
            cmd,
            cwd=self.server_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1,
            universal_newlines=True
        )

        # curto delay para preencher pid e início
        time.sleep(0.5)

        self.pid = self.process.pid
        self.start_time = time.time()

        # cria thread leitora
        self._reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self._reader_thread.start()
        return True

    def stop(self, timeout=25):
        if not self.is_running():
            return False

        try:
            # tenta parar graciosamente pelo console
            try:
                self.send_command("stop")
            except Exception:
                pass

            # espera o processo terminar naturalmente
            self.process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            try:
                # tenta terminar e forçar kill se necessário
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass

        # cleanup
        self.pid = None
        self.start_time = None
        self.process = None
        return True

    def status(self):
        return {
            "running": self.is_running(),
            "pid": self.pid,
            "port": self.port,
            "ram_mb": self.ram_mb,
            "server_type": self.server_type,
            "uptime": int(time.time() - self.start_time) if self.start_time else 0
        }

    def send_command(self, cmd):
        """
        Envia comando para o stdin do processo (funciona para Java e, em geral, Bedrock).
        Pode lançar se stdin fechar.
        """
        if not self.process or not self.is_running():
            raise RuntimeError("Processo não está rodando")

        if not self.process.stdin:
            raise RuntimeError("stdin não disponível para o processo")

        try:
            self.process.stdin.write(cmd + "\n")
            self.process.stdin.flush()
            return True
        except Exception as e:
            # Se houver erro ao escrever (por exemplo stdin já fechado), raise para o caller lidar
            raise e
