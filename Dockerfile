FROM python:3.9-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar arquivos necessários
COPY requirements.txt .
COPY botdown.py .
COPY stats.json .
COPY error_log.txt .

# Criar diretório de cache
RUN mkdir cache

# Instalar dependências Python
RUN pip install --no-cache-dir -r requirements.txt

# Definir variáveis de ambiente
ENV TELEGRAM_BOT_TOKEN=""

CMD ["python", "botdown.py"]
