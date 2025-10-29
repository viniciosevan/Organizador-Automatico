import json
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

CONFIG_PATH = Path(__file__).parent / "config.json"


def carregar_config():
    
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"pastas_para_monitorar": [], "categorias": {}}


def salvar_config(config):
    
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


class ConfiguradorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Configuração do Organizador Automático")
        self.root.geometry("600x400")

        self.config = carregar_config()

        # === Interface ===
        tk.Label(root, text="Pastas monitoradas:", font=("Arial", 12, "bold")).pack(pady=5)

        self.lista_pastas = tk.Listbox(root, width=80, height=12, selectmode=tk.SINGLE)
        self.lista_pastas.pack(pady=5)

        for pasta in self.config["pastas_para_monitorar"]:
            self.lista_pastas.insert(tk.END, pasta)

        # Botões
        frame_botoes = tk.Frame(root)
        frame_botoes.pack(pady=10)

        tk.Button(frame_botoes, text="➕ Adicionar pasta", command=self.adicionar_pasta).grid(row=0, column=0, padx=5)
        tk.Button(frame_botoes, text="➖ Remover selecionada", command=self.remover_pasta).grid(row=0, column=1, padx=5)
        tk.Button(frame_botoes, text="💾 Salvar alterações", command=self.salvar).grid(row=0, column=2, padx=5)
        tk.Button(frame_botoes, text="🚪 Fechar", command=self.root.quit).grid(row=0, column=3, padx=5)

        # Status
        self.status_label = tk.Label(root, text="", fg="green")
        self.status_label.pack(pady=10)

    def adicionar_pasta(self):
        caminho = filedialog.askdirectory(title="Selecione uma pasta para monitorar")
        if caminho and caminho not in self.config["pastas_para_monitorar"]:
            self.config["pastas_para_monitorar"].append(caminho.replace("\\", "/"))
            self.lista_pastas.insert(tk.END, caminho.replace("\\", "/"))
            self.status_label.config(text="Pasta adicionada com sucesso ✅")

    def remover_pasta(self):
        selecao = self.lista_pastas.curselection()
        if selecao:
            idx = selecao[0]
            pasta = self.lista_pastas.get(idx)
            self.lista_pastas.delete(idx)
            self.config["pastas_para_monitorar"].remove(pasta)
            self.status_label.config(text=f"Pasta removida: {pasta}")
        else:
            messagebox.showwarning("Aviso", "Selecione uma pasta para remover.")

    def salvar(self):
        salvar_config(self.config)
        self.status_label.config(text="Alterações salvas com sucesso 💾")
        messagebox.showinfo("Sucesso", "Configurações salvas no config.json!")


if __name__ == "__main__":
    root = tk.Tk()
    app = ConfiguradorApp(root)
    root.mainloop()