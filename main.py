

import json
import os
import shutil
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "config.json"
DEFAULT_CONFIG = {
    "pastas_para_monitorar": [str(Path.home() / "Downloads")],
    "categorias": {
        "Imagens": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
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
            return json.load(f)
    except Exception:
        
        salvar_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG.copy()


def salvar_config(config):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


def mover_arquivo(caminho_origem, pasta_destino, logger=None):
    try:
        os.makedirs(pasta_destino, exist_ok=True)
        nome = os.path.basename(caminho_origem)
        destino = os.path.join(pasta_destino, nome)
        
        if os.path.exists(destino):
            base, ext = os.path.splitext(nome)
            i = 1
            while True:
                novo = f"{base} ({i}){ext}"
                destino = os.path.join(pasta_destino, novo)
                if not os.path.exists(destino):
                    break
                i += 1
        shutil.move(caminho_origem, destino)
        if logger:
            logger(f"📂 {nome} → {pasta_destino}")
    except Exception as e:
        if logger:
            logger(f"❌ Erro ao mover {caminho_origem}: {e}")



class OrganizadorHandler(FileSystemEventHandler):
    def __init__(self, categorias, logger=None):
        super().__init__()
        self.categorias = categorias
        self.logger = logger

    def on_created(self, event):
        if event.is_directory:
            return
        
        time.sleep(0.3)
        self.organizar(event.src_path)

    def on_moved(self, event):
        if event.is_directory:
            return
        time.sleep(0.2)
        self.organizar(event.dest_path)

    def organizar(self, arquivo):
        _, ext = os.path.splitext(arquivo)
        ext = ext.lower()
        for categoria, extensoes in self.categorias.items():
            if ext in extensoes:
                mover_arquivo(arquivo, os.path.join(os.path.dirname(arquivo), categoria), self.logger)
                return
        mover_arquivo(arquivo, os.path.join(os.path.dirname(arquivo), "Outros"), self.logger)



class MonitorManager:
    def __init__(self, logger=None):
        self.observers = []
        self.thread = None
        self.running = False
        self.logger = logger

    def start(self, pastas, categorias):
        if self.running:
            return
        self.running = True
        
        self.thread = threading.Thread(target=self._run, args=(pastas, categorias), daemon=True)
        self.thread.start()
        if self.logger:
            self.logger("🟢 Monitoramento iniciado")

    def _run(self, pastas, categorias):
        try:
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
            
            while self.running:
                time.sleep(0.5)
        except Exception as e:
            if self.logger:
                self.logger(f"❌ Erro no monitor: {e}")

    def stop(self):
        if not self.running:
            return
        self.running = False
        for obs in self.observers:
            try:
                obs.stop()
            except Exception:
                pass
        for obs in self.observers:
            try:
                obs.join()
            except Exception:
                pass
        self.observers = []
        if self.logger:
            self.logger("🔴 Monitoramento parado")



class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Organizador Automático")
        self.geometry("720x520")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        
        self.config_data = carregar_config()
        self.monitor = MonitorManager(logger=self.log)

        
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        self.configure(bg="#f3f6f9")
        self.style.configure('TFrame', background="#f3f6f9")
        self.style.configure('TLabel', background="#f3f6f9", font=("Segoe UI", 10))
        self.style.configure('Header.TLabel', font=("Segoe UI", 12, 'bold'))
        self.style.configure('TButton', padding=6, relief='flat', font=("Segoe UI", 10))

        
        container = ttk.Frame(self)
        container.pack(fill=tk.BOTH, expand=True, padx=16, pady=12)

        header = ttk.Label(container, text="Organizador Automático", style='Header.TLabel')
        header.pack(anchor='w')

       
        top = ttk.Frame(container)
        top.pack(fill=tk.X, pady=(8, 6))

        left = ttk.Frame(top)
        left.pack(side=tk.LEFT, fill=tk.Y, expand=True)

        ttk.Label(left, text="Pastas monitoradas:").pack(anchor='w')
        self.lista_pastas = tk.Listbox(left, height=8, width=60, bd=0, highlightthickness=0, activestyle='none')
        self.lista_pastas.pack(pady=6)
        for p in self.config_data.get("pastas_para_monitorar", []):
            self.lista_pastas.insert(tk.END, p)

        btn_frame = ttk.Frame(left)
        btn_frame.pack(anchor='w')

        btn_add = ttk.Button(btn_frame, text="➕ Adicionar pasta", command=self.adicionar_pasta)
        btn_add.grid(row=0, column=0, padx=4, pady=6)
        btn_remove = ttk.Button(btn_frame, text="➖ Remover selecionada", command=self.remover_pasta)
        btn_remove.grid(row=0, column=1, padx=4, pady=6)

        # Right side controls
        right = ttk.Frame(top)
        right.pack(side=tk.RIGHT, fill=tk.Y)

        self.status_var = tk.StringVar(value="Parado")
        ttk.Label(right, text="Status:").pack(anchor='e')
        self.status_label = ttk.Label(right, textvariable=self.status_var, font=("Segoe UI", 11, 'bold'))
        self.status_label.pack(pady=(0,8))

        self.btn_start = ttk.Button(right, text="Iniciar Monitoramento", command=self.toggle_monitor)
        self.btn_start.pack(fill=tk.X, pady=4)

        self.btn_save = ttk.Button(right, text="💾 Salvar e Recarregar", command=self.salvar_e_recarregar)
        self.btn_save.pack(fill=tk.X, pady=4)

        # Log area
        ttk.Label(container, text="Atividade:").pack(anchor='w', pady=(10,0))
        self.logbox = scrolledtext.ScrolledText(container, height=12, state='disabled', bg='white', font=("Consolas", 9))
        self.logbox.pack(fill=tk.BOTH, expand=True, pady=(6,0))

        # Footer
        footer = ttk.Frame(container)
        footer.pack(fill=tk.X, pady=(8,0))
        ttk.Label(footer, text="Dica: use 'Salvar e Recarregar' após adicionar pastas.").pack(side=tk.LEFT)

       
    def log(self, msg: str):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        self.logbox.config(state='normal')
        self.logbox.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.logbox.see(tk.END)
        self.logbox.config(state='disabled')

    def adicionar_pasta(self):
        caminho = filedialog.askdirectory(title="Selecione a pasta a ser monitorada")
        if not caminho:
            return
        caminho = caminho.replace('\\', '/')
        if caminho in self.config_data.get('pastas_para_monitorar', []):
            messagebox.showinfo("Info", "A pasta já está na lista.")
            return
        self.config_data.setdefault('pastas_para_monitorar', []).append(caminho)
        self.lista_pastas.insert(tk.END, caminho)
        self.log(f"➕ Pasta adicionada (ainda não salva): {caminho}")

    def remover_pasta(self):
        sel = self.lista_pastas.curselection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecione uma pasta para remover")
            return
        idx = sel[0]
        pasta = self.lista_pastas.get(idx)
        self.lista_pastas.delete(idx)
        try:
            self.config_data['pastas_para_monitorar'].remove(pasta)
        except Exception:
            pass
        self.log(f"➖ Pasta removida (ainda não salva): {pasta}")

    def salvar_e_recarregar(self):
        
        pastas = [self.lista_pastas.get(i) for i in range(self.lista_pastas.size())]
        self.config_data['pastas_para_monitorar'] = pastas
        salvar_config(self.config_data)
        self.log('💾 Configurações salvas em config.json')
        
        if self.monitor.running:
            self.monitor.stop()
            time.sleep(0.2)
            self.monitor.start(self.config_data['pastas_para_monitorar'], self.config_data['categorias'])
            self.status_var.set('Monitorando')
        else:
            self.log('⚠️ Monitor está parado. Clique em Iniciar Monitoramento para ativar.')

    def toggle_monitor(self):
        if self.monitor.running:
            self.monitor.stop()
            self.status_var.set('Parado')
            self.btn_start.config(text='Iniciar Monitoramento')
        else:
            pastas = self.config_data.get('pastas_para_monitorar', [])
            categorias = self.config_data.get('categorias', {})
            if not pastas:
                messagebox.showwarning('Aviso', 'Nenhuma pasta selecionada para monitorar.')
                return
            self.monitor.start(pastas, categorias)
            self.status_var.set('Monitorando')
            self.btn_start.config(text='Parar Monitoramento')

    def on_close(self):
        if messagebox.askokcancel("Sair", "Deseja realmente sair? O monitor será interrompido."):
            try:
                self.monitor.stop()
            except Exception:
                pass
            self.destroy()



if __name__ == '__main__':
    app = App()
    app.mainloop()
