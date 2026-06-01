import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3

# ==========================================
# BANCO DE DADOS
# ==========================================

DB = "supermercado.db"

def db(sql, params=(), fetch=None, commit=False):
    """Executa qualquer SQL e retorna o resultado pedido."""
    conn = sqlite3.connect(DB)
    cur  = conn.cursor()
    cur.execute(sql, params)
    resultado = cur.fetchall() if fetch == "all" else cur.fetchone() if fetch == "one" else None
    if commit:
        conn.commit()
    conn.close()
    return resultado

def inicializar_banco():
    db("""CREATE TABLE IF NOT EXISTS usuarios (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT NOT NULL UNIQUE,
            senha   TEXT NOT NULL)""", commit=True)
    db("""CREATE TABLE IF NOT EXISTS produtos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            nome       TEXT    NOT NULL,
            preco      REAL    NOT NULL,
            quantidade INTEGER NOT NULL,
            categoria  TEXT    NOT NULL)""", commit=True)
    if not db("SELECT id FROM usuarios WHERE usuario='admin'", fetch="one"):
        db("INSERT INTO usuarios (usuario, senha) VALUES (?,?)", ("admin","123"), commit=True)

inicializar_banco()

# ==========================================
# CORES
# ==========================================

COR_FUNDO      = "#181A20"
COR_MENU       = "#22252E"
COR_CARD       = "#2A2D37"
COR_AZUL       = "#5E81F4"
COR_AZUL_HOVER = "#4B6FE3"
COR_VERMELHO   = "#E74C3C"
COR_TEXTO      = "#FFFFFF"
COR_SUBTEXTO   = "#B8BCC8"

# ==========================================
# JANELA
# ==========================================

janela = tk.Tk()
janela.title("Sistema de Supermercado")
janela.geometry("1200x650")
janela.configure(bg=COR_FUNDO)
janela.resizable(False, False)

# ==========================================
# ESTILO TABELA
# ==========================================

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", background=COR_CARD, foreground=COR_TEXTO,
                fieldbackground=COR_CARD, rowheight=35, font=("Segoe UI", 11), borderwidth=0)
style.configure("Treeview.Heading", background=COR_AZUL, foreground="white",
                font=("Segoe UI", 11, "bold"), relief="flat")
style.map("Treeview", background=[("selected", COR_AZUL_HOVER)])

# ==========================================
# FUNÇÕES
# ==========================================

categoria_ativa = tk.StringVar(value="Todos")

def get_id_selecionado():
    item = tabela.selection()
    return int(tabela.item(item[0])["values"][0]) if item else None

def atualizar_tabela():
    tabela.delete(*tabela.get_children())
    sql    = "SELECT id, nome, preco, quantidade, categoria FROM produtos WHERE LOWER(nome) LIKE ?"
    params = [f"%{campo_pesquisa.get().lower()}%"]
    cat = categoria_ativa.get()
    if cat != "Todos":
        sql += " AND LOWER(categoria) = ?"
        params.append(cat.lower())
    for pid, nome, preco, qtd, cat in db(sql, params, fetch="all"):
        tabela.insert("", "end", iid=str(pid), values=(pid, nome, f"R$ {preco:.2f}", qtd, cat))
    atualizar_dashboard()

def atualizar_dashboard():
    total_produtos.config(text=str(db("SELECT COUNT(*) FROM produtos", fetch="one")[0]))
    produtos_estoque.config(text=str(db("SELECT SUM(quantidade) FROM produtos", fetch="one")[0] or 0))
    valor = db("SELECT SUM(preco*quantidade) FROM produtos", fetch="one")[0] or 0
    valor_estoque.config(text=f"R$ {valor:,.2f}")

def cadastrar_produto():
    nome = simpledialog.askstring("Cadastro", "Nome do produto:")
    if not nome: return
    try:
        preco      = float(simpledialog.askstring("Cadastro", "Preço:"))
        quantidade = int(simpledialog.askstring("Cadastro", "Quantidade:"))
    except (TypeError, ValueError):
        messagebox.showerror("Erro", "Valores inválidos."); return
    categoria = simpledialog.askstring("Cadastro", "Categoria:")
    if not categoria: return
    db("INSERT INTO produtos (nome, preco, quantidade, categoria) VALUES (?,?,?,?)",
       (nome, preco, quantidade, categoria), commit=True)
    atualizar_tabela()
    messagebox.showinfo("Sucesso", "Produto cadastrado!")

def remover_produto():
    pid = get_id_selecionado()
    if pid is None: messagebox.showerror("Erro", "Selecione um produto."); return
    nome = tabela.item(tabela.selection()[0])["values"][1]
    db("DELETE FROM produtos WHERE id=?", (pid,), commit=True)
    atualizar_tabela()
    messagebox.showinfo("Sucesso", f"{nome} removido.")

def alterar_preco():
    pid = get_id_selecionado()
    if pid is None: messagebox.showerror("Erro", "Selecione um produto."); return
    try:
        novo_preco = float(simpledialog.askstring("Alterar Preço", "Novo preço:"))
    except (TypeError, ValueError):
        messagebox.showerror("Erro", "Preço inválido."); return
    db("UPDATE produtos SET preco=? WHERE id=?", (novo_preco, pid), commit=True)
    atualizar_tabela()
    messagebox.showinfo("Sucesso", "Preço alterado!")

def estoque_baixo():
    produtos = db("SELECT nome, quantidade FROM produtos WHERE quantidade < 100", fetch="all")
    texto = "\n".join(f"• {n} (Qtd: {q})" for n, q in produtos) if produtos \
            else "Nenhum produto com estoque baixo."
    messagebox.showwarning("⚠ Estoque Baixo", texto)

def filtrar_categoria(cat):
    categoria_ativa.set(cat)
    atualizar_tabela()

def verificar_login():
    if db("SELECT id FROM usuarios WHERE usuario=? AND senha=?",
          (entry_usuario.get(), entry_senha.get()), fetch="one"):
        tela_login.destroy()
        janela.deiconify()
    else:
        messagebox.showerror("Erro", "Usuário ou senha incorretos.")

# ==========================================
# HOVER BOTÃO
# ==========================================

def criar_botao(pai, texto, comando, cor=COR_AZUL, **pack_opts):
    b = tk.Button(pai, text=texto, command=comando, bg=cor, fg="white",
                  activebackground=COR_AZUL_HOVER, activeforeground="white",
                  relief="flat", bd=0, cursor="hand2", font=("Segoe UI", 12, "bold"), height=2)
    b.pack(**pack_opts)
    b.bind("<Enter>", lambda e: e.widget.config(bg=COR_AZUL_HOVER))
    b.bind("<Leave>", lambda e: e.widget.config(bg=cor))
    return b

def criar_card(titulo_card, valor):
    frame = tk.Frame(frame_dashboard, bg=COR_CARD, width=220, height=100)
    frame.pack(side="left", padx=10)
    frame.pack_propagate(False)
    tk.Label(frame, text=titulo_card, bg=COR_CARD, fg=COR_SUBTEXTO,
             font=("Segoe UI", 11)).pack(pady=(15, 5))
    label = tk.Label(frame, text=valor, bg=COR_CARD, fg=COR_TEXTO,
                     font=("Segoe UI", 20, "bold"))
    label.pack()
    return label

# ==========================================
# TELA DE LOGIN
# ==========================================

janela.withdraw()
tela_login = tk.Toplevel()
tela_login.title("Login")
tela_login.geometry("400x400")
tela_login.configure(bg=COR_FUNDO)
tela_login.resizable(False, False)

frame_login = tk.Frame(tela_login, bg=COR_CARD, width=320, height=300)
frame_login.place(relx=0.5, rely=0.5, anchor="center")
frame_login.pack_propagate(False)

tk.Label(frame_login, text="🔐 LOGIN", bg=COR_CARD, fg="white",
         font=("Segoe UI", 22, "bold")).pack(pady=20)
entry_usuario = tk.Entry(frame_login, font=("Segoe UI", 12), width=25)
entry_usuario.pack(pady=15)
entry_senha = tk.Entry(frame_login, show="*", font=("Segoe UI", 12), width=25)
entry_senha.pack(pady=15)
criar_botao(frame_login, "Entrar", verificar_login, pady=25)

# ==========================================
# TÍTULO
# ==========================================

tk.Label(janela, text="🛒 SUPERMERCADO DASHBOARD", bg=COR_FUNDO, fg=COR_TEXTO,
         font=("Segoe UI", 26, "bold")).pack(pady=20)

# ==========================================
# FRAME PRINCIPAL
# ==========================================

frame_principal = tk.Frame(janela, bg=COR_FUNDO)
frame_principal.pack(fill="both", expand=True, padx=20, pady=10)

# ==========================================
# MENU LATERAL
# ==========================================

frame_menu = tk.Frame(frame_principal, bg=COR_MENU, width=260)
frame_menu.pack(side="left", fill="y", padx=(0, 20))

# ==========================================
# ÁREA DIREITA
# ==========================================

frame_direita = tk.Frame(frame_principal, bg=COR_FUNDO)
frame_direita.pack(side="right", fill="both", expand=True)

# ==========================================
# DASHBOARD
# ==========================================

frame_dashboard = tk.Frame(frame_direita, bg=COR_FUNDO)
frame_dashboard.pack(fill="x", pady=(0, 20))
total_produtos   = criar_card("Produtos", "0")
produtos_estoque = criar_card("Itens em Estoque", "0")
valor_estoque    = criar_card("Valor Total", "R$ 0")

# ==========================================
# PESQUISA E FILTROS
# ==========================================

frame_topo = tk.Frame(frame_direita, bg=COR_FUNDO)
frame_topo.pack(fill="x", pady=(0, 15))

campo_pesquisa = tk.Entry(frame_topo, font=("Segoe UI", 12), width=30, relief="flat")
campo_pesquisa.pack(side="left", ipady=8, padx=(0, 10))
campo_pesquisa.bind("<KeyRelease>", lambda e: atualizar_tabela())

tk.Button(frame_topo, text="🔍 Pesquisar", command=atualizar_tabela,
          bg=COR_AZUL, fg="white", relief="flat", bd=0, cursor="hand2",
          font=("Segoe UI", 10, "bold"), padx=15, pady=8).pack(side="left")

frame_filtros = tk.Frame(frame_topo, bg=COR_FUNDO)
frame_filtros.pack(side="right")

for texto, cat in [("📦 Todos","Todos"),("🍎 Frutas","Frutas"),
                   ("🥤 Bebidas","Bebidas"),("🧃 Refrigerantes","Refrigerantes")]:
    tk.Button(frame_filtros, text=texto, command=lambda c=cat: filtrar_categoria(c),
              bg=COR_CARD, fg="white", relief="flat", bd=0, cursor="hand2",
              font=("Segoe UI", 10, "bold"), padx=15, pady=8).pack(side="left", padx=5)

# ==========================================
# BOTÕES
# ==========================================

tk.Label(frame_menu, text="MENU", bg=COR_MENU, fg=COR_TEXTO,
         font=("Segoe UI", 20, "bold")).pack(pady=30)
criar_botao(frame_menu, "➕ Cadastrar Produto", cadastrar_produto, fill="x", padx=20, pady=10)
criar_botao(frame_menu, "💲 Alterar Preço",     alterar_preco,     fill="x", padx=20, pady=10)
criar_botao(frame_menu, "🗑 Remover Produto",   remover_produto,   fill="x", padx=20, pady=10)
criar_botao(frame_menu, "⚠ Estoque Baixo",     estoque_baixo,     fill="x", padx=20, pady=10)
criar_botao(frame_menu, "❌ Sair", janela.destroy, COR_VERMELHO,
            side="bottom", fill="x", padx=20, pady=20)

# ==========================================
# FRAME TABELA
# ==========================================

frame_tabela = tk.Frame(frame_direita, bg=COR_CARD)
frame_tabela.pack(fill="both", expand=True)

# ==========================================
# TABELA
# ==========================================

colunas = ("id", "Nome", "Preço", "Quantidade", "Categoria")
tabela  = ttk.Treeview(frame_tabela, columns=colunas, show="headings")
tabela.heading("id", text="")
tabela.column("id", width=0, stretch=False)
for col in colunas[1:]:
    tabela.heading(col, text=col)
    tabela.column(col, width=180, anchor="center")
tabela.pack(side="left", fill="both", expand=True)

# ==========================================
# SCROLLBAR
# ==========================================

scrollbar = ttk.Scrollbar(frame_tabela, orient="vertical", command=tabela.yview)
tabela.configure(yscroll=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# ==========================================
# INICIAR
# ==========================================

atualizar_tabela()
janela.mainloop()