# sync_app/services/jira_service.py
import os
import requests
from ..core.network import api_request
from ..core.utils import html_to_text

def create_jira_ticket(freshdesk_ticket, config):
    """
    Cria um novo ticket no Jira com base em um ticket do Freshdesk.

    Args:
        freshdesk_ticket (dict): O objeto completo do ticket do Freshdesk.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        dict or None: O objeto do ticket criado no Jira ou None em caso de falha.
    """
    url = f"{config['JIRA_URL']}/rest/api/3/issue"
    description_plain = html_to_text(freshdesk_ticket.get('description', 'Descrição não fornecida.'))
    
    # Converte a descrição para o formato Atlassian Document Format (ADF)
    adf_description = {
        "type": "doc",
        "version": 1,
        "content": [{"type": "paragraph", "content": [{"type": "text", "text": description_plain}]}]
    }
    
    # Mapeia a prioridade do Freshdesk para a prioridade do Jira
    fd_priority_code = str(freshdesk_ticket.get('priority', 2)) # Padrão para 'Média'
    jira_priority_name = config.get('FRESHDESK_TO_JIRA_PRIORITY', {}).get(fd_priority_code, 'Medium')
    
    payload = {
        "fields": {
            "project": {"key": config['JIRA_PROJECT_KEY']},
            "issuetype": {"name": config.get('JIRA_DEFAULT_ISSUE_TYPE', 'Task')},
            "summary": freshdesk_ticket.get('subject', 'Sem assunto'),
            "description": adf_description,
            "priority": {"name": jira_priority_name}
        }
    }
    print(f"Criando ticket no Jira para o Freshdesk {freshdesk_ticket['id']}...")
    return api_request('POST', url, config['JIRA_AUTH'], json_data=payload)

def fetch_updated_jira_tickets(since_date_str, config):
    """
    Busca tickets do Jira atualizados desde uma data específica.

    Args:
        since_date_str (str): Data no formato 'YYYY-MM-DD'.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        list: Uma lista de tickets do Jira. Retorna lista vazia em caso de falha.
    """
    jql_query = f"project = '{config['JIRA_PROJECT_KEY']}' AND updated >= '{since_date_str}' ORDER BY updated DESC"
    url = f"{config['JIRA_URL']}/rest/api/3/search"
    params = {
        'jql': jql_query,
        'fields': 'summary,description,status,comment,updated,created,priority,attachment'
    }
    response_data = api_request('GET', url, config['JIRA_AUTH'], params=params)
    return response_data.get('issues', []) if response_data else []

def add_jira_comment(issue_key, comment_text, config):
    """
    Adiciona um comentário a um ticket existente no Jira.

    Args:
        issue_key (str): A chave do ticket do Jira (e.g., 'PROJ-123').
        comment_text (str): O texto do comentário a ser adicionado.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        dict or None: O objeto do comentário criado ou None em caso de falha.
    """
    url = f"{config['JIRA_URL']}/rest/api/3/issue/{issue_key}/comment"
    # O corpo do comentário deve estar no formato ADF
    payload = {
        "body": {
            "type": "doc",
            "version": 1,
            "content": [{"type": "paragraph", "content": [{"type": "text", "text": comment_text}]}]
        }
    }
    print(f"Adicionando comentário ao Jira {issue_key}...")
    return api_request('POST', url, config['JIRA_AUTH'], json_data=payload)

def add_jira_attachment(issue_key, file_path, config):
    """
    Envia um anexo para um ticket do Jira.
    Esta função usa 'requests' diretamente pois a API de anexo do Jira tem um comportamento específico.

    Args:
        issue_key (str): A chave do ticket do Jira.
        file_path (str): O caminho do arquivo a ser enviado.
        config (dict): O dicionário de configuração do cliente.

    Returns:
        str or None: O ID do anexo criado no Jira ou None em caso de falha.
    """
    url = f"{config['JIRA_URL']}/rest/api/3/issue/{issue_key}/attachments"
    headers = {"X-Atlassian-Token": "no-check"}
    
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'application/octet-stream')}
            response = requests.post(url, headers=headers, files=files, auth=config['JIRA_AUTH'])
            response.raise_for_status()
            
            attachment_info = response.json()
            if attachment_info and isinstance(attachment_info, list):
                jira_attachment_id = attachment_info[0]['id']
                print(f"Anexo '{os.path.basename(file_path)}' enviado para o Jira {issue_key} com sucesso. ID: {jira_attachment_id}")
                return jira_attachment_id
            else:
                print(f"ERRO: A API do Jira não retornou a informação esperada para o anexo em {issue_key}.")
                return None
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao enviar anexo para o Jira {issue_key}. Detalhes: {e.response.text if e.response else e}")
        return None