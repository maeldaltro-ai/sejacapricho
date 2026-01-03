import os
import sys

class SystemConfig:
    # DETECTAR AMBIENTE
    is_streamlit_cloud = "streamlit" in sys.modules and hasattr(sys, 'base_prefix')
    
    if is_streamlit_cloud:
        print("🚀 Ambiente Streamlit Cloud detectado")
        # SEMPRE usar SQLite no Streamlit Cloud
        SQLALCHEMY_DATABASE_URI = "sqlite:///./dtf_pricing.db"
    elif os.getenv("DATABASE_URL") and os.getenv("DATABASE_URL").startswith("postgres"):
        # Usar PostgreSQL apenas se DATABASE_URL estiver configurado
        db_url = os.getenv("DATABASE_URL")
        if db_url.startswith("postgres://"):
            SQLALCHEMY_DATABASE_URI = db_url.replace("postgres://", "postgresql://", 1)
        else:
            SQLALCHEMY_DATABASE_URI = db_url
        print("🔗 Conectando ao PostgreSQL")
    else:
        # Fallback para SQLite
        SQLALCHEMY_DATABASE_URI = "sqlite:///./dtf_pricing.db"
        print("🔧 Usando SQLite (fallback)")
    
    # Chave para o sistema de Login (JWT)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dtf-pricing-secret-key-2024")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    PASSWORD_HASH_ROUNDS = 12

config = SystemConfig()
