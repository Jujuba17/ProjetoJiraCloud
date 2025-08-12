# sync_app/core/network.py
import requests
import os

def api_request(method, url, auth, json_data=None, params=None, data=None, files=None):
    """
    Realiza uma requisição de API genérica e centralizada.

    Args:
        method (str): O método HTTP (e.g., 'GET', 'POST').
        url (str): A URL do endpoint da API.
        auth (tuple or AuthBase): Objeto de autenticação (e.g., HTTPBasicAuth).
        json_data (dict, optional): Payload JSON para a requisição.
        params (dict, optional): Parâmetros de URL.
        data (dict, optional): Dados de formulário.
        files (dict, optional): Arquivos para upload.

    Returns:
        dict or list or bool or None: A resposta JSON da API, True para sucesso
                                      sem conteúdo, ou None em caso de erro.
    """
    headers = {}
    # Se não estivermos enviando arquivos, o Content-Type é application/json
    if not files:
        headers['Content-Type'] = 'application/json'
    headers['Accept'] = 'application/json'

    try:
        response = requests.request(
            method,
            url,
            json=json_data,
            params=params,
            data=data,
            files=files,
            auth=auth,
            headers=headers
        )
        response.raise_for_status()  # Lança uma exceção para status de erro (4xx ou 5xx)

        # Respostas 201 (Created) sem conteúdo são comuns, tratamos como sucesso
        if response.status_code == 201 and not response.content:
            return True
            
        # Retorna o JSON se houver conteúdo, caso contrário, None
        return response.json() if response.content else None

    except requests.exceptions.RequestException as e:
        print(f"Erro na API para {method} {url}: {e}")
        if e.response is not None:
            print(f"Status: {e.response.status_code}, Detalhes: {e.response.text}")
        return None

def download_attachment(url, file_path, auth=None):
    """
    Baixa um arquivo de uma URL e o salva localmente.

    Args:
        url (str): A URL do anexo a ser baixado.
        file_path (str): O caminho completo onde o arquivo será salvo.
        auth (tuple or AuthBase, optional): Objeto de autenticação, se necessário.

    Returns:
        bool: True se o download for bem-sucedido e o arquivo não estiver vazio,
              False caso contrário.
    """
    try:
        # Usamos stream=True para lidar com arquivos grandes de forma eficiente
        response = requests.get(url, auth=auth, stream=True)
        response.raise_for_status()
        
        with open(file_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Confirma que o arquivo foi realmente criado e tem conteúdo
        return os.path.getsize(file_path) > 0
        
    except requests.exceptions.RequestException as e:
        print(f"ERRO: Falha ao baixar anexo de {url}. Detalhes: {e}")
        return False