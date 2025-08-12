# main.py
import os
from datetime import datetime
# Importa a função principal do nosso pacote de aplicação
from sync_app.services.sync_service import process_client

# O diretório raiz que contém as pastas de cada cliente
CLIENTS_ROOT_FOLDER = 'clients'

def main():
    """
    Ponto de entrada principal do script. Itera sobre as pastas de clientes
    e inicia o processo de sincronização para cada um.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    clients_path = os.path.join(base_dir, CLIENTS_ROOT_FOLDER)

    if not os.path.isdir(clients_path):
        print(f"ERRO CRÍTICO: Diretório de clientes '{clients_path}' não foi encontrado.")
        print("Por favor, crie o diretório 'clients' e adicione as pastas dos seus clientes dentro dele.")
        exit(1)

    print(f"\n{'='*70}\nIniciando processo de sincronização em {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n{'='*70}")
    
    client_folders = [name for name in os.listdir(clients_path) if os.path.isdir(os.path.join(clients_path, name))]

    if not client_folders:
        print(f"Nenhuma pasta de cliente encontrada no diretório '{clients_path}'. Encerrando.")
        return
        
    for client_name in client_folders:
        client_folder_path = os.path.join(clients_path, client_name)
        process_client(client_folder_path, client_name)

    print(f"\n{'='*70}\nProcesso de sincronização concluído para todos os clientes.\n{'='*70}")

if __name__ == '__main__':
    main()