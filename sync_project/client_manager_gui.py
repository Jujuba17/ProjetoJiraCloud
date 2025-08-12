import tkinter as tk
from tkinter import ttk, messagebox
import json
import os
import requests
import shutil
from requests.auth import HTTPBasicAuth
import datetime

# --- LÓGICA DE TESTE DE CONEXÃO ---
# (Sem alterações aqui, a lógica de teste principal permanece a mesma)
def test_jira_connection(url, user_email, api_token, project_key):
    """Testa a conexão com o Jira e retorna (status, mensagem)."""
    if not all([url, user_email, api_token, project_key]):
        return False, "Todos os campos do Jira devem ser preenchidos."
    try:
        response = requests.get(
            f"{url}/rest/api/3/project/{project_key}",
            headers={"Accept": "application/json"},
            auth=HTTPBasicAuth(user_email, api_token),
            timeout=10
        )
        response.raise_for_status()
        return True, "Jira: Conexão bem-sucedida."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return False, "Jira: Falha na autenticação (Email ou Token inválido)."
        if e.response.status_code == 404:
            return False, f"Jira: Conexão OK, mas o projeto '{project_key}' não foi encontrado."
        return False, f"Jira: Erro HTTP - {e}"
    except requests.exceptions.RequestException as e:
        return False, f"Jira: Erro de Conexão - {e}"

def test_freshdesk_connection(domain, api_key):
    """Testa a conexão com o Freshdesk e retorna (status, mensagem)."""
    if not all([domain, api_key]):
        return False, "Todos os campos do Freshdesk devem ser preenchidos."
    try:
        response = requests.get(
            f"https://{domain}.freshdesk.com/api/v2/tickets?per_page=1",
            auth=(api_key, "X"),
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()
        return True, "Freshdesk: Conexão bem-sucedida."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return False, "Freshdesk: Falha na autenticação (Domínio ou Chave da API inválida)."
        return False, f"Freshdesk: Erro HTTP - {e}"
    except requests.exceptions.RequestException as e:
        return False, f"Freshdesk: Erro de Conexão - {e}"

# --- FUNÇÕES DA INTERFACE GRÁFICA ---

def edit_client_window(client_name, on_close_callback):
    """
    [ATUALIZADO] Abre a janela de edição com os campos finais.
    """
    config_path = os.path.join('clients', client_name, 'config.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        messagebox.showerror("Erro de Leitura", f"Não foi possível ler o arquivo de configuração: {e}")
        return

    edit_window = tk.Toplevel(root)
    edit_window.title(f"Editando Cliente: {client_name}")
    edit_window.geometry("650x620") # Altura ajustada

    frame = ttk.Frame(edit_window, padding="10")
    frame.pack(fill="both", expand=True)

    entries = {}
    labels_and_keys = {
        # Jira
        "URL do Jira:": "JIRA_URL", "Email do Usuário Jira:": "JIRA_USER_EMAIL",
        "Token da API Jira:": "JIRA_API_TOKEN", "Chave do Projeto Jira:": "JIRA_PROJECT_KEY",
        # Freshdesk
        "Domínio do Freshdesk:": "FRESHDESK_DOMAIN", "Chave da API Freshdesk:": "FRESHDESK_API_KEY",
        "ID da Companhia no Freshdesk (Opcional):": "FRESHDESK_COMPANY_ID"
    }

    ttk.Label(frame, text="Nome do Cliente:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky="w", pady=2)
    ttk.Label(frame, text=client_name).grid(row=0, column=1, sticky="w", pady=2)
    current_row = 1

    for text, key in labels_and_keys.items():
        ttk.Label(frame, text=text).grid(row=current_row, column=0, sticky="w", pady=2)
        entry = ttk.Entry(frame, width=70)
        value = config.get(key)
        entry.insert(0, str(value) if value is not None else "")
        entry.grid(row=current_row, column=1, sticky="ew", pady=2)
        entries[key] = entry
        current_row += 1

    ttk.Separator(frame, orient='horizontal').grid(row=current_row, columnspan=2, sticky='ew', pady=10)
    current_row += 1

    # Checkboxes de Sincronização
    checkbox_vars = {
        "SYNC_STATUS_JIRA_TO_FRESHDESK": tk.BooleanVar(value=config.get("SYNC_STATUS_JIRA_TO_FRESHDESK", False)),
        "SYNC_COMMENTS_JIRA_TO_FRESHDESK": tk.BooleanVar(value=config.get("SYNC_COMMENTS_JIRA_TO_FRESHDESK", False)),
        "SYNC_COMMENTS_FRESHDESK_TO_JIRA": tk.BooleanVar(value=config.get("SYNC_COMMENTS_FRESHDESK_TO_JIRA", False)),
        "SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK": tk.BooleanVar(value=config.get("SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK", False)),
        "SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA": tk.BooleanVar(value=config.get("SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA", False))
    }
    
    ttk.Label(frame, text="Opções de Sincronização", font=("Arial", 10, "bold")).grid(row=current_row, columnspan=2, sticky="w", pady=(5, 0))
    current_row += 1

    ttk.Checkbutton(frame, text="Sincronizar Status (Jira -> Freshdesk)", variable=checkbox_vars["SYNC_STATUS_JIRA_TO_FRESHDESK"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Comentários (Jira -> Freshdesk)", variable=checkbox_vars["SYNC_COMMENTS_JIRA_TO_FRESHDESK"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Comentários (Freshdesk -> Jira)", variable=checkbox_vars["SYNC_COMMENTS_FRESHDESK_TO_JIRA"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Anexos (Jira -> Freshdesk)", variable=checkbox_vars["SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Anexos (Freshdesk -> Jira)", variable=checkbox_vars["SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1

    def test_form_connection():
        jira_status, jira_msg = test_jira_connection(
            entries["JIRA_URL"].get(), entries["JIRA_USER_EMAIL"].get(),
            entries["JIRA_API_TOKEN"].get(), entries["JIRA_PROJECT_KEY"].get()
        )
        fd_status, fd_msg = test_freshdesk_connection(
            entries["FRESHDESK_DOMAIN"].get(), entries["FRESHDESK_API_KEY"].get()
        )
        message = f"{jira_msg}\n{fd_msg}"
        if jira_status and fd_status: messagebox.showinfo("Resultado do Teste", message, parent=edit_window)
        else: messagebox.showerror("Resultado do Teste", message, parent=edit_window)

    def save_changes():
        new_config = {}
        
        for key, entry in entries.items():
            new_config[key] = entry.get().strip()
        
        try:
            company_id_str = new_config["FRESHDESK_COMPANY_ID"]
            new_config["FRESHDESK_COMPANY_ID"] = int(company_id_str) if company_id_str else None
        except ValueError:
            messagebox.showerror("Erro de Validação", "O ID da Companhia deve ser um número válido.", parent=edit_window)
            return
            
        for key, var in checkbox_vars.items():
            new_config[key] = var.get()
            
        new_config["CLIENT_NAME"] = client_name

        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(new_config, f, indent=4)
            messagebox.showinfo("Sucesso", f"Cliente '{client_name}' atualizado com sucesso!", parent=edit_window)
            edit_window.destroy()
            on_close_callback()
        except Exception as e:
            messagebox.showerror("Erro de Arquivo", f"Não foi possível salvar as alterações: {e}", parent=edit_window)

    button_frame = ttk.Frame(frame)
    button_frame.grid(row=current_row, columnspan=2, pady=20)
    ttk.Button(button_frame, text="Testar Conexão", command=test_form_connection).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Salvar Alterações", command=save_changes).pack(side="left", padx=10)


def delete_client(client_name, client_frame, on_delete_callback):
    """Pede confirmação e deleta o cliente."""
    if messagebox.askyesno("Confirmar Exclusão", f"Você tem certeza que deseja excluir o cliente '{client_name}'?", icon='warning'):
        try:
            shutil.rmtree(os.path.join('clients', client_name))
            client_frame.destroy()
            on_delete_callback()
            messagebox.showinfo("Sucesso", f"Cliente '{client_name}' excluído com sucesso.")
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível excluir o cliente: {e}")

def list_clients():
    """Abre a janela para listar, editar, excluir e TESTAR clientes."""
    list_window = tk.Toplevel(root)
    list_window.title("Clientes Cadastrados")
    list_window.geometry("600x500")

    main_frame = ttk.Frame(list_window)
    main_frame.pack(fill="both", expand=True)

    def refresh_list():
        for widget in scrollable_frame.winfo_children(): widget.destroy()
        populate_list()
        update_scroll_region()

    header_frame = ttk.Frame(main_frame, padding=5)
    header_frame.pack(fill="x", side="top")
    ttk.Label(header_frame, text="Clientes:", font=("Arial", 12, "bold")).pack(side="left")
    ttk.Button(header_frame, text="Adicionar Novo", command=lambda: open_new_client_window(refresh_list)).pack(side="right")
    
    ttk.Separator(main_frame).pack(fill='x', pady=5)
    
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    def update_scroll_region():
        canvas.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))

    def test_saved_config(client_name):
        config_path = os.path.join('clients', client_name, 'config.json')
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except Exception as e:
            messagebox.showerror("Erro", f"Não foi possível ler o config.json: {e}", parent=list_window)
            return

        jira_status, jira_msg = test_jira_connection(
            config.get("JIRA_URL"), config.get("JIRA_USER_EMAIL"),
            config.get("JIRA_API_TOKEN"), config.get("JIRA_PROJECT_KEY")
        )
        fd_status, fd_msg = test_freshdesk_connection(
            config.get("FRESHDESK_DOMAIN"), config.get("FRESHDESK_API_KEY")
        )

        message = f"Cliente: {client_name}\n\n{jira_msg}\n{fd_msg}"
        if jira_status and fd_status: messagebox.showinfo("Resultado do Teste", message, parent=list_window)
        else: messagebox.showerror("Resultado do Teste", message, parent=list_window)

    def populate_list():
        try:
            clients_dir = 'clients'
            if not os.path.exists(clients_dir):
                os.makedirs(clients_dir)
            clients = sorted([f for f in os.listdir(clients_dir) if os.path.isdir(os.path.join(clients_dir, f))])
        except Exception:
            clients = []

        if not clients:
            ttk.Label(scrollable_frame, text="Nenhum cliente cadastrado.", padding=10).pack()
            return

        for client_name in clients:
            client_frame = ttk.Frame(scrollable_frame, padding=5, relief="groove", borderwidth=1)
            client_frame.pack(fill="x", expand=True, padx=10, pady=5)
            
            ttk.Label(client_frame, text=client_name, font=("Arial", 11, "bold")).pack(side="left", padx=10)
            delete_btn = ttk.Button(client_frame, text="Excluir", command=lambda name=client_name, frame=client_frame: delete_client(name, frame, update_scroll_region))
            delete_btn.pack(side="right", padx=5)
            edit_btn = ttk.Button(client_frame, text="Editar", command=lambda name=client_name: edit_client_window(name, refresh_list))
            edit_btn.pack(side="right", padx=5)
            test_btn = ttk.Button(client_frame, text="Testar", command=lambda name=client_name: test_saved_config(name))
            test_btn.pack(side="right", padx=5)

    populate_list()
    update_scroll_region()

def open_new_client_window(on_close_callback=None):
    """
    [ATUALIZADO] Abre a janela para criar um novo cliente com a estrutura de config final.
    """
    new_window = tk.Toplevel(root)
    new_window.title("Cadastrar Novo Cliente")
    new_window.geometry("650x620") # Altura ajustada
    
    if on_close_callback:
        new_window.protocol("WM_DELETE_WINDOW", lambda: (on_close_callback(), new_window.destroy()))

    frame = ttk.Frame(new_window, padding="10")
    frame.pack(fill="both", expand=True)

    entries = {}
    labels = {
        "CLIENT_NAME": "Nome do Cliente (sem espaços):",
        "JIRA_URL": "URL do Jira:", "JIRA_USER_EMAIL": "Email do Usuário Jira:",
        "JIRA_API_TOKEN": "Token da API Jira:", "JIRA_PROJECT_KEY": "Chave do Projeto Jira:",
        "FRESHDESK_DOMAIN": "Domínio do Freshdesk:", "FRESHDESK_API_KEY": "Chave da API Freshdesk:",
        "FRESHDESK_COMPANY_ID": "ID da Companhia no Freshdesk (Opcional):"
    }

    current_row = 0
    for key, text in labels.items():
        ttk.Label(frame, text=text).grid(row=current_row, column=0, sticky="w", pady=2)
        entry = ttk.Entry(frame, width=70)
        entry.grid(row=current_row, column=1, sticky="ew", pady=2)
        entries[key] = entry
        current_row += 1
    
    ttk.Separator(frame, orient='horizontal').grid(row=current_row, columnspan=2, sticky='ew', pady=10)
    current_row += 1

    # Checkboxes de Sincronização
    checkbox_vars = {
        "SYNC_STATUS_JIRA_TO_FRESHDESK": tk.BooleanVar(value=False),
        "SYNC_COMMENTS_JIRA_TO_FRESHDESK": tk.BooleanVar(value=False),
        "SYNC_COMMENTS_FRESHDESK_TO_JIRA": tk.BooleanVar(value=False),
        "SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK": tk.BooleanVar(value=False),
        "SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA": tk.BooleanVar(value=False)
    }
    
    ttk.Label(frame, text="Opções de Sincronização", font=("Arial", 10, "bold")).grid(row=current_row, columnspan=2, sticky="w", pady=(5, 0))
    current_row += 1
    
    ttk.Checkbutton(frame, text="Sincronizar Status (Jira -> Freshdesk)", variable=checkbox_vars["SYNC_STATUS_JIRA_TO_FRESHDESK"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Comentários (Jira -> Freshdesk)", variable=checkbox_vars["SYNC_COMMENTS_JIRA_TO_FRESHDESK"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Comentários (Freshdesk -> Jira)", variable=checkbox_vars["SYNC_COMMENTS_FRESHDESK_TO_JIRA"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Anexos (Jira -> Freshdesk)", variable=checkbox_vars["SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1
    ttk.Checkbutton(frame, text="Sincronizar Anexos (Freshdesk -> Jira)", variable=checkbox_vars["SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA"]).grid(row=current_row, columnspan=2, pady=2, sticky="w")
    current_row += 1

    def test_current_connection():
        jira_status, jira_msg = test_jira_connection(entries["JIRA_URL"].get(), entries["JIRA_USER_EMAIL"].get(), entries["JIRA_API_TOKEN"].get(), entries["JIRA_PROJECT_KEY"].get())
        fd_status, fd_msg = test_freshdesk_connection(entries["FRESHDESK_DOMAIN"].get(), entries["FRESHDESK_API_KEY"].get())
        message = f"{jira_msg}\n{fd_msg}"
        if jira_status and fd_status: messagebox.showinfo("Resultado do Teste", message, parent=new_window)
        else: messagebox.showerror("Resultado do Teste", message, parent=new_window)

    def save_client():
        config_data = {}
        client_name = entries["CLIENT_NAME"].get().strip()
        
        if not client_name or ' ' in client_name:
            messagebox.showerror("Erro", "Nome do cliente é obrigatório e não pode conter espaços.", parent=new_window)
            return
            
        for key, entry in entries.items():
            config_data[key] = entry.get().strip()

        required_fields = ["JIRA_URL", "JIRA_USER_EMAIL", "JIRA_API_TOKEN", "JIRA_PROJECT_KEY", 
                           "FRESHDESK_DOMAIN", "FRESHDESK_API_KEY"]
        if not all(config_data.get(f) for f in required_fields):
             messagebox.showerror("Erro", "Todos os campos de texto (exceto ID da Companhia) são obrigatórios.", parent=new_window)
             return

        try:
            company_id_str = config_data["FRESHDESK_COMPANY_ID"]
            config_data["FRESHDESK_COMPANY_ID"] = int(company_id_str) if company_id_str else None
        except ValueError:
            messagebox.showerror("Erro de Validação", "O ID da Companhia deve ser um número válido.", parent=new_window)
            return

        client_path = os.path.join('clients', client_name)
        if os.path.exists(client_path):
            messagebox.showerror("Erro", f"Cliente '{client_name}' já existe.", parent=new_window)
            return

        for key, var in checkbox_vars.items():
            config_data[key] = var.get()

        try:
            if not os.path.exists('clients'):
                os.makedirs('clients')
            os.makedirs(client_path)
            with open(os.path.join(client_path, 'config.json'), 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4)
            messagebox.showinfo("Sucesso", f"Cliente '{client_name}' salvo!", parent=new_window)
            new_window.destroy()
            if on_close_callback: on_close_callback()
        except Exception as e:
            messagebox.showerror("Erro de Arquivo", f"Não foi possível salvar: {e}", parent=new_window)
    
    button_frame = ttk.Frame(frame)
    button_frame.grid(row=current_row, columnspan=2, pady=20)
    ttk.Button(button_frame, text="Testar Conexão", command=test_current_connection).pack(side="left", padx=10)
    ttk.Button(button_frame, text="Salvar Cliente", command=save_client).pack(side="left", padx=10)

# --- Janela Principal ---
root = tk.Tk()
root.title("Gerenciador de Clientes - Sincronizador")
root.geometry("450x250")
root.eval('tk::PlaceWindow . center')

style = ttk.Style(root)
style.theme_use('clam')

main_frame = ttk.Frame(root, padding=20)
main_frame.pack(expand=True, fill="both")

ttk.Label(main_frame, text="Gerenciador de Clientes", font=("Arial", 16, "bold")).pack(pady=10)
ttk.Button(main_frame, text="Gerenciar Clientes", command=list_clients, width=30).pack(pady=10, ipady=5)

root.mainloop()