FROM python:3.10-slim-bullseye

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements primeiro (para cache)
COPY requirements.txt .

# Instalar dependências Python
RUN pip install --upgrade pip==23.0.1 && \
    pip install --no-cache-dir -r requirements.txt

# Copiar aplicação
COPY . .

# Criar usuário não-root
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expor porta
EXPOSE 8080

# Comando para rodar
CMD streamlit run app.py --server.port=8080 --server.address=0.0.0.0
