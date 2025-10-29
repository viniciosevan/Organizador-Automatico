import os
import shutil
import time
import json
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler



def carregar_configuracao():
    config_path = Path(__file__).parent / "config.json"
    if not config_path.exists():
        raise FileNotFoundError("Arquivo config.json não encontrado.")
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)



def mover_arquivo(arquivo, categorias, pasta_base):
    item = Path(arquivo)

 
    if not item.is_file():
        return

   
    for categoria, extensoes in categorias.items():
        if item.suffix.lower() in extensoes:
            destino = Path(pasta_base) / categoria
            destino.mkdir(exist_ok=True)
            shutil.move(str(item), destino / item.name)
            print(f"📂 {item.name} → {categoria}")
            return

    
    destino = Path(pasta_base) / "Outros"
    destino.mkdir(exist_ok=True)
    shutil.move(str(item), destino / item.name)
    print(f"📦 {item.name} → Outros")



class MonitoramentoHandler(FileSystemEventHandler):
    def __init__(self, categorias, pasta_base):
        self.categorias = categorias
        self.pasta_base = pasta_base

    def on_created(self, event):
        if not event.is_directory:
            mover_arquivo(event.src_path, self.categorias, self.pasta_base)

    def on_moved(self, event):
        if not event.is_directory:
            mover_arquivo(event.dest_path, self.categorias, self.pasta_base)



def iniciar_monitoramento():
    config = carregar_configuracao()
    categorias = config["categorias"]
    pastas = config["pastas_para_monitorar"]

    observers = []

    for pasta in pastas:
        if not os.path.exists(pasta):
            print(f"⚠️  Pasta não encontrada: {pasta}")
            continue

        print(f"👀 Monitorando: {pasta}")
        event_handler = MonitoramentoHandler(categorias, pasta)
        observer = Observer()
        observer.schedule(event_handler, pasta, recursive=False)
        observer.start()
        observers.append(observer)

    print("✅ Organizador automático iniciado! Pressione Ctrl+C para parar.")

    try:
        while True:
            time.sleep(2)
    except KeyboardInterrupt:
        print("\n🛑 Encerrando monitoramento...")
        for observer in observers:
            observer.stop()
        for observer in observers:
            observer.join()
        print("✅ Programa finalizado com segurança.")


if __name__ == "__main__":
    iniciar_monitoramento()
