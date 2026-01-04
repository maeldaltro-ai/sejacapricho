import bcrypt
import jwt
import re
from datetime import datetime, timedelta
import sys
import os

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from config import config
    JWT_SECRET_KEY = config.JWT_SECRET_KEY
    JWT_ALGORITHM = config.JWT_ALGORITHM
except (ImportError, AttributeError):
    # Valores padrão para desenvolvimento
    JWT_SECRET_KEY = "dtf-pricing-secret-key-2024-!@#$%^&*()_+"
    JWT_ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    """Gera um hash seguro para a senha"""
    try:
        # Usar bcrypt para gerar hash
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8')
    except Exception as e:
        print(f"❌ Erro ao gerar hash da senha: {e}")
        # Fallback simples (NÃO usar em produção real)
        import hashlib
        return hashlib.sha256(password.encode('utf-8')).hexdigest()

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    try:
        if not password or not hashed_password:
            return False
        
        # Verificar se o hash é bcrypt
        if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$") or hashed_password.startswith("$2y$"):
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        else:
            # Fallback para hash SHA256 (para compatibilidade com senhas antigas)
            import hashlib
            return hashlib.sha256(password.encode('utf-8')).hexdigest() == hashed_password
    except Exception as e:
        print(f"❌ Erro ao verificar senha: {e}")
        return False

def validate_email(email: str) -> bool:
    """Valida o formato do email"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Valida a força da senha"""
    if len(password) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres"
    
    # Pode adicionar mais regras aqui se necessário
    return True, "Senha válida"

def create_jwt_token(user_id: int, expiration_hours: int = 24) -> str:
    """Cria um token JWT para o usuário"""
    try:
        expiration = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        payload = {
            'user_id': user_id,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        return token
    except Exception as e:
        print(f"❌ Erro ao criar token JWT: {e}")
        return ""

def verify_jwt_token(token: str):
    """Verifica e decodifica um token JWT"""
    try:
        if not token:
            return None
            
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        print("❌ Token JWT expirado")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ Token JWT inválido: {e}")
        return None
    except Exception as e:
        print(f"❌ Erro ao verificar token JWT: {e}")
        return None
