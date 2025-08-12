# sync_app/services/sync_service.py
import os
from datetime import datetime, timezone, timedelta
from requests.auth import HTTPBasicAuth

# Importa os serviços e módulos necessários
from . import freshdesk_service, jira_service
from ..core import utils, network
from ..storage import file_storage

def get_temp_attachments_dir(client_name):
    """Cria e retorna o caminho para o diretório de anexos temporários."""
    # O diretório base para os clientes agora é 'clients'
    temp_dir = os.path.join('clients', client_name, 'temp_attachments')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def _sync_jira_to_freshdesk(jira_tickets, mapping, config):
    """Lógica interna para sincronizar atualizações do Jira para o Freshdesk."""
    print("\n--- Sincronizando Jira -> Freshdesk (para tickets mapeados) ---")
    for jira_ticket in jira_tickets:
        jira_key = jira_ticket['key']
        if jira_key not in mapping:
            continue

        mapping_entry = mapping[jira_key]
        mapping_entry.setdefault('synced_attachments', [])
        
        last_sync = utils.parse_datetime(mapping_entry.get('last_jira_update'))
        jira_updated_at = utils.parse_datetime(jira_ticket['fields']['updated'])
        
        if last_sync and jira_updated_at and jira_updated_at <= last_sync:
            continue

        fd_id = mapping_entry['freshdesk_id']
        print(f"Verificando atualizações no Freshdesk {fd_id} com base no Jira {jira_key}...")

        # Sincronizar comentários
        if config.get('SYNC_COMMENTS_JIRA_TO_FRESHDESK', True):
            for comment in jira_ticket['fields'].get('comment', {}).get('comments', []):
                comment_updated_at = utils.parse_datetime(comment['updated'])
                if not last_sync or (comment_updated_at and comment_updated_at > last_sync):
                    try:
                        comment_body = comment['body']['content'][0]['content'][0]['text']
                    except (KeyError, IndexError):
                        comment_body = "Não foi possível extrair o conteúdo."

                    # VERIFICA SE O COMENTÁRIO DO JIRA JÁ FOI ORIGINADO DO FRESHDESK para evitar loops.
                    if "no Freshdesk:_" in comment_body:
                        print(f"  -> Pulando comentário do Jira {comment['id']} (origem: Freshdesk).")
                        continue

                    comment_author = comment['author']['displayName']
                    note = f"<i>Comentário de <b>{comment_author}</b> no Jira:</i><br><hr>{comment_body}"
                    freshdesk_service.add_freshdesk_note(fd_id, note, config)
        
        # Sincronizar anexos
        if config.get('SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK', True):
            temp_dir = get_temp_attachments_dir(config['CLIENT_NAME'])
            for attachment in jira_ticket['fields'].get('attachment', []):
                attachment_id = f"jira-{attachment['id']}"
                if attachment_id in mapping_entry['synced_attachments']:
                    continue
                
                print(f"Novo anexo detectado no Jira {jira_key}: {attachment['filename']}")
                file_path = os.path.join(temp_dir, attachment['filename'])
                if network.download_attachment(attachment['content'], file_path, auth=config['JIRA_AUTH']):
                    if freshdesk_service.add_freshdesk_attachment(fd_id, file_path, config):
                        mapping_entry['synced_attachments'].append(attachment_id)
                    os.remove(file_path)

        # ==================================================================
        # <<< INÍCIO DA LÓGICA DE SINCRONIZAÇÃO DE STATUS (COM MAPA EMBUTIDO) >>>
        # ==================================================================
        # 1. Verifica no config.json se a funcionalidade está LIGADA.
        if config.get('SYNC_STATUS_JIRA_TO_FRESHDESK', False):
            # Mapa de status embutido no código.
            # Chave: Nome do Status no Jira (sensível a maiúsculas/minúsculas)
            # Valor: Código numérico do Status no Freshdesk
            status_map_embedded = {
                "Done": 4,         # 4 = Resolvido
                "Concluído": 4,    # 4 = Resolvido
                "Resolved": 4,     # 4 = Resolvido
                "Closed": 5,       # 5 = Fechado
                "Fechado": 5       # 5 = Fechado
            }
            
            # Pega o nome exato do status vindo do Jira
            jira_status_name = jira_ticket['fields']['status']['name']
            print(f"  [Status Sync] Status atual do Jira {jira_key}: '{jira_status_name}'")
            
            # 2. Verifica se o nome do status do Jira está nas chaves do nosso mapa
            if jira_status_name in status_map_embedded:
                freshdesk_status_code = status_map_embedded[jira_status_name]
                
                print(f"  [Status Sync] Status '{jira_status_name}' encontrado no mapa. Mapeado para código Freshdesk: {freshdesk_status_code}.")
                print(f"  [Status Sync] Tentando atualizar o status do Freshdesk ticket {fd_id}...")
                
                # 3. Chama o serviço para atualizar o status no Freshdesk
                response = freshdesk_service.update_freshdesk_ticket_status(fd_id, freshdesk_status_code, config)
                
                # 4. Verifica o resultado da chamada à API para feedback
                if response:
                    print(f"  [Status Sync] SUCESSO: Status do Freshdesk {fd_id} atualizado.")
                else:
                    print(f"  [Status Sync] FALHA: Não foi possível atualizar o status do Freshdesk {fd_id}. Verifique os logs de erro da API acima.")
            else:
                # Log para nos ajudar a identificar nomes de status que precisam ser adicionados ao mapa
                print(f"  [Status Sync] AVISO: Status do Jira '{jira_status_name}' não está no mapa de sincronização. Nenhuma ação será tomada.")
        # ==================================================================
        # <<< FIM DA LÓGICA DE SINCRONIZAÇÃO DE STATUS >>>
        # ==================================================================

        mapping_entry['last_jira_update'] = jira_updated_at.isoformat()

