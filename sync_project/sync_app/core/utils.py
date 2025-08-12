# sync_app/core/utils.py
import re
import html
from datetime import datetime, timezone

def html_to_text(html_string):
    """
    Converte uma string HTML em texto plano.

    Args:
        html_string (str): A string contendo HTML.

    Returns:
        str: O texto extraído e limpo.
    """
    if not html_string:
        return ""
    # Remove tags HTML
    text = re.sub('<[^<]+?>', ' ', html_string)
    # Decodifica entidades HTML (como &amp;)
    text = html.unescape(text)
    # Remove espaços em branco múltiplos
    return re.sub(r'\s+', ' ', text).strip()

def parse_datetime(datetime_str):
    """
    Converte uma string de data/hora em formato ISO para um objeto datetime ciente do fuso horário (UTC).

    Args:
        datetime_str (str): A string de data e hora (e.g., '2025-08-12T10:00:00Z').

    Returns:
        datetime or None: O objeto datetime convertido para UTC, ou None se a conversão falhar.
    """
    if not datetime_str:
        return None
    # Normaliza a string, garantindo que o 'Z' seja tratado como fuso +00:00
    normalized_str = str(datetime_str).replace('Z', '+00:00')
    try:
        # Converte a string para datetime e garante que está no fuso horário UTC
        return datetime.fromisoformat(normalized_str).astimezone(timezone.utc)
    except (ValueError, TypeError):
        print(f"AVISO: Não foi possível converter a data '{datetime_str}'")
        return None