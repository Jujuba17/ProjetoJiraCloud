# sync_app/storage/file_storage.py
import json
import os
from datetime import datetime, timezone

def load_client_config(config_path):
    """
    Carrega o arquivo de configuração do cliente (config.json).
    Se o 'FIRST_RUN_TIMESTAMP' não existir, ele é adicionado e o arquivo é salvo.

    Args:
        config_path (str): O caminho para o arquivo config.json.

    Returns:
        dict or None: O dicionário de configuração ou None se o arquivo não existir.
    """
    if not os.path.exists(config_path):
        print(f"AVISO: '{os.path.basename(config_path)}' não encontrado. Pulando.")
        return None

    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Se for a primeira execução para este cliente, registra o timestamp
    if 'FIRST_RUN_TIMESTAMP' not in config:
        now_iso = datetime.now(timezone.utc).isoformat()
        config['FIRST_RUN_TIMESTAMP'] = now_iso
        print(f"PRIMEIRA EXECUÇÃO DETECTADA. Registrando data de corte: {now_iso}")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
            
    return config

def load_mapping_data(mapping_path):
    """
    Carrega o arquivo de mapeamento de tickets (mapping.json).

    Args:
        mapping_path (str): O caminho para o arquivo mapping.json.

    Returns:
        dict: O dicionário de mapeamento. Retorna um dicionário vazio se
              o arquivo não existir ou estiver corrompido.
    """
    mapping_data = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r', encoding='utf-8') as f:
            try:
                mapping_data = json.load(f)
            except json.JSONDecodeError:
                print(f"AVISO: '{os.path.basename(mapping_path)}' corrompido. Iniciando um novo.")
    else:
        print(f"AVISO: '{os.path.basename(mapping_path)}' não encontrado. Um novo será criado.")
    return mapping_data

def save_mapping_data(mapping_path, mapping_data):
    """
    Salva os dados de mapeamento em um arquivo JSON.

    Args:
        mapping_path (str): O caminho onde o arquivo mapping.json será salvo.
        mapping_data (dict): O dicionário de mapeamento a ser salvo.
    """
    try:
        with open(mapping_path, 'w', encoding='utf-8') as f:
            json.dump(mapping_data, f, indent=4)
        print(f"Mapeamento salvo com sucesso em {mapping_path}")
    except Exception as e:
        print(f"ERRO CRÍTICO: Falha ao salvar o arquivo de mapeamento em {mapping_path}. Detalhes: {e}")