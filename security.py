import bcrypt
import re
from datetime import datetime, timedelta
from typing import Optional
import jwt
from config import config

def hash_password(password: str) -> str:
    """Gera hash da senha usando bcrypt"""
    salt = bcrypt.gensalt(rounds=config.PASSWORD_HASH_ROUNDS)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verifica se a senha corresponde ao hash"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

def validate_email(email: str) -> bool:
    """Valida formato de email"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password_strength(password: str) -> tuple[bool, str]:
    """Valida força da senha"""
    if len(password) < 6:
        return False, "A senha deve ter pelo menos 6 caracteres"
    
    # Pode adicionar mais validações aqui
    return True, "Senha válida"

def generate_reset_token(email: str, expires_in: int = 3600) -> str:
    """Gera token para reset de senha"""
    expiration = datetime.utcnow() + timedelta(seconds=expires_in)
    
    payload = {
        'email': email,
        'exp': expiration,
        'iat': datetime.utcnow(),
        'type': 'password_reset'
    }
    
    token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    return token

def verify_reset_token(token: str) -> Optional[str]:
    """Verifica token de reset de senha"""
    try:
        payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        if payload.get('type') != 'password_reset':
            return None
        return payload.get('email')
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def sanitize_input(text: str) -> str:
    """Remove caracteres perigosos de inputs"""
    if not text:
        return text
    
    # Remove tags HTML/JavaScript
    import html
    text = html.escape(text)
    
    # Remove caracteres de controle
    text = ''.join(char for char in text if ord(char) >= 32)
    
    return text.strip()