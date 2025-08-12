# sync_app/services/freshdesk_service.py
import os
from ..core.network import api_request

def fetch_freshdesk_ticket_details(ticket_id, config):
    """
    Busca os detalhes completos de um ticket específico do Freshdesk, incluindo suas conversas.

    Args:
        ticket_id (int or str): O ID do ticket do Freshdesk.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        dict or None: O objeto completo do ticket ou None em caso de falha.
    """
    # Nota: a partir de versões mais recentes da API, incluir conversas aqui pode não ser o ideal.
    # A lógica de sincronização já busca as conversas separadamente para maior controle.
    url = f"https://{config['FRESHDESK_DOMAIN']}.freshdesk.com/api/v2/tickets/{ticket_id}?include=conversations"
    return api_request('GET', url, config['FRESHDESK_AUTH'])

def fetch_updated_freshdesk_tickets(since_date_str, config):
    """
    Busca tickets do Freshdesk atualizados desde uma data específica,
    com filtro opcional por ID da empresa.

    Args:
        since_date_str (str): Data no formato 'YYYY-MM-DD'.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        list: Uma lista de tickets do Freshdesk. Retorna lista vazia em caso de falha.
    """
    updated_since = f"{since_date_str}T00:00:00Z"
    url = f"https://{config['FRESHDESK_DOMAIN']}.freshdesk.com/api/v2/tickets"
    
    params = {
        'updated_since': updated_since,
        'order_by': 'updated_at',
        'order_type': 'desc'
    }
    
    # Se um ID de empresa for fornecido na configuração, adiciona ao filtro
    company_id = config.get('FRESHDESK_COMPANY_ID')
    if company_id:
        try:
            params['company_id'] = int(company_id)
            print(f"Filtrando tickets do Freshdesk para a empresa ID: {company_id}")
        except (ValueError, TypeError):
            print(f"AVISO: O valor de FRESHDESK_COMPANY_ID ('{company_id}') não é um número válido. O filtro será ignorado.")

    return api_request('GET', url, config['FRESHDESK_AUTH'], params=params) or []

def fetch_freshdesk_conversations(ticket_id, config):
    """
    Busca todas as conversas (notas, respostas) de um ticket do Freshdesk.

    Args:
        ticket_id (int or str): O ID do ticket do Freshdesk.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        list: Lista de conversas do ticket. Retorna lista vazia em caso de falha.
    """
    url = f"https://{config['FRESHDESK_DOMAIN']}.freshdesk.com/api/v2/tickets/{ticket_id}/conversations"
    return api_request('GET', url, config['FRESHDESK_AUTH']) or []

def add_freshdesk_note(ticket_id, note_text, config):
    """
    Adiciona uma nota privada a um ticket do Freshdesk.

    Args:
        ticket_id (int or str): O ID do ticket do Freshdesk.
        note_text (str): O conteúdo da nota (pode ser HTML).
        config (dict): O dicionário de configuração do cliente.

    Returns:
        dict or None: O objeto da nota criada ou None em caso de falha.
    """
    url = f"https://{config['FRESHDESK_DOMAIN']}.freshdesk.com/api/v2/tickets/{ticket_id}/notes"
    payload = {'body': note_text, 'private': True}
    print(f"Adicionando nota privada ao Freshdesk {ticket_id}...")
    return api_request('POST', url, config['FRESHDESK_AUTH'], json_data=payload)

def add_freshdesk_attachment(ticket_id, file_path, config):
    """
    Adiciona um anexo a um ticket do Freshdesk, criando uma nota privada associada.

    Args:
        ticket_id (int or str): O ID do ticket do Freshdesk.
        file_path (str): O caminho do arquivo a ser enviado.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        bool: True se o anexo foi enviado com sucesso, False caso contrário.
    """
    url = f"https://{config['FRESHDESK_DOMAIN']}.freshdesk.com/api/v2/tickets/{ticket_id}/notes"
    
    # Cria um corpo de nota para contextualizar o anexo
    body_text = f"[Anexo Sincronizado do Jira] {os.path.basename(file_path)}"
    data = {'body': body_text, 'private': 'true'}
    
    try:
        with open(file_path, 'rb') as f:
            files = {'attachments[]': (os.path.basename(file_path), f, 'application/octet-stream')}
            # Usa a api_request genérica para o upload
            success = api_request('POST', url, config['FRESHDESK_AUTH'], data=data, files=files)
        
        if success:
            print(f"Anexo '{os.path.basename(file_path)}' enviado para o Freshdesk {ticket_id} com sucesso.")
            return True
        else:
            print(f"Falha ao enviar anexo para o Freshdesk {ticket_id}.")
            return False
            
    except Exception as e:
        print(f"ERRO INESPERADO ao tentar enviar anexo para o Freshdesk {ticket_id}: {e}")
        return False
    
def update_freshdesk_ticket_status(ticket_id, status_code, config):
    """
    Atualiza o status de um ticket no Freshdesk usando um código de status numérico.

    Args:
        ticket_id (int or str): O ID do ticket do Freshdesk.
        status_code (int): O código numérico do status do Freshdesk (e.g., 4 para Resolvido).
        config (dict): O dicionário de configuração do cliente.

    Returns:
        dict or None: A resposta da API em caso de sucesso, None em caso de erro.
    """
    url = f"https://{config['FRESHDESK_DOMAIN']}.freshdesk.com/api/v2/tickets/{ticket_id}"
    
    # A API do Freshdesk espera um payload com a chave 'status' e o valor numérico.
    payload = {'status': status_code}
    
    print(f"Atualizando status do ticket Freshdesk {ticket_id} para o código {status_code}...")
    
    # A atualização de ticket usa o método PUT.
    return api_request('PUT', url, config['FRESHDESK_AUTH'], json_data=payload)
