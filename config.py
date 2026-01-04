import os
from urllib.parse import urlparse

class SystemConfig:
    # Configuração do banco de dados
    # Usar variável de ambiente DATABASE_URL fornecida pelo Railway/Streamlit
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Chave para o sistema de Login (JWT)
    # Tenta pegar do ambiente, senão usa uma chave segura padrão
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dtf-pricing-secret-key-2024-!@#$%^&*()")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

    SQLALCHEMY_DATABASE_URI = ""

    if DATABASE_URL:
        # Converter URL do formato postgres:// para postgresql:// (necessário para SQLAlchemy)
        if DATABASE_URL.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
        
        # Verificar se precisa adicionar driver psycopg2 explicitamente
        if "postgresql://" in SQLALCHEMY_DATABASE_URI and "psycopg2" not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+psycopg2://")
        
        print(f"🔧 Usando PostgreSQL Remoto")
    else:
        # Fallback para desenvolvimento local (SQLite)
        # O caminho absoluto ajuda a evitar erros de 'arquivo não encontrado'
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        DB_PATH = os.path.join(BASE_DIR, "dtf_pricing.db")
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DB_PATH}"
        print(f"🔧 Usando SQLite local: {SQLALCHEMY_DATABASE_URI}")

# Instância para facilitar importação
config = SystemConfig()
