FROM python:3.9-slim-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y jq dos2unix && rm -rf /var/lib/apt/lists/*

COPY . .

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
