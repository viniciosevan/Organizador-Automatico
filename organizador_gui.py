import os
import sys
import json
import shutil
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

CONFIG_PATH = BASE_DIR / "config.json"

DEFAULT_CONFIG = {
    "pastas_para_monitorar": [str(Path.home() / "Downloads")],
    "categorias": {
        "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"],
        "Vídeos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv"],
        "Áudios": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
        "Documentos": [".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx"],
        "Compactados": [".zip", ".rar", ".7z", ".tar", ".gz"],
        "Executáveis": [".exe", ".msi", ".bat"],
        "Torrents": [".torrent"],
        "Scripts": [".py", ".js", ".sh", ".ps1", ".java", ".cpp"],
        "Outros": []
    }
}

def carregar_config():
    if not CONFIG_PATH.exists():
        salvar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        salvar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()
    # normalize key name compatibility
    if "pastas_para_monitorar" not in cfg and "pastas_monitoradas" in cfg:
        cfg["pastas_para_monitorar"] = cfg.pop("pastas_monitoradas")
    if "pastas_para_monitorar" not in cfg:
        cfg["pastas_para_monitorar"] = DEFAULT_CONFIG["pastas_para_monitorar"]
    if "categorias" not in cfg:
        cfg["categorias"] = DEFAULT_CONFIG["categorias"]
    return cfg

def salvar_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def mover_arquivo(caminho, categorias, logger=None):
    try:
        caminho = Path(caminho)
        if not caminho.is_file():
            return
        ext = caminho.suffix.lower()
        pasta_base = caminho.parent
        for categoria, exts in categorias.items():
            if ext in exts:
                destino = pasta_base / categoria
                destino.mkdir(exist_ok=True)
                alvo = destino / caminho.name
                
                if alvo.exists():
                    base, e = caminho.stem, caminho.suffix
                    i = 1
                    while destino.joinpath(f"{base} ({i}){e}").exists():
                        i += 1
                    alvo = destino.joinpath(f"{base} ({i}){e}")
                shutil.move(str(caminho), str(alvo))
                if logger:
                    logger(f"📂 {caminho.name} → {categoria}")
                return
        
        destino = pasta_base / "Outros"
        destino.mkdir(exist_ok=True)
        shutil.move(str(caminho), str(destino / caminho.name))
        if logger:
            logger(f"📦 {caminho.name} → Outros")
    except Exception as e:
        if logger:
            logger(f"❌ Erro mover {caminho}: {e}")


class OrganizadorHandler(FileSystemEventHandler):
    def __init__(self, categorias, logger=None):
        super().__init__()
        self.categorias = categorias
        self.logger = logger

    def on_created(self, event):
        if event.is_directory:
            return
        
        time.sleep(0.2)
        mover_arquivo(event.src_path, self.categorias, self.logger)

    def on_moved(self, event):
        if event.is_directory:
            return
        time.sleep(0.1)
        mover_arquivo(event.dest_path, self.categorias, self.logger)


class MonitorManager:
    def __init__(self, logger=None):
        self.observers = []
        self.running = False
        self.logger = logger

    def start(self, pastas, categorias):
        if self.running:
            return
        self.running = True
        self.observers = []
        for pasta in pastas:
            if not os.path.exists(pasta):
                if self.logger:
                    self.logger(f"⚠️ Pasta não encontrada: {pasta}")
                continue
            handler = OrganizadorHandler(categorias, logger=self.logger)
            obs = Observer()
            obs.schedule(handler, pasta, recursive=False)
            obs.start()
            self.observers.append(obs)
            if self.logger:
                self.logger(f"✅ Monitorando: {pasta}")

    def stop(self):
        if not self.running:
            return
        for obs in self.observers:
            try:
                obs.stop()
            except Exception:
                pass
        for obs in self.observers:
            try:
                obs.join(timeout=2)
            except Exception:
                pass
        self.observers = []
        self.running = False
        if self.logger:
            self.logger("🔴 Monitoramento parado")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador Automático")
        self.geometry("720x520")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.cfg = carregar_config()
        self.monitor = MonitorManager(logger=self.log)
        self._build_ui()

    def _build_ui(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        self.configure(bg="#f3f6f9")
        style.configure('Header.TLabel', font=("Segoe UI", 13, 'bold'))
        style.configure('TButton', padding=6, relief='flat')

        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        ttk.Label(frame, text="Organizador Automático", style='Header.TLabel').pack(anchor='w')

        top = ttk.Frame(frame)
        top.pack(fill=tk.X, pady=(8,6))

        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.Y, expand=True)

        ttk.Label(left, text="Pastas monitoradas:").pack(anchor='w')
        self.listbox = tk.Listbox(left, width=60, height=10)
        self.listbox.pack(pady=6)
        for p in self.cfg.get("pastas_para_monitorar", []):
            self.listbox.insert(tk.END, p)

        btn_frame = ttk.Frame(left); btn_frame.pack(anchor='w')
        ttk.Button(btn_frame, text="➕ Adicionar pasta", command=self.add_folder).grid(row=0, column=0, padx=4)
        ttk.Button(btn_frame, text="➖ Remover selecionada", command=self.remove_folder).grid(row=0, column=1, padx=4)
        ttk.Button(btn_frame, text="💾 Salvar", command=self.save_config).grid(row=0, column=2, padx=4)

        right = ttk.Frame(top); right.pack(side=tk.RIGHT, fill=tk.Y)
        ttk.Label(right, text="Status:").pack(anchor='e')
        self.status_var = tk.StringVar(value="Parado")
        ttk.Label(right, textvariable=self.status_var, font=("Segoe UI", 11, 'bold')).pack(pady=(0,8))

        self.btn_toggle = ttk.Button(right, text="Iniciar Monitoramento", command=self.toggle_monitor)
        self.btn_toggle.pack(fill=tk.X, pady=4)

        ttk.Button(right, text="Salvar e Recarregar", command=self.save_and_reload).pack(fill=tk.X, pady=4)

        ttk.Label(frame, text="Atividade:").pack(anchor='w', pady=(10,0))
        self.logbox = scrolledtext.ScrolledText(frame, height=14, state='disabled', font=("Consolas",9))
        self.logbox.pack(fill=tk.BOTH, expand=True, pady=(6,0))

    
    def log(self, msg):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        self.logbox.config(state='normal')
        self.logbox.insert(tk.END, f"[{ts}] {msg}\n")
        self.logbox.see(tk.END)
        self.logbox.config(state='disabled')

    def add_folder(self):
        d = filedialog.askdirectory(title="Selecione pasta para monitorar")
        if d and d not in self.cfg["pastas_para_monitorar"]:
            self.cfg["pastas_para_monitorar"].append(d.replace("\\","/"))
            self.listbox.insert(tk.END, d.replace("\\","/"))
            self.log(f"➕ Pasta adicionada (não salva): {d}")

    def remove_folder(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Aviso","Selecione uma pasta para remover")
            return
        idx = sel[0]
        pasta = self.listbox.get(idx)
        self.listbox.delete(idx)
        try:
            self.cfg["pastas_para_monitorar"].remove(pasta)
        except Exception:
            pass
        self.log(f"➖ Pasta removida (não salva): {pasta}")

    def save_config(self):
        
        pastas = [self.listbox.get(i) for i in range(self.listbox.size())]
        self.cfg["pastas_para_monitorar"] = pastas
        salvar_config(self.cfg)
        self.log("💾 Configurações salvas em config.json")
        messagebox.showinfo("Sucesso","Configurações salvas")

    def save_and_reload(self):
        self.save_config()
        if self.monitor.running:
            self.monitor.stop()
            time.sleep(0.2)
            self.monitor.start(self.cfg["pastas_para_monitorar"], self.cfg["categorias"])
            self.status_var.set("Monitorando")
            self.log("♻️ Monitor reiniciado com novas configurações")
        else:
            self.log("⚠️ Monitor está parado. Clique em Iniciar Monitoramento para ativar.")

    def toggle_monitor(self):
        if self.monitor.running:
            self.monitor.stop()
            self.status_var.set("Parado")
            self.btn_toggle.config(text="Iniciar Monitoramento")
        else:
            self.monitor.start(self.cfg["pastas_para_monitorar"], self.cfg["categorias"])
            self.status_var.set("Monitorando")
            self.btn_toggle.config(text="Parar Monitoramento")

    def on_close(self):
        if messagebox.askokcancel("Sair","Deseja sair? O monitor será interrompido."):
            try:
                self.monitor.stop()
            except Exception:
                pass
            self.destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()