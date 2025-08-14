#!/bin/bash
set -e
 

# Função para imprimir mensagens com timestamp
log() {
 echo "$(date '+%Y-%m-%d %H:%M:%S') - $*"
}
 

log "Iniciando o script de entrada..."
log "PID do processo: $"
log "Variáveis de ambiente:"
env | sort
 

CLIENTS_ROOT_FOLDER="/app/clients"
 

# Processa todos os clientes
find "$CLIENTS_ROOT_FOLDER" -maxdepth 1 -type d -not -path "$CLIENTS_ROOT_FOLDER" -print0 |
while IFS= read -r -d '' client_folder; do
 client_name=$(basename "$client_folder")
 log "Processando cliente: $client_name"
 

 config_file="$client_folder/config.json"
 

 if [ -f "$config_file" ]; then
 log "Arquivo de configuração encontrado: $config_file"
 

 # Carrega as variáveis
 export JIRA_URL=$(jq -r .JIRA_URL "$config_file")
 export JIRA_USER_EMAIL=$(jq -r .JIRA_USER_EMAIL "$config_file")
 export JIRA_API_TOKEN=$(jq -r .JIRA_API_TOKEN "$config_file")
 export JIRA_PROJECT_KEY=$(jq -r .JIRA_PROJECT_KEY "$config_file")
 export FRESHDESK_DOMAIN=$(jq -r .FRESHDESK_DOMAIN "$config_file")
 export FRESHDESK_API_KEY=$(jq -r .FRESHDESK_API_KEY "$config_file")
 export SYNC_STATUS_JIRA_TO_FRESHDESK=$(jq -r .SYNC_STATUS_JIRA_TO_FRESHDESK "$config_file")
 export SYNC_COMMENTS_JIRA_TO_FRESHDESK=$(jq -r .SYNC_COMMENTS_JIRA_TO_FRESHDESK "$config_file")
 export SYNC_COMMENTS_FRESHDESK_TO_JIRA=$(jq -r .SYNC_COMMENTS_FRESHDESK_TO_JIRA "$config_file")
 export SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK=$(jq -r .SYNC_ATTACHMENTS_JIRA_TO_FRESHDESK "$config_file")
 export SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA=$(jq -r .SYNC_ATTACHMENTS_FRESHDESK_TO_JIRA "$config_file")
 export FRESHDESK_COMPANY_ID=$(jq -r .FRESHDESK_COMPANY_ID "$config_file")
 

 # Executa o Python para esse cliente
 python -c "from sync_app.services.sync_service import process_client; process_client('$client_folder', '$client_name')"
 else
 log "Arquivo de configuração não encontrado para $client_name"
 fi
 done
 

 log "Script de entrada concluído."