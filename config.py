import os

class SystemConfig:
    # SEMPRE usar SQLite no Streamlit Cloud - REMOVER PostgreSQL completamente
    SQLALCHEMY_DATABASE_URI = "sqlite:///./dtf_pricing.db"
    print("🔧 Usando SQLite (compatível com Streamlit Cloud)")
    
    # Chave para o sistema de Login (JWT)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dtf-pricing-secret-key-2024-!@#$%^&*()_+")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    PASSWORD_HASH_ROUNDS = 12

config = SystemConfig()
