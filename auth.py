import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session
from models import User, SessionLocal
from utils.security import verify_password, hash_password
from config import config

class AuthSystem:
    def __init__(self):
        self.session = SessionLocal()
    
    def register_user(self, username: str, email: str, password: str, full_name: str = None) -> tuple[bool, str]:
        """Registra um novo usuário"""
        try:
            # Verificar se o usuário já existe
            existing_user = self.session.query(User).filter(
                (User.username == username) | (User.email == email)
            ).first()
            
            if existing_user:
                return False, "Usuário ou email já cadastrado"
            
            # Criar novo usuário
            new_user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                full_name=full_name,
                is_active=True
            )
            
            self.session.add(new_user)
            self.session.commit()
            return True, "Usuário registrado com sucesso"
            
        except Exception as e:
            self.session.rollback()
            return False, f"Erro ao registrar usuário: {str(e)}"
    
    def login_user(self, username: str, password: str) -> tuple[bool, Optional[User], str]:
        """Autentica um usuário"""
        try:
            user = self.session.query(User).filter(
                (User.username == username) | (User.email == username),
                User.is_active == True
            ).first()
            
            if not user:
                return False, None, "Usuário não encontrado"
            
            if not verify_password(password, user.password_hash):
                return False, None, "Senha incorreta"
            
            # Gerar token JWT
            token = self.create_jwt_token(user.id)
            
            return True, user, token
            
        except Exception as e:
            return False, None, f"Erro ao fazer login: {str(e)}"
    
    def create_jwt_token(self, user_id: int) -> str:
        """Cria um token JWT para o usuário"""
        expiration = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        
        payload = {
            'user_id': user_id,
            'exp': expiration,
            'iat': datetime.utcnow()
        }
        
        token = jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
        return token
    
    def verify_jwt_token(self, token: str) -> Optional[int]:
        """Verifica um token JWT e retorna o user_id"""
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            return payload.get('user_id')
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self, token: str) -> Optional[User]:
        """Retorna o usuário atual baseado no token"""
        user_id = self.verify_jwt_token(token)
        if not user_id:
            return None
        
        return self.session.query(User).filter(User.id == user_id, User.is_active == True).first()
    
    def update_user_password(self, user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
        """Atualiza a senha do usuário"""
        try:
            user = self.session.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "Usuário não encontrado"
            
            if not verify_password(current_password, user.password_hash):
                return False, "Senha atual incorreta"
            
            user.password_hash = hash_password(new_password)
            self.session.commit()
            return True, "Senha atualizada com sucesso"
            
        except Exception as e:
            self.session.rollback()
            return False, f"Erro ao atualizar senha: {str(e)}"
    
    def logout_user(self):
        """Limpa a sessão do usuário"""
        if 'auth_token' in st.session_state:
            del st.session_state.auth_token
        if 'current_user' in st.session_state:
            del st.session_state.current_user
    
    def __del__(self):
        self.session.close()

# Instância global do sistema de autenticação
auth_system = AuthSystem()

def show_login_register_page():
    """Mostra a página de login/registro"""
    st.title("🔐 DTF Pricing Calculator - Login")
    
    tab1, tab2 = st.tabs(["Login", "Registro"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Usuário ou Email")
            password = st.text_input("Senha", type="password")
            submit = st.form_submit_button("Entrar")
            
            if submit:
                if username and password:
                    success, user, token = auth_system.login_user(username, password)
                    if success:
                        st.session_state.auth_token = token
                        st.session_state.current_user = user.to_dict()
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Falha no login: {user if user else token}")
                else:
                    st.warning("Preencha todos os campos")
    
    with tab2:
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Nome de usuário")
                email = st.text_input("Email")
            with col2:
                full_name = st.text_input("Nome completo")
                password = st.text_input("Senha", type="password")
                confirm_password = st.text_input("Confirmar Senha", type="password")
            
            submit = st.form_submit_button("Registrar")
            
            if submit:
                if not all([username, email, password, confirm_password]):
                    st.warning("Preencha todos os campos obrigatórios")
                elif password != confirm_password:
                    st.error("As senhas não coincidem")
                elif len(password) < 6:
                    st.error("A senha deve ter pelo menos 6 caracteres")
                else:
                    success, message = auth_system.register_user(username, email, password, full_name)
                    if success:
                        st.success(message)
                        # Auto-login após registro
                        success, user, token = auth_system.login_user(username, password)
                        if success:
                            st.session_state.auth_token = token
                            st.session_state.current_user = user.to_dict()
                            st.rerun()
                    else:
                        st.error(message)

def require_auth():
    """Decorador para requerer autenticação"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'auth_token' not in st.session_state or 'current_user' not in st.session_state:
                show_login_register_page()
                return
            
            # Verificar se o token ainda é válido
            user_id = auth_system.verify_jwt_token(st.session_state.auth_token)
            if not user_id:
                st.warning("Sessão expirada. Por favor, faça login novamente.")
                auth_system.logout_user()
                st.rerun()
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user():
    """Retorna o usuário atual"""
    return st.session_state.get('current_user')

def is_admin():
    """Verifica se o usuário atual é admin"""
    user = get_current_user()
    return user and user.get('is_admin', False)