import os

class SystemConfig:
    # Configuração do banco de dados
    # Primeiro, tenta usar a DATABASE_URL do Railway (ambiente de produção)
    _database_url = os.getenv("DATABASE_URL")
    
    if _database_url:
        # O Railway fornece a URL como postgres://, mas o SQLAlchemy exige postgresql://
        if _database_url.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = _database_url.replace("postgres://", "postgresql://", 1)
            print(f"🔧 URL convertida (postgres -> postgresql)")
        else:
            SQLALCHEMY_DATABASE_URI = _database_url
            print(f"🔧 URL já está em formato postgresql")
    else:
        # Fallback para desenvolvimento local
        SQLALCHEMY_DATABASE_URI = "sqlite:///./dtf_pricing.db"
        print(f"🔧 Usando SQLite local (nenhum DATABASE_URL encontrado)")
    
    # DEBUG: Mostrar URL final
    print(f"🔧 SQLALCHEMY_DATABASE_URI final: {SQLALCHEMY_DATABASE_URI[:50]}...")
    
    # Chave para o sistema de Login (JWT)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dtf-pricing-secret-key-2024-!@#$%^&*()_+")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    PASSWORD_HASH_ROUNDS = 12

config = SystemConfig()

# Para debug: mostrar qual banco está sendo usado (apenas em desenvolvimento)
if os.getenv("ENVIRONMENT") != "production":
    print(f"🔧 Configuração do banco: {config.SQLALCHEMY_DATABASE_URI[:50]}...")