def _sync_freshdesk_to_jira(freshdesk_tickets, mapping, config):
    """Lógica interna para sincronizar atualizações do Freshdesk para o Jira."""
    fd_id_to_jira_key = {str(v['freshdesk_id']): k for k, v in mapping.items()}
    print("\n--- Sincronizando Freshdesk -> Jira (para tickets mapeados) ---")
    for fd_ticket in freshdesk_tickets:
        fd_id_str = str(fd_ticket['id'])
        if fd_id_str not in fd_id_to_jira_key:
            continue

        jira_key = fd_id_to_jira_key[fd_id_str]
        mapping_entry = mapping[jira_key]
        mapping_entry.setdefault('synced_attachments', [])

        last_sync = utils.parse_datetime(mapping_entry.get('last_freshdesk_update'))
        fd_updated_at = utils.parse_datetime(fd_ticket['updated_at'])

        if last_sync and fd_updated_at and fd_updated_at <= last_sync:
            continue

        print(f"Atualizando Jira {jira_key} com base no Freshdesk {fd_id_str}...")
        
        # Busca as conversas para obter notas, respostas e anexos
        for conv in freshdesk_service.fetch_freshdesk_conversations(fd_id_str, config):
            # ==================================================================
            # <<< INÍCIO DA CORREÇÃO >>>
            # ==================================================================
            # VERIFICA SE A CONVERSA FOI ORIGINALMENTE SINCRONIZADA DO JIRA.
            # A verificação é feita no corpo HTML ('body') porque é onde inserimos a tag <i>.
            if "<i>Comentário de" in conv.get('body', ''):
                # Se o marcador for encontrado, pulamos esta conversa para evitar o loop.
                print(f"  -> Pulando conversa {conv['id']} (origem: Jira).")
                continue
            # ==================================================================
            # <<< FIM DA CORREÇÃO >>>
            # ==================================================================
            
            conv_updated_at = utils.parse_datetime(conv['updated_at'])
            if not last_sync or (conv_updated_at and conv_updated_at > last_sync):
                user_name = conv.get('user', {}).get('name', 'Usuário Desconhecido')
                body_text = conv.get('body_text', '').strip()
                
                # Sincronizar comentários/notas
                if config.get('SYNC_COMMENTS_FRESHDESK_TO_JIRA', True) and body_text:
                    note_type = "Nota Privada" if conv.get('private', True) else "Resposta Pública"
                    comment_text = f"_{note_type} de **{user_name}** no Freshdesk:_\n\n{body_text}"
                    jira_service.add_jira_comment(jira_key, comment_text, config)

                # Sincronizar anexos da conversa
                if config.get('SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA', True) and conv.get('attachments'):
                    temp_dir = get_temp_attachments_dir(config['CLIENT_NAME'])
                    for attachment in conv['attachments']:
                        attachment_id_fd = f"fd-{attachment['id']}"
                        if attachment_id_fd in mapping_entry['synced_attachments']:
                            continue
                        
                        print(f"  -> Novo anexo detectado no Freshdesk {fd_id_str}: {attachment['name']}")
                        file_path = os.path.join(temp_dir, attachment['name'])
                        if network.download_attachment(attachment['attachment_url'], file_path):
                            jira_attachment_id = jira_service.add_jira_attachment(jira_key, file_path, config)
                            if jira_attachment_id:
                                # Registra ambos os IDs para criar o vínculo
                                attachment_id_jira = f"jira-{jira_attachment_id}"
                                mapping_entry['synced_attachments'].append(attachment_id_fd)
                                mapping_entry['synced_attachments'].append(attachment_id_jira)
                                print(f"  -> Anexo {attachment_id_fd} mapeado para {attachment_id_jira}.")
                            os.remove(file_path)

        mapping_entry['last_freshdesk_update'] = fd_updated_at.isoformat()

  

def _find_and_map_new_freshdesk_tickets(freshdesk_tickets, mapping, config):
    """Encontra novos tickets no Freshdesk e os cria no Jira, atualizando o mapeamento."""
    print("\n--- Verificando tickets do Freshdesk para criação no Jira ---")
    existing_fd_ids = {str(v['freshdesk_id']) for v in mapping.values()}
    
    first_run_timestamp_str = config.get('FIRST_RUN_TIMESTAMP')
    if not first_run_timestamp_str:
        print("AVISO: 'FIRST_RUN_TIMESTAMP' não definido. Não será possível criar novos tickets.")
        return

    first_run_date = utils.parse_datetime(first_run_timestamp_str)
    if not first_run_date:
        print(f"AVISO: 'FIRST_RUN_TIMESTAMP' inválido: {first_run_timestamp_str}. Não será possível criar novos tickets.")
        return

    # ==================================================================
    # <<< INÍCIO DA CORREÇÃO >>>
    # ==================================================================
    for fd_ticket_summary in freshdesk_tickets:
        fd_id_str = str(fd_ticket_summary['id'])

        # 1. Pula tickets que já estão mapeados
        if fd_id_str in existing_fd_ids:
            continue
            
        # 2. Obtém e valida a data de criação do ticket
        ticket_creation_date = utils.parse_datetime(fd_ticket_summary['created_at'])
        if not ticket_creation_date:
            print(f"AVISO: Não foi possível determinar a data de criação do ticket Freshdesk {fd_id_str}. Pulando.")
            continue

        # 3. Verifica se o ticket é novo (criado após a data de corte)
        if ticket_creation_date > first_run_date:
            print(f"Ticket Freshdesk {fd_id_str} é novo. Buscando detalhes completos...")
            
            # Busca detalhes completos do ticket no Freshdesk
            full_fd_ticket = freshdesk_service.fetch_freshdesk_ticket_details(fd_id_str, config)
            if not full_fd_ticket:
                print(f"ERRO: Falha ao buscar detalhes do Freshdesk {fd_id_str}.")
                continue

            # Cria o ticket correspondente no Jira
            new_jira_ticket = jira_service.create_jira_ticket(full_fd_ticket, config)
            if new_jira_ticket and 'key' in new_jira_ticket:
                jira_key = new_jira_ticket['key']
                sync_time = datetime.now(timezone.utc).isoformat()
                
                # Cria a entrada inicial no mapeamento
                mapping[jira_key] = {
                    'freshdesk_id': int(fd_id_str),
                    'last_jira_update': sync_time,
                    'last_freshdesk_update': sync_time,
                    'synced_attachments': []
                }
                print(f"Mapeamento criado: Jira {jira_key} <-> Freshdesk {fd_id_str}")

                # Sincroniza anexos iniciais do ticket Freshdesk (com a lógica de vincular IDs)
                if config.get('SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA', True) and full_fd_ticket.get('attachments'):
                    print(f"Sincronizando anexos iniciais do Freshdesk {fd_id_str} para Jira {jira_key}...")
                    temp_dir = get_temp_attachments_dir(config['CLIENT_NAME'])
                    
                    for attachment in full_fd_ticket['attachments']:
                        attachment_id_fd = f"fd-{attachment['id']}"
                        
                        if attachment_id_fd in mapping[jira_key]['synced_attachments']:
                            continue

                        file_path = os.path.join(temp_dir, attachment['name'])
                        if network.download_attachment(attachment['attachment_url'], file_path):
                            jira_attachment_id = jira_service.add_jira_attachment(jira_key, file_path, config)
                            if jira_attachment_id:
                                # Registra ambos os IDs para criar o vínculo
                                attachment_id_jira = f"jira-{jira_attachment_id}"
                                mapping[jira_key]['synced_attachments'].append(attachment_id_fd)
                                mapping[jira_key]['synced_attachments'].append(attachment_id_jira)
                                print(f"  -> Anexo {attachment_id_fd} mapeado para {attachment_id_jira}.")
                            os.remove(file_path)
            else:
                print(f"ERRO: A criação do ticket Jira para o Freshdesk {fd_id_str} falhou.")



def run_sync_for_client(config, mapping_data, mapping_path):
    """
    Executa o ciclo de sincronização completo para um único cliente.

    Args:
        config (dict): A configuração do cliente.
        mapping_data (dict): Os dados de mapeamento atuais.
        mapping_path (str): O caminho para salvar o arquivo de mapeamento.
    """
    sync_days_ago = config.get("SYNC_DAYS_AGO", 1)
    since_date = (datetime.now(timezone.utc) - timedelta(days=sync_days_ago)).strftime('%Y-%m-%d')
    print(f"\nBuscando tickets atualizados desde {since_date}...")

    # 1. Buscar tickets de ambas as plataformas
    jira_tickets = jira_service.fetch_updated_jira_tickets(since_date, config)
    freshdesk_tickets = freshdesk_service.fetch_updated_freshdesk_tickets(since_date, config)

    if jira_tickets is None or freshdesk_tickets is None:
        print("Falha ao buscar tickets de uma das plataformas. Abortando a sincronização para este cliente.")
        return
    
    # 2. Criar novos tickets no Jira a partir de tickets do Freshdesk
    _find_and_map_new_freshdesk_tickets(freshdesk_tickets, mapping_data, config)
    
    # 3. Sincronizar atualizações de tickets já mapeados
    _sync_jira_to_freshdesk(jira_tickets, mapping_data, config)
    _sync_freshdesk_to_jira(freshdesk_tickets, mapping_data, config)
    
    # 4. Salvar o estado do mapeamento
    file_storage.save_mapping_data(mapping_path, mapping_data)

def process_client(client_folder_path, client_name):
    """
    Processa um cliente: carrega configuração, prepara autenticação e inicia a sincronização.

    Args:
        client_folder_path (str): Caminho para a pasta do cliente.
        client_name (str): Nome do cliente.
    """
    print(f"\n{'─'*25} Processando cliente: {client_name.upper()} {'─'*25}")
    config_path = os.path.join(client_folder_path, 'config.json')
    mapping_path = os.path.join(client_folder_path, 'mapping.json')

    # Carrega config e mapping usando o módulo de storage
    config = file_storage.load_client_config(config_path)
    if not config:
        return
        
    mapping_data = file_storage.load_mapping_data(mapping_path)
    
    # Adiciona dados dinâmicos à configuração
    config['CLIENT_NAME'] = client_name
    
    try:
        config['JIRA_AUTH'] = HTTPBasicAuth(config['JIRA_USER_EMAIL'], config['JIRA_API_TOKEN'])
        config['FRESHDESK_AUTH'] = (config['FRESHDESK_API_KEY'], 'X')
    except KeyError as e:
        print(f"ERRO DE CONFIGURAÇÃO: A chave {e} está faltando no config.json de {client_name}. Pulando.")
        return
        
    try:
        run_sync_for_client(config, mapping_data, mapping_path)
        print(f"Cliente {client_name.upper()} processado com sucesso.")
    except Exception as e:
        print(f"ERRO INESPERADO durante a sincronização de {client_name}: {e}")
        import traceback
        traceback.print_exc()