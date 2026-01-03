import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configurações do aplicativo
    APP_NAME = "DTF Pricing Calculator"
    APP_VERSION = "2.0.0"
    APP_ENV = os.getenv("APP_ENV", "development")
    
    # Configurações de segurança
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # Configurações de segurança
    PASSWORD_HASH_ROUNDS = 12
    SESSION_TIMEOUT_MINUTES = 60
    
    # Configurações do banco de dados - Railway usa DATABASE_URL
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Fallback para desenvolvimento local
    DB_TYPE = os.getenv("DB_TYPE", "postgresql")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")
    DB_NAME = os.getenv("DB_NAME", "dtf_pricing")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "")
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Prioridade: DATABASE_URL do Railway
        if self.DATABASE_URL:
            # Railway fornece DATABASE_URL no formato postgresql://
            # Algumas versões usam postgres://, então convertemos se necessário
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql://", 1)
            return self.DATABASE_URL
        
        # Fallback para desenvolvimento
        if self.DB_TYPE == "postgresql":
            return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        elif self.DB_TYPE == "sqlite":
            return "sqlite:///dtf_pricing.db"
        else:
            raise ValueError(f"Tipo de banco de dados não suportado: {self.DB_TYPE}")
    
    # Configurações do sistema
    DEFAULT_MARGIN = 50.0
    DEFAULT_PRODUCTION_DAYS = 5
    CURRENCY = "BRL"
    TIMEZONE = "America/Sao_Paulo"
    
    # Configurações do Streamlit para produção
    STREAMLIT_SERVER_PORT = int(os.getenv("PORT", 8501))
    STREAMLIT_SERVER_ADDRESS = "0.0.0.0"
    
    @property
    def IS_PRODUCTION(self):
        return self.APP_ENV.lower() == "production"
    
    @property
    def IS_DEVELOPMENT(self):
        return self.APP_ENV.lower() == "development"

config = Config()
