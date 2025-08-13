# sync_app/core/utils.py
import re
import html
from datetime import datetime, timezone
from dateutil import parser

def html_to_text(html_string):
    """
    Converte uma string HTML em texto plano.

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
    if not datetime_str:
        return None
    try:
        # Use dateutil.parser para analisar a string de data
        dt_object = parser.parse(datetime_str)
        # Garante que o datetime está no fuso horário UTC
        return dt_object.astimezone(timezone.utc)
    except (ValueError, TypeError):
        print(f"AVISO: Não foi possível converter a data '{datetime_str}'")
        return None