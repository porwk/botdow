FROM python:3.9

WORKDIR /app

# Copiar primeiro os requisitos para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copiar todo o código do projeto
COPY . .

# Se necessário, dar permissões para a pasta lib
RUN chmod -R 755 /app/lib

CMD ["python", "botdown.py"]
