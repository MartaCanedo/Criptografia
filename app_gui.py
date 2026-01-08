# Ambiente gráfico para cifragem / decifragem / visualização de gráficos

import os
import threading
import traceback
import tkinter as tk
import mplcursors
from tkinter import ttk, filedialog, messagebox, BooleanVar
from datetime import datetime

# imports do projeto 
from crypto_utils import gen_key
from file_ops import encrypt_file, decrypt_file
import benchmark 
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import csv

APP_TITLE = "CryptoLab — Cifragem / Decifragem / Análise de Modos AES"

class CryptoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.minsize(1000, 650)

        self.style = ttk.Style()
        self.current_theme_dark = BooleanVar(value=False)
        self._setup_themes()

        # Estado
        self.keypath = None
        self.input_file = None
        self.enc_file = None
        self.output_file = None
        self.loaded_key = None

        # Variáveis do Gráfico/Diagrama
        self.plot_type_var = tk.StringVar(value="time")
        self.plot_mode_filter_var = tk.StringVar(value="ALL")  # Filtro de modo
        self.plot_bits_filter_var = tk.StringVar(value="ALL")  # NOVO: Filtro de bits
        self.key_size_var = tk.StringVar(value="256")

        self._build_ui()
        self.log("Aplicação pronta. Selecione 'Gerar nova chave' ou 'Carregar chave' para começar.")

    def _setup_themes(self):
        # Tema claro 
        self.style.theme_use("clam")
        self.style.configure(".", background="#f5f5f5", foreground="#111111")
        self.style.configure("TLabel", background="#f5f5f5", foreground="#111111")
        self.style.configure("TFrame", background="#f5f5f5")
        self.style.configure("TLabelframe", background="#f5f5f5")
        self.style.configure("TLabelframe.Label", background="#f5f5f5", foreground="#111111")
        self.style.configure("TButton", padding=4)

        # Estilo de botão primário
        self.style.configure(
            "Accent.TButton",
            background="#0078D4",
            foreground="white"
        )

    def toggle_theme(self):
        dark = self.current_theme_dark.get()

        if dark:
            bg = "#202124"
            fg = "#e8eaed"
            entry_bg = "#303134"
            tab_bg = "#3c4043"
            tab_sel_bg = "#8ab4f8"
            tab_sel_fg = "#202124"
            cb_fg = "#e8eaed"
        else:
            bg = "#f5f5f5"
            fg = "#111111"
            entry_bg = "white"
            tab_bg = "#e1e1e1"
            tab_sel_bg = "#ffffff"
            tab_sel_fg = "#111111"
            cb_fg = "#111111"

        self.style.theme_use("clam")

        self.style.configure(".", background=bg, foreground=fg)
        self.style.configure("TFrame", background=bg)
        self.style.configure("TLabelframe", background=bg)
        self.style.configure("TLabelframe.Label", background=bg, foreground=fg)
        self.style.configure("TLabel", background=bg, foreground=fg)
        self.style.configure("TButton", background=tab_bg, foreground=fg)
        self.style.configure(
            "Accent.TButton",
            background="#8ab4f8" if dark else "#0078D4",
            foreground="#202124" if dark else "white"
        )
        # Botão normal
        self.style.configure("TButton", background=tab_bg, foreground=fg)
        self.style.map(
            "TButton",
            background=[("active", "#5f6368" if dark else "#d0d0d0")],
            foreground=[("active", fg)]
        )

        # Botão “accent”
        accent_bg = "#8ab4f8" if dark else "#0078D4"
        accent_fg = "#202124" if dark else "white"
        self.style.configure("Accent.TButton", background=accent_bg, foreground=accent_fg)
        self.style.map(
            "Accent.TButton",
            background=[("active", "#aecbfa" if dark else "#3392ff")],
            foreground=[("active", accent_fg)]
        )

        # Radio buttons
        self.style.configure(
            "TRadiobutton",
            background=bg,
            foreground=fg
        )
        self.style.map(
            "TRadiobutton",
            background=[("active", "#303134" if dark else "#dcdcdc")],
            foreground=[("active", fg)]
        )

        # Entry
        self.style.configure(
            "TEntry",
            fieldbackground=entry_bg,
            foreground=fg
        )

        # Combobox (campo visível)
        self.style.configure(
            "TCombobox",
            fieldbackground=entry_bg,
            foreground=cb_fg,
            background=entry_bg
        )
        # Combobox em estado readonly
        self.style.map(
            "TCombobox",
            fieldbackground=[("readonly", entry_bg), ("!disabled", entry_bg)],
            foreground=[("readonly", cb_fg), ("!disabled", cb_fg)]
        )
        # Lista drop-down do Combobox
        self.option_add("*TCombobox*Listbox.background", entry_bg)
        self.option_add("*TCombobox*Listbox.foreground", cb_fg)

        # Notebook e tabs
        self.style.configure("TNotebook", background=bg, borderwidth=0)
        self.style.configure(
            "TNotebook.Tab",
            background=tab_bg,
            foreground=fg,
            padding=(10, 4)
        )
        self.style.map(
            "TNotebook.Tab",
            background=[("selected", tab_sel_bg)],
            foreground=[("selected", tab_sel_fg)]
        )

        # janela principal
        self.configure(bg=bg)

        # Text de logs
        try:
            self.log_text.configure(bg=entry_bg, fg=fg, insertbackground=fg)
        except Exception:
            pass

    def _build_ui(self):
        # Barra superior
        topbar = ttk.Frame(self)
        topbar.pack(fill=tk.X, padx=10, pady=(10, 0))

        ttk.Label(
            topbar,
            text="CryptoLab",
            font=("Segoe UI", 12, "bold"),
            anchor="w"
        ).pack(side=tk.LEFT)

        theme_switch = ttk.Checkbutton(
            topbar,
            text="🌙 Dark mode",
            variable=self.current_theme_dark,
            command=self.toggle_theme
        )

        theme_switch.pack(side=tk.RIGHT)

        # Notebook principal
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 1. Logs Tab - Deve ser construído primeiro para inicializar self.log_text
        self.log_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.log_tab, text="📋 Logs de Atividade")
        self._build_log_tab()
        
        # 2. Cifrar / Decifrar Tab
        self.crypto_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.crypto_tab, text="🔐 Cifrar / Decifrar")
        self._build_crypto_tab()
        
        # 3. Benchmark & Gráficos Tab (Diagrams)
        self.diagrams_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.diagrams_tab, text="📈 Benchmark & Gráficos")
        self._build_diagrams_tab()
        
    def _build_log_tab(self):
        ttk.Label(
            self.log_tab,
            text="Logs Detalhados da Aplicação",
            font=("Segoe UI", 10, "bold"),
            wraplength=400,
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=5, pady=5)

        self.log_text = tk.Text(self.log_tab, height=30, wrap=tk.WORD, state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
    def _build_crypto_tab(self):
        main = ttk.Frame(self.crypto_tab)
        main.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        key_frame = ttk.LabelFrame(main, text="⚙️ Gestão de Chave e Modos")
        key_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15), pady=5)

        op_frame = ttk.LabelFrame(main, text="🚀 Operações de Ficheiro (Cifrar / Decifrar)")
        op_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        # --- Coluna da Chave/Controlos ---
        self.keylabel = ttk.Label(key_frame, text="Nenhuma chave carregada", wraplength=200)
        self.keylabel.pack(fill=tk.X, padx=10, pady=(10, 5))

        ttk.Label(
            key_frame,
            text="Tamanho da Chave (para Geração):",
            anchor="w",
            justify="left",
            wraplength=200
        ).pack(anchor="w", padx=10, pady=(10, 5))

        key_size_combo = ttk.Combobox(
            key_frame,
            textvariable=self.key_size_var,
            values=["128", "192", "256"],
            state="readonly",
            width=5
        )
        key_size_combo.pack(anchor="w", padx=10, pady=(0, 10))

        kbtn_frame = ttk.Frame(key_frame)
        kbtn_frame.pack(fill=tk.X, padx=10, pady=(5, 15))

        btn_gen_key = ttk.Button(kbtn_frame, text="🔑 Gerar nova chave", command=self.generate_key)
        btn_gen_key.pack(fill=tk.X, pady=2)

        btn_load_key = ttk.Button(kbtn_frame, text="⬆️ Carregar chave existente", command=self.load_key)
        btn_load_key.pack(fill=tk.X, pady=2)

        ttk.Separator(key_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10, padx=10)

        ttk.Label(
            key_frame,
            text="Modo AES:",
            anchor="w",
            justify="left",
            wraplength=200
        ).pack(anchor="w", padx=10, pady=(0, 5))

        self.mode_var = tk.StringVar(value="GCM")
        mode_combo = ttk.Combobox(
            key_frame,
            textvariable=self.mode_var,
            values=[
                "GCM (Autenticado - Recomendado)",
                "CBC (Com HMAC para Integridade)",
                "CTR (Com HMAC para Integridade)"
            ],
            state="readonly"
        )
        mode_combo.pack(fill=tk.X, padx=10, pady=(0, 10))
        mode_combo.bind('<<ComboboxSelected>>',
                        lambda event: self.mode_var.set(mode_combo.get().split(' ')[0]))

        # --- Coluna Operações (op_frame) ---
        ttk.Label(
            op_frame,
            text="1. Selecionar Ficheiro de Entrada",
            font=("Segoe UI", 10, "bold"),
            wraplength=400,
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=10, pady=(10, 5))

        btn_select_in = ttk.Button(
            op_frame,
            text="📁 Selecionar Ficheiro a Cifrar",
            command=self.select_input_file
        )
        btn_select_in.pack(fill=tk.X, padx=10, pady=2)

        btn_select_enc = ttk.Button(
            op_frame,
            text="📂 Selecionar Ficheiro (.enc) a Decifrar",
            command=self.select_enc_file
        )
        btn_select_enc.pack(fill=tk.X, padx=10, pady=2)

        ttk.Separator(op_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15, padx=10)

        ttk.Label(
            op_frame,
            text="2. Caminho do Ficheiro de Saída",
            font=("Segoe UI", 10, "bold"),
            wraplength=400,
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        path_group = ttk.Frame(op_frame)
        path_group.pack(fill=tk.X, padx=10)

        self.outpath_entry = ttk.Entry(path_group)
        self.outpath_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, pady=(0, 5))

        btn_choose_out = ttk.Button(
            path_group,
            text="Escolher...",
            command=self.choose_output_path
        )
        btn_choose_out.pack(side=tk.LEFT, padx=(5, 0), pady=(0, 5))

        ttk.Separator(op_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15, padx=10)

        ttk.Label(
            op_frame,
            text="3. Executar Operação",
            font=("Segoe UI", 10, "bold"),
            wraplength=400,
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=10, pady=(0, 5))

        btn_run_enc = ttk.Button(
            op_frame,
            text="🔒 CIFRAR (Encrypt)",
            command=self.run_encrypt,
            style="Accent.TButton"
        )
        btn_run_enc.pack(fill=tk.X, padx=10, pady=5)

        btn_run_dec = ttk.Button(
            op_frame,
            text="🔓 DECIFRAR (Decrypt)",
            command=self.run_decrypt
        )
        btn_run_dec.pack(fill=tk.X, padx=10, pady=5)

        # Label de ajuda (tooltips textuais)
        self.help_label = ttk.Label(
            self.crypto_tab,
            text="Dica: começa por gerar ou carregar uma chave.",
            font=("Segoe UI", 9, "italic"),
            anchor="w",
            justify="left",
            wraplength=600
        )
        self.help_label.pack(fill=tk.X, padx=10, pady=(0, 5))

        # Binds para tooltips simples
        btn_select_in.bind(
            "<Enter>",
            lambda e: self.help_label.config(
                text="Escolhe o ficheiro que queres cifrar."
            )
        )
        btn_select_in.bind(
            "<Leave>",
            lambda e: self.help_label.config(text="")
        )

        btn_select_enc.bind(
            "<Enter>",
            lambda e: self.help_label.config(
                text="Seleciona um ficheiro cifrado (.enc) para decifrar."
            )
        )
        btn_select_enc.bind(
            "<Leave>",
            lambda e: self.help_label.config(text="")
        )

        btn_choose_out.bind(
            "<Enter>",
            lambda e: self.help_label.config(
                text="Define o caminho/nome do ficheiro de saída."
            )
        )
        btn_choose_out.bind(
            "<Leave>",
            lambda e: self.help_label.config(text="")
        )

        btn_run_enc.bind(
            "<Enter>",
            lambda e: self.help_label.config(
                text="Cifra o ficheiro de entrada com a chave e modo atuais."
            )
        )
        btn_run_enc.bind(
            "<Leave>",
            lambda e: self.help_label.config(text="")
        )

        btn_run_dec.bind(
            "<Enter>",
            lambda e: self.help_label.config(
                text="Decifra o ficheiro .enc usando a chave carregada."
            )
        )
        btn_run_dec.bind(
            "<Leave>",
            lambda e: self.help_label.config(text="")
        )

        try:
            self.style.configure(
                'Accent.TButton',
                background='green',
                foreground='black',
                font=('Segoe UI', 10, 'bold')
            )
        except Exception:
            pass

    # --- UI Benchmark & Gráficos (Diagrams) ---
    def _build_diagrams_tab(self):
        # 1. Controles e Execução do Benchmark
        controls_frame = ttk.Frame(self.diagrams_tab)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(
            controls_frame,
            text="Executar Benchmark e Atualizar Gráficos",
            command=self.run_benchmark
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            controls_frame,
            text="Atualizar Visualização",
            command=self.update_diagrams
        ).pack(side=tk.LEFT, padx=0, pady=10)

        ttk.Button(
            controls_frame,
            text="📁 Abrir pasta do projecto",
            command=self.open_project_folder
        ).pack(side=tk.LEFT)

        ttk.Separator(self.diagrams_tab, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10, padx=10)

        # 2. Seleção do Tipo de Visualização & Filtro
        graph_selector_frame = ttk.LabelFrame(self.diagrams_tab, text="Tipo de Visualização & Filtro")
        graph_selector_frame.pack(fill=tk.X, padx=10, pady=5)

        # Filtro de Modo
        ttk.Label(
            graph_selector_frame,
            text="Filtro de Modo:",
            anchor="w",
            justify="left",
            wraplength=150
        ).pack(side=tk.LEFT, padx=(5, 0))

        plot_mode_combo = ttk.Combobox(
            graph_selector_frame,
            textvariable=self.plot_mode_filter_var,
            values=["ALL", "GCM", "CBC", "CTR", "CHACHA20", "3DES"],
            state="readonly",
            width=9
        )
        plot_mode_combo.pack(side=tk.LEFT, padx=(0, 15))
        plot_mode_combo.bind("<<ComboboxSelected>>", lambda event: self.update_diagrams())

        # Filtro de Bits
        ttk.Label(
            graph_selector_frame,
            text="Bits:",
            anchor="w",
            justify="left",
            wraplength=50
        ).pack(side=tk.LEFT, padx=(0, 0))

        bits_combo = ttk.Combobox(
            graph_selector_frame,
            textvariable=self.plot_bits_filter_var,
            values=["ALL", "128", "192", "256"],
            state="readonly",
            width=5
        )
        bits_combo.pack(side=tk.LEFT, padx=(0, 15))
        bits_combo.bind("<<ComboboxSelected>>", lambda event: self.update_diagrams())


        # Botões de Rádio do Tipo de Gráfico
        ttk.Radiobutton(
            graph_selector_frame,
            text="Tempo Enc/Dec (s)",
            variable=self.plot_type_var,
            value="time",
            command=self.update_diagrams
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Radiobutton(
            graph_selector_frame,
            text="Overhead do Ciphertext (%)",
            variable=self.plot_type_var,
            value="overhead",
            command=self.update_diagrams
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Radiobutton(
            graph_selector_frame,
            text="Expansão Cipher/Plain",
            variable=self.plot_type_var,
            value="expansion",
            command=self.update_diagrams
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Radiobutton(
            graph_selector_frame,
            text="Trade-off Tempo/Overhead",
            variable=self.plot_type_var,
            value="tradeoff",
            command=self.update_diagrams
        ).pack(side=tk.LEFT, padx=5, pady=5)

        ttk.Radiobutton(
            graph_selector_frame,
            text="Throughput (MB/s)",
            variable=self.plot_type_var,
            value="throughput",
            command=self.update_diagrams
        ).pack(side=tk.LEFT, padx=5)

        ttk.Radiobutton(
            graph_selector_frame, 
            text="CPU/RAM", 
            variable=self.plot_type_var, 
            value="cpu", 
            command=self.update_diagrams
        ).pack(side=tk.LEFT)

        # 3. Área de Visualização (Gráfico Matplotlib)
        self.graph_frame = ttk.LabelFrame(self.diagrams_tab, text="Gráfico de Desempenho")
        self.graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.fig, self.ax = plt.subplots(figsize=(6, 4))
        self.ax.set_title("Resultados do Benchmark AES")
        self.ax.set_xlabel("Tamanho da chave (bits)")
        self.ax.set_ylabel("Tempo (s)")
        self.ax.grid(True)

        self.cursor = None

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.graph_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Label com informação do ficheiro
        self.file_info_label = ttk.Label(
            self.graph_frame,
            text="Tamanho do ficheiro: —",
            font=("Segoe UI", 9, "italic")
        )
        self.file_info_label.pack(anchor="e", padx=10, pady=5)

        # primeiro desenho do gráfico (tempo por defeito)
        self.plot_from_csv()

    # ---- util ----
    def log(self, msg):
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.config(state=tk.DISABLED)

    def open_project_folder(self):
        path = os.getcwd()
        try:
            if os.name == 'nt':
                os.startfile(path)
            else:
                import subprocess
                subprocess.Popen(['xdg-open', path])
        except Exception as e:
            self.log(f"Erro ao abrir pasta: {e}")

    # ---- key management ----
    def generate_key(self):
        try:
            bits = int(self.key_size_var.get())
            key = gen_key(bits)
            save = filedialog.asksaveasfilename(defaultextension=".bin", filetypes=[("Key file","*.bin")], title=f"Salvar chave de {bits}-bit como...")
            if not save:
                self.log("Geração de chave cancelada")
                return
            with open(save, "wb") as f:
                f.write(key)
            self.keypath = save
            self.loaded_key = key
            self.keylabel.config(text=f"Chave:\n{os.path.basename(save)}\n({bits} bits, {len(key)} bytes)")
            self.log(f"Gerada e guardada chave de {bits}-bit em {save}")
        except Exception as e:
            self.log("Erro ao gerar chave: " + str(e))
            self.log(traceback.format_exc())

    def load_key(self):
        p = filedialog.askopenfilename(filetypes=[("Key file","*.bin"),("All files","*.*")], title="Selecionar ficheiro de chave")
        if not p:
            self.log("Carregamento de chave cancelado")
            return
        try:
            with open(p, "rb") as f:
                key = f.read()
            self.loaded_key = key
            self.keypath = p
            self.keylabel.config(text=f"Chave:\n{os.path.basename(p)}\n({len(key)*8} bits, {len(key)} bytes)")
            self.log(f"Chave carregada de {p}")
        except Exception as e:
            self.log("Erro ao carregar chave: " + str(e))
            self.log(traceback.format_exc())

    # ---- file selectors ----
    def select_input_file(self):
        p = filedialog.askopenfilename(title="Selecionar ficheiro a cifrar")
        if not p:
            return
        self.input_file = p
        self.enc_file = None
        self.outpath_entry.delete(0, tk.END)
        self.outpath_entry.insert(0, p + ".enc")
        self.log(f"Selecionado para cifrar: {p}")
    
    def select_enc_file(self):
        p = filedialog.askopenfilename(
            title="Selecionar ficheiro cifrado (.enc)",
            filetypes=[("Encrypted files", "*.enc"), ("All files", "*.*")]
        )
        if not p:
            return
        self.enc_file = p
        self.input_file = None
        self.outpath_entry.delete(0, tk.END)
        self.outpath_entry.insert(0, os.path.splitext(p)[0] + ".dec")
        self.log(f"Selecionado para decifrar: {p}")

    def choose_output_path(self):
        p = filedialog.asksaveasfilename(
            title="Escolher ficheiro de saída",
            filetypes=[("All files", "*.*")]
        )
        if not p:
            return
        self.outpath_entry.delete(0, tk.END)
        self.outpath_entry.insert(0, p)
        mode = self.mode_var.get()
        self.log(f"Output definido: {p} (modo: {mode})")

    def run_decrypt(self):
        enc = self.enc_file
        if not enc:
            enc_guess = self.outpath_entry.get().strip()
            if enc_guess and os.path.exists(enc_guess):
                enc = enc_guess
        if not enc:
            messagebox.showwarning("Falta ficheiro", "Seleciona o ficheiro cifrado (.enc) primeiro.")
            return
        if not self.loaded_key:
            messagebox.showwarning("Falta chave", "Carrega a chave (.bin) usada para cifrar.")
            return
        out = self.outpath_entry.get().strip()
        if not out:
            messagebox.showwarning("Falta output", "Escolhe um ficheiro de saída para a decifragem.")
            return
        self.log(f"Iniciando decifragem: {os.path.basename(enc)} -> {os.path.basename(out)}")
        threading.Thread(target=self._decrypt_thread, args=(enc, out, self.loaded_key), daemon=True).start()


    def _encrypt_thread(self, infile, outfile, key, mode):
        try:
            # Cifrar ficheiro
            res = encrypt_file(infile, outfile, key, mode=mode)
            self.log(f"Cifrado concluído: {res['file_out']} (tempo: {res['elapsed_s']:.3f}s)")

            # Atualizar benchmark automaticamente usando este ficheiro como teste
            try:
                import importlib
                import benchmark
                importlib.reload(benchmark)

                self.log("Atualizando benchmark com o ficheiro recém-cifrado...")
                benchmark.run_bench(test_file=infile)  # run_bench(test_file=...) no benchmark.py
                self.log("Benchmark atualizado e CSV gerado (benchmark_results.csv).")

                # Atualizar gráficos na aba de benchmark
                self.update_diagrams()
            except Exception as e:
                self.log(f"Falha ao atualizar benchmark automático: {e}")

            messagebox.showinfo("OK", f"Cifrado concluído:\n{res['file_out']}")

        except Exception as e:
            self.log("Erro cifragem: " + str(e))
            self.log(traceback.format_exc())
            messagebox.showerror("Erro", f"Erro na cifragem: {e}")


    def _encrypt_thread(self, infile, outfile, key, mode):
        try:
            res = encrypt_file(infile, outfile, key, mode=mode)
            self.log(f"Cifrado concluído: {res['file_out']} (tempo: {res['elapsed_s']:.3f}s)")
            messagebox.showinfo("OK", f"Cifrado concluído:\n{res['file_out']}")
        except Exception as e:
            self.log("Erro cifragem: " + str(e))
            self.log(traceback.format_exc())
            messagebox.showerror("Erro", f"Erro na cifragem: {e}")

        # ---- ops long running (Mantido) ----
    def run_encrypt(self):
        if not self.input_file:
            messagebox.showwarning("Falta ficheiro", "Seleciona um ficheiro a cifrar primeiro.")
            return
        if not self.loaded_key:
            messagebox.showwarning("Falta chave", "Carrega ou gera uma chave (.bin) antes.")
            return
        out = self.outpath_entry.get().strip()
        if not out:
            messagebox.showwarning("Falta output", "Escolhe um ficheiro de saída.")
            return
        mode_full = self.mode_var.get()
        mode = mode_full.split(' ')[0]
        self.log(f"Iniciando cifragem: {os.path.basename(self.input_file)} -> {os.path.basename(out)} (mode={mode})")
        threading.Thread(
            target=self._encrypt_thread,
            args=(self.input_file, out, self.loaded_key, mode),
            daemon=True
        ).start()

    def _encrypt_thread(self, infile, outfile, key, mode):
        try:
            # Cifrar ficheiro
            res = encrypt_file(infile, outfile, key, mode=mode)
            self.log(f"Cifrado concluído: {res['file_out']} (tempo: {res['elapsed_s']:.3f}s)")

            # Atualizar benchmark automaticamente usando este ficheiro como teste
            try:
                import importlib
                import benchmark
                importlib.reload(benchmark)

                self.log("Atualizando benchmark com o ficheiro recém-cifrado...")
                benchmark.run_bench(test_file=infile)  # run_bench(test_file=...) no benchmark.py
                self.log("Benchmark atualizado e CSV gerado (benchmark_results.csv).")

                # Atualizar gráficos na aba de benchmark
                self.update_diagrams()
            except Exception as e:
                self.log(f"Falha ao atualizar benchmark automático: {e}")

            messagebox.showinfo("OK", f"Cifrado concluído:\n{res['file_out']}")

        except Exception as e:
            self.log("Erro cifragem: " + str(e))
            self.log(traceback.format_exc())
            messagebox.showerror("Erro", f"Erro na cifragem: {e}")


    def _decrypt_thread(self, infile, outfile, key):
        try:
            res = decrypt_file(infile, outfile, key)
            self.log(f"Decifração concluída: {res['file_out']} (tempo: {res['elapsed_s']:.3f}s)")
            messagebox.showinfo("OK", f"Decifração concluída:\n{res['file_out']}")
        except Exception as e:
            self.log("Erro decifragem: " + str(e))
            self.log(traceback.format_exc())
            messagebox.showerror("Erro", f"Erro na decifragem: {e}")

    # ---- benchmark / plotting ----
    def run_benchmark(self):
        def _task():
            try:
                self.log("Iniciando benchmark (pode demorar alguns segundos)...")
                import benchmark
                benchmark.run_bench()
                self.log("Benchmark concluído e CSV gerado (benchmark_results.csv).")
                messagebox.showinfo("Benchmark", "Benchmark concluído! CSV gerado: benchmark_results.csv")
                self.update_diagrams()
            except ImportError:
                self.log("Erro: O ficheiro 'benchmark.py' não foi encontrado.")
                messagebox.showerror("Erro", "Ficheiro 'benchmark.py' não encontrado.")
            except Exception as e:
                self.log("Erro no benchmark: " + str(e))
                self.log(traceback.format_exc())
                messagebox.showerror("Erro", f"Erro no benchmark: {e}")
        threading.Thread(target=_task, daemon=True).start()

    def update_diagrams(self):
        plot_type = self.plot_type_var.get()
        csvpath = os.path.join(os.getcwd(), "benchmark_results.csv")

        self.fig.clear()

        if plot_type == "time":
            self.plot_from_csv()
            self.graph_frame.config(text=f"Gráfico Tempo Enc/Dec (s). Modo {self.plot_mode_filter_var.get()}")
        elif plot_type == "overhead":
            self.plot_overhead_from_csv()          # <-- aqui
            self.graph_frame.config(text=f"Gráfico Overhead do Ciphertext. Modo {self.plot_mode_filter_var.get()}")
        elif plot_type == "expansion":
            self.plot_expansion_by_cipher()        # nome novo
            self.graph_frame.config(text="Expansão Ciphertext/Plaintext por Cifra")
        elif plot_type == "tradeoff":
            self.plot_time_overhead_tradeoff()     # nome novo
            self.graph_frame.config(text="Trade-off Tempo vs Overhead por Cifra")
        elif plot_type == "throughput":
            self.plot_throughput()                 # nome novo se aplicável
            self.graph_frame.config(text="Throughput de cifragem (MB/s)")
        elif plot_type == "cpu":
            self.plot_cpu_from_csv()
            self.graph_frame.config(text=f"Uso de CPU/RAM. Modo {self.plot_mode_filter_var.get()}")

        # garantir que o canvas está visível
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _attach_tooltips(self):
        # limpar cursor antigo
        if self.cursor is not None:
            try:
                self.cursor.remove()
            except Exception:
                pass

        # criar novo cursor para todos os artistas visíveis no eixo atual
        self.cursor = mplcursors.cursor(self.fig.axes, hover=True)

        @self.cursor.connect("add")
        def on_add(sel):
            x, y = sel.target
            # formata label com valores X/Y
            sel.annotation.set_text(f"x = {x:.3f}\ny = {y:.3f}")
            sel.annotation.get_bbox_patch().set(alpha=0.8)

    # Adiciona filtro de modo
    def plot_overhead_from_csv(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            messagebox.showwarning("CSV não encontrado", "Executa o benchmark primeiro.")
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["bits"] = int(r["bits"])
                r["overhead_bytes"] = float(r["overhead_bytes"])
                r["overhead_pct"] = float(r["overhead_pct"])
                data.append(r)

        self.fig.clear()
        gs = self.fig.add_gridspec(2, 1, height_ratios=[2, 1])
        ax1 = self.fig.add_subplot(gs[0])
        ax2 = self.fig.add_subplot(gs[1])

        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        filter_mode = self.plot_mode_filter_var.get()

        modes = [m for m in ordered if any(d["mode"] == m for d in data)]
        if filter_mode != "ALL":
            modes = [filter_mode]

        for mode in modes:
            xs = [d["bits"] for d in data if d["mode"] == mode]
            ys = [d["overhead_bytes"] for d in data if d["mode"] == mode]
            ax1.plot(xs, ys, marker="o", label=mode)

        ax1.set_title("Overhead absoluto (bytes)")
        ax1.set_xlabel("Tamanho da chave (bits)")
        ax1.set_ylabel("Bytes")
        ax1.grid(True)
        ax1.legend()

        means = []
        for mode in modes:
            vals = [d["overhead_pct"] for d in data if d["mode"] == mode]
            means.append(sum(vals) / len(vals))

        ax2.bar(modes, means)
        ax2.set_title("Overhead médio (%)")
        ax2.set_ylabel("%")
        ax2.grid(axis="y")

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

    def plot_from_csv(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            messagebox.showwarning("CSV não encontrado", "Executa o benchmark primeiro.")
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    r["bits"] = int(r.get("bits", 0))
                except Exception:
                    r["bits"] = 0
                try:
                    r["enc_times"] = float(r.get("enc_time_s", 0))
                except Exception:
                    r["enc_times"] = 0.0
                try:
                    r["dec_times"] = float(r.get("dec_time_s", 0))
                except Exception:
                    r["dec_times"] = 0.0
                try:
                    r["cipher_len"] = int(r.get("cipher_len", 0))
                except Exception:
                    r["cipher_len"] = 0
                try:
                    r["plain_len"] = int(r.get("plain_len", 0))
                except Exception:
                    r["plain_len"] = 0
                data.append(r)

        # aplicar filtro de bits
        bits_filter = self.plot_bits_filter_var.get()
        if bits_filter != "ALL":
            try:
                bf = int(bits_filter)
                data = [r for r in data if r.get("bits") == bf]
            except Exception:
                pass

        self.fig.clear()

        gs = self.fig.add_gridspec(2, 2, height_ratios=[2, 1])
        ax1 = self.fig.add_subplot(gs[0, 0])
        ax2 = self.fig.add_subplot(gs[0, 1])
        ax3 = self.fig.add_subplot(gs[1, :])

        # ordem fixa de modos (inclui ChaCha20 e 3DES)
        all_modes = {r["mode"] for r in data}
        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        modes = [m for m in ordered if m in all_modes]

        # filtro de modo (combobox)
        filter_mode = self.plot_mode_filter_var.get()
        if filter_mode != "ALL":
            modes = [filter_mode] if filter_mode in modes else []

        cmap = plt.get_cmap("tab10")

        # gráficos de linhas enc/dec
        for i, mode in enumerate(modes):
            xs = [r["bits"] for r in data if r["mode"] == mode]
            enc = [r["enc_times"] for r in data if r["mode"] == mode]
            dec = [r["dec_times"] for r in data if r["mode"] == mode]

            color = cmap(i / max(1, len(modes)))
            if xs:
                ax1.plot(xs, enc, marker="o", label=mode, color=color)
                ax2.plot(xs, dec, marker="x", linestyle="--", label=mode, color=color)

        ax1.set_title("Tempo de Cifragem")
        ax2.set_title("Tempo de Decifragem")
        for ax in (ax1, ax2):
            ax.set_xlabel("Tamanho da chave (bits)")
            ax.set_ylabel("Tempo (s)")
            ax.grid(True)
            ax.legend()

        # barras de médias por cifra (enc/dec)
        labels = []
        enc_means = []
        dec_means = []

        for mode in modes:
            enc_vals = [r["enc_times"] for r in data if r["mode"] == mode]
            dec_vals = [r["dec_times"] for r in data if r["mode"] == mode]
            if not enc_vals and not dec_vals:
                continue
            labels.append(mode)
            enc_means.append(sum(enc_vals) / len(enc_vals) if enc_vals else 0)
            dec_means.append(sum(dec_vals) / len(dec_vals) if dec_vals else 0)

        x = list(range(len(labels)))
        width = 0.35

        ax3.clear()
        if labels:
            ax3.bar([p - width/2 for p in x], enc_means, width, label="Enc (média)", color="C0")
            ax3.bar([p + width/2 for p in x], dec_means, width, label="Dec (média)", color="C1")
            ax3.set_xticks(list(x))
            ax3.set_xticklabels(labels)

        ax3.set_title("Média de Tempo por Cifra (Enc vs Dec)")
        ax3.set_ylabel("Tempo (s)")
        ax3.grid(axis="y")
        ax3.legend()

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

        # info de ficheiro (1.ª linha do CSV)
        if data:
            plain = data[0].get("plain_len", 0)
            cipher = data[0].get("cipher_len", 0)
            self.file_info_label.config(
                text=f"Plaintext: {plain/1024:.2f} KB | Ciphertext: {cipher/1024:.2f} KB"
            )

    # Adiciona filtro de modo e verifica conversão de dados
    def plot_overhead_from_csv(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            messagebox.showwarning("CSV não encontrado", "Executa o benchmark primeiro.")
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    r["bits"] = int(r.get("bits", 0))
                except Exception:
                    r["bits"] = 0
                try:
                    r["cipher_len"] = int(r.get("cipher_len", 0))
                except Exception:
                    r["cipher_len"] = 0
                try:
                    r["plain_len"] = int(r.get("plain_len", 0))
                except Exception:
                    r["plain_len"] = 0
                data.append(r)
        
        # aplicar filtro de bits
        bits_filter = self.plot_bits_filter_var.get()
        if bits_filter != "ALL":
            try:
                bf = int(bits_filter)
                data = [r for r in data if r.get("bits") == bf]
            except Exception:
                pass

        self.fig.clear()
        gs = self.fig.add_gridspec(2, 1, height_ratios=[3, 1])
        ax = self.fig.add_subplot(gs[0, 0])
        ax2 = self.fig.add_subplot(gs[1, 0])

        # ordem fixa de modos
        all_modes = {r["mode"] for r in data}
        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        modes = [m for m in ordered if m in all_modes]

        # filtro de modo
        filter_mode = self.plot_mode_filter_var.get()
        if filter_mode != "ALL":
            modes = [filter_mode] if filter_mode in modes else []

        cmap = plt.get_cmap("tab10")

        # linhas: overhead por tamanho de chave
        for i, mode in enumerate(modes):
            xs = []
            ys = []
            for r in data:
                if r.get("mode") == mode:
                    xs.append(r.get("bits", 0))
                    plain = r.get("plain_len", 0)
                    cipher = r.get("cipher_len", 0)
                    if plain:
                        ys.append((cipher - plain) / plain * 100)
                    else:
                        ys.append(0)
            color = cmap(i / max(1, len(modes)))
            if xs:
                ax.plot(xs, ys, marker="o", label=mode, color=color)

        ax.set_title("Overhead do Ciphertext (%)")
        ax.set_xlabel("Tamanho da chave (bits)")
        ax.set_ylabel("Overhead (%)")
        ax.grid(True)
        ax.legend()

        # barras: overhead médio por cifra
        labels = []
        means = []
        for mode in modes:
            values = []
            for r in data:
                if r.get("mode") == mode:
                    plain = r.get("plain_len", 0)
                    cipher = r.get("cipher_len", 0)
                    if plain:
                        values.append((cipher - plain) / plain * 100)
            labels.append(mode)
            means.append(sum(values) / len(values) if values else 0)

        ax2.clear()
        if labels:
            ax2.bar(labels, means, color=[cmap(i / max(1, len(labels))) for i in range(len(labels))])
        ax2.set_title("Overhead médio por Cifra (%)")
        ax2.set_ylabel("Overhead (%)")
        ax2.grid(axis="y")

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

        # info do ficheiro (1.ª linha)
        if data:
            plain = data[0].get("plain_len", 0)
            cipher = data[0].get("cipher_len", 0)
            self.file_info_label.config(
                text=f"Plaintext: {plain/1024:.2f} KB | Ciphertext: {cipher/1024:.2f} KB"
            )

    def plot_expansion_by_cipher(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            messagebox.showwarning("CSV não encontrado", "Executa o benchmark primeiro.")
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    cipher_len = int(r.get("cipher_len", 0))
                except Exception:
                    cipher_len = 0
                try:
                    plain_len = int(r.get("plain_len", 0))
                except Exception:
                    plain_len = 0
                r["cipher_len"] = cipher_len
                r["plain_len"] = plain_len
                data.append(r)

        # aplicar filtro de bits
        bits_filter = self.plot_bits_filter_var.get()
        if bits_filter != "ALL":
            try:
                bf = int(bits_filter)
                data = [r for r in data if int(r.get("bits", 0)) == bf]
            except Exception:
                pass

        if not data:
            self.log("CSV de benchmark vazio.")
            return

        all_modes = {r["mode"] for r in data}
        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        modes = [m for m in ordered if m in all_modes]

        filter_mode = self.plot_mode_filter_var.get()
        if filter_mode != "ALL":
            modes = [filter_mode] if filter_mode in modes else []

        labels = []
        ratios = []

        for mode in modes:
            rows = [r for r in data if r["mode"] == mode]
            vals = []
            for r in rows:
                plain = r["plain_len"]
                cipher = r["cipher_len"]
                if plain:
                    vals.append(cipher / plain)
            if not vals:
                continue
            labels.append(mode)
            ratios.append(sum(vals) / len(vals))

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if labels:
            ax.bar(labels, ratios, color="C0")
        ax.set_title("Expansão média Ciphertext/Plaintext por Cifra")
        ax.set_ylabel("Cipher_len / Plain_len")
        ax.grid(axis="y")

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

    def plot_time_overhead_tradeoff(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            messagebox.showwarning("CSV não encontrado", "Executa o benchmark primeiro.")
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    enc = float(r.get("enc_time_s", 0))
                except Exception:
                    enc = 0.0
                try:
                    dec = float(r.get("dec_time_s", 0))
                except Exception:
                    dec = 0.0
                try:
                    cipher_len = int(r.get("cipher_len", 0))
                except Exception:
                    cipher_len = 0
                try:
                    plain_len = int(r.get("plain_len", 0))
                except Exception:
                    plain_len = 0
                r["total"] = enc + dec
                r["cipher_len"] = cipher_len
                r["plain_len"] = plain_len
                data.append(r)

        # aplicar filtro de bits
        bits_filter = self.plot_bits_filter_var.get()
        if bits_filter != "ALL":
            try:
                bf = int(bits_filter)
                data = [r for r in data if int(r.get("bits", 0)) == bf]
            except Exception:
                pass

        if not data:
            self.log("CSV de benchmark vazio.")
            return

        all_modes = {r["mode"] for r in data}
        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        modes = [m for m in ordered if m in all_modes]

        filter_mode = self.plot_mode_filter_var.get()
        if filter_mode != "ALL":
            modes = [filter_mode] if filter_mode in modes else []

        labels = []
        times = []
        overheads = []

        for mode in modes:
            rows = [r for r in data if r["mode"] == mode]
            if not rows:
                continue

            time_vals = [r["total"] for r in rows]
            ov_vals = []
            for r in rows:
                plain = r["plain_len"]
                cipher = r["cipher_len"]
                if plain:
                    ov_vals.append((cipher - plain) / plain * 100)

            labels.append(mode)
            times.append(sum(time_vals) / len(time_vals) if time_vals else 0)
            overheads.append(sum(ov_vals) / len(ov_vals) if ov_vals else 0)

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if labels:
            for x, y, label in zip(overheads, times, labels):
                ax.scatter(x, y)
                ax.text(x, y, label)

        ax.set_title("Trade-off Tempo vs Overhead por Cifra")
        ax.set_xlabel("Overhead médio (%)")
        ax.set_ylabel("Tempo médio total (s)")
        ax.grid(True)

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

    def plot_throughput(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                r["throughput_mb_s"] = float(r["throughput_mb_s"])
                data.append(r)

        # aplicar filtro de bits
        bits_filter = self.plot_bits_filter_var.get()
        if bits_filter != "ALL":
            try:
                bf = int(bits_filter)
                data = [r for r in data if int(r.get("bits", 0)) == bf]
            except Exception:
                pass

        self.fig.clear()
        ax = self.fig.add_subplot(111)

        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        filter_mode = self.plot_mode_filter_var.get()

        modes = [m for m in ordered if any(d["mode"] == m for d in data)]
        if filter_mode != "ALL":
            modes = [filter_mode]

        for mode in modes:
            xs = [int(d["bits"]) for d in data if d["mode"] == mode]
            ys = [d["throughput_mb_s"] for d in data if d["mode"] == mode]
            ax.plot(xs, ys, marker="o", label=mode)

        ax.set_title("Throughput de cifragem (MB/s)")
        ax.set_xlabel("Tamanho da chave (bits)")
        ax.set_ylabel("MB/s")
        ax.grid(True)
        ax.legend()

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

    def plot_cpu_from_csv(self):
        csv_path = os.path.join(os.getcwd(), "benchmark_results.csv")
        if not os.path.exists(csv_path):
            messagebox.showwarning("CSV não encontrado", "Executa o benchmark primeiro.")
            return

        data = []
        with open(csv_path, newline="") as f:
            reader = csv.DictReader(f)
            for r in reader:
                try:
                    r["bits"] = int(r.get("bits", 0))
                    r["cpu_pct"] = float(r.get("cpu_pct", 0))
                    r["mem_delta_bytes"] = float(r.get("mem_delta_bytes", 0))
                except Exception:
                    r["bits"] = 0
                    r["cpu_pct"] = 0.0
                    r["mem_delta_bytes"] = 0.0
                data.append(r)

        # Filtro de bits
        bits_filter = self.plot_bits_filter_var.get()
        if bits_filter != "ALL":
            try:
                bf = int(bits_filter)
                data = [r for r in data if int(r.get("bits", 0)) == bf]
            except Exception:
                pass

        if not data:
            self.log("CSV de benchmark vazio (CPU).")
            return

        # Ordem e filtro de modos
        ordered = ["GCM", "CBC", "CTR", "CHACHA20", "3DES"]
        filter_mode = self.plot_mode_filter_var.get()
        modes = [m for m in ordered if any(d["mode"] == m for d in data)]
        if filter_mode != "ALL":
            modes = [filter_mode] if filter_mode in modes else []

        self.fig.clear()
        gs = self.fig.add_gridspec(2, 1, height_ratios=[2, 1])
        ax1 = self.fig.add_subplot(gs[0])
        ax2 = self.fig.add_subplot(gs[1])

        # Gráfico de linha: CPU% vs bits
        for mode in modes:
            xs = [int(d["bits"]) for d in data if d["mode"] == mode]
            ys = [d["cpu_pct"] for d in data if d["mode"] == mode]
            if xs:
                ax1.plot(xs, ys, marker="o", label=mode)
        ax1.set_title("Uso de CPU (%)")
        ax1.set_xlabel("Tamanho da chave (bits)")
        ax1.set_ylabel("CPU (%)")
        ax1.grid(True)
        ax1.legend()

        # Gráfico de barras: média de memória extra por modo (em MB)
        mem_means = []
        mem_labels = []
        for mode in modes:
            vals = [d["mem_delta_bytes"] for d in data if d["mode"] == mode]
            if not vals:
                continue
            mem_labels.append(mode)
            mem_means.append(sum(vals) / len(vals) / (1024 * 1024))  # converter para MB

        if mem_labels:
            ax2.bar(mem_labels, mem_means)
        ax2.set_title("Memória adicional média (MB)")
        ax2.set_ylabel("MB")
        ax2.grid(axis="y")

        self.fig.tight_layout()
        self.canvas.draw()
        self._attach_tooltips()

if __name__ == "__main__":
    app = CryptoApp()
    app.mainloop()