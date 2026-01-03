import os
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class Config:
    # Configurações do aplicativo
    APP_NAME = "DTF Pricing Calculator"
    APP_VERSION = "2.0.0"
    SECRET_KEY = os.getenv("SECRET_KEY", "sua-chave-secreta-aqui-para-desenvolvimento")
    
    # Configurações do banco de dados
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")  # postgresql, sqlite, mysql
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "dtf_pricing")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    # Configurações de autenticação
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # Configurações de segurança
    PASSWORD_HASH_ROUNDS = 12
    SESSION_TIMEOUT_MINUTES = 60
    
    # Configurações do sistema
    DEFAULT_MARGIN = 50.0
    DEFAULT_PRODUCTION_DAYS = 5
    CURRENCY = "BRL"
    TIMEZONE = "America/Sao_Paulo"
    
    @property
    def DATABASE_URL(self):
        if self.DB_TYPE == "postgresql":
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == "sqlite":
            return "sqlite:///dtf_pricing.db"
        else:
            raise ValueError(f"Tipo de banco de dados não suportado: {self.DB_TYPE}")

config = Config()