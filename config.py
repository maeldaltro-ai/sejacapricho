import os

class SystemConfig:
    # O Railway fornece a URL como postgres://, mas o SQLAlchemy exige postgresql://
    _database_url = os.getenv("DATABASE_URL")
    if _database_url and _database_url.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = _database_url.replace("postgres://", "postgresql://", 1)
    else:
        # Fallback para teste local se não houver banco configurado
        SQLALCHEMY_DATABASE_URI = _database_url or "sqlite:///./local_test.db"

    # Chave para o sistema de Login (JWT)
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "uma-chave-muito-secreta-e-longa-123")
    JWT_ALGORITHM = "HS256"
    PASSWORD_HASH_ROUNDS = 12

config = SystemConfig()
