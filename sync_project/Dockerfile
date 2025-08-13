# Usa uma imagem base do Python (versão 3.9 ou superior)
FROM python:3.9-slim-buster

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia os arquivos de dependência (requirements.txt)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o resto do código fonte
COPY . .

# Define a variável de ambiente PYTHONUNBUFFERED para imprimir os logs em tempo real
ENV PYTHONUNBUFFERED=1

# Comando para executar o serviço
CMD ["python", "main.py"]