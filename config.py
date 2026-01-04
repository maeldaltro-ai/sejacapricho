import os
from urllib.parse import urlparse

class SystemConfig:
    # Configuração do banco de dados
    # Usar variável de ambiente DATABASE_URL fornecida pelo Railway
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    if DATABASE_URL:
        # Converter URL do formato postgres:// para postgresql://
        if DATABASE_URL.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = DATABASE_URL
        
        # Verificar se precisa adicionar driver psycopg2
        if "postgresql://" in SQLALCHEMY_DATABASE_URI and "psycopg2" not in SQLALCHEMY_DATABASE_URI:
            SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgresql://", "postgresql+psycopg2://")
        
        print(f"🔧 Usando PostgreSQL do Railway")
    else:
        # Fallback para desenvolvimento local
        SQLALCHEMY_DATABASE_URI = "sqlite:///./dtf_pricing.db"
        print(f"🔧 Usando SQLite local (nenhum DATABASE_URL encontrado)")
    
    # DEBUG: Mostrar URL final (ocultando credenciais)
    if SQLALCHEMY_DATABASE_URI:
        parsed = urlparse(SQLALCHEMY_DATABASE_URI)
        safe_url = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}{parsed.path}"
        print(f"🔧 Conectando ao banco: {safe_url}")
    
    # Chave para o sistema de Login (JWT)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dtf-pricing-secret-key-2024-!@#$%^&*()_+")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    PASSWORD_HASH_ROUNDS = 12

config = SystemConfig()
