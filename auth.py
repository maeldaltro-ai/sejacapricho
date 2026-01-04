import streamlit as st
from datetime import datetime, timedelta
from typing import Optional
import jwt
from sqlalchemy.orm import Session
from sqlalchemy import or_
from models import User, SessionLocal
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from security import verify_password, hash_password, validate_email
    from config import config
    JWT_SECRET_KEY = config.JWT_SECRET_KEY
    JWT_ALGORITHM = config.JWT_ALGORITHM
    JWT_EXPIRATION_HOURS = config.JWT_EXPIRATION_HOURS
except (ImportError, AttributeError) as e:
    # Valores padrão para desenvolvimento
    print(f"⚠️ Erro ao importar configurações: {e}")
    JWT_SECRET_KEY = "dev_secret_key_change_in_production"
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24

class AuthSystem:
    def __init__(self):
        # Não instanciar sessão aqui para evitar problemas de thread
        pass
    
    def get_session(self):
        return SessionLocal()
    
    def register_user(self, username: str, email: str, password: str, full_name: str = None) -> tuple[bool, str]:
        """Registra um novo usuário"""
        session = self.get_session()
        try:
            # Normalizar dados
            username = username.strip().lower()
            email = email.strip().lower()
            
            if not validate_email(email):
                return False, "Email inválido"
            
            # Verificar se o usuário já existe
            existing_user = session.query(User).filter(
                or_(
                    User.username.ilike(username),
                    User.email.ilike(email)
                )
            ).first()
            
            if existing_user:
                if existing_user.username.lower() == username.lower():
                    return False, "Nome de usuário já cadastrado"
                else:
                    return False, "Email já cadastrado"
            
            # Validar senha
            if len(password) < 6:
                return False, "A senha deve ter pelo menos 6 caracteres"
            
            # Criar novo usuário
            new_user = User(
                username=username,
                email=email,
                password_hash=hash_password(password),
                full_name=full_name.strip() if full_name else None,
                is_active=True,
                is_admin=False
            )
            
            session.add(new_user)
            session.commit()
            return True, "Usuário registrado com sucesso!"
            
        except Exception as e:
            session.rollback()
            print(f"❌ Erro ao registrar usuário: {e}")
            return False, f"Erro ao registrar usuário: {str(e)}"
        finally:
            session.close()
    
    def login_user(self, username: str, password: str) -> tuple[bool, Optional[User], str]:
        """Autentica um usuário"""
        session = self.get_session()
        try:
            username_input = username.strip().lower()
            
            user = session.query(User).filter(
                or_(
                    User.username.ilike(username_input),
                    User.email.ilike(username_input)
                ),
                User.is_active == True
            ).first()
            
            if not user:
                return False, None, "Usuário não encontrado"
            
            if not verify_password(password, user.password_hash):
                return False, None, "Senha incorreta"
            
            token = self.create_jwt_token(user.id)
            return True, user, token
            
        except Exception as e:
            print(f"❌ Erro ao fazer login: {e}")
            return False, None, f"Erro ao fazer login: {str(e)}"
        finally:
            session.close()
    
    def create_jwt_token(self, user_id: int) -> str:
        try:
            expiration = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
            payload = {
                'user_id': user_id,
                'exp': expiration,
                'iat': datetime.utcnow()
            }
            return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
        except Exception as e:
            print(f"❌ Erro ao criar token JWT: {e}")
            return ""
    
    def verify_jwt_token(self, token: str) -> Optional[int]:
        try:
            if not token:
                return None
            payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
            return payload.get('user_id')
        except Exception:
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        session = self.get_session()
        try:
            return session.query(User).filter(User.id == user_id, User.is_active == True).first()
        finally:
            session.close()
    
    def update_user_password(self, user_id: int, current_password: str, new_password: str) -> tuple[bool, str]:
        session = self.get_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                return False, "Usuário não encontrado"
            
            if not verify_password(current_password, user.password_hash):
                return False, "Senha atual incorreta"
            
            if len(new_password) < 6:
                return False, "A nova senha deve ter pelo menos 6 caracteres"
            
            user.password_hash = hash_password(new_password)
            session.commit()
            return True, "Senha atualizada com sucesso!"
            
        except Exception as e:
            session.rollback()
            return False, f"Erro ao atualizar senha: {str(e)}"
        finally:
            session.close()
    
    def logout_user(self):
        keys_to_remove = ['auth_token', 'current_user', 'current_page', 'selected_products', 'manual_items']
        for key in keys_to_remove:
            if key in st.session_state:
                del st.session_state[key]

auth_system = AuthSystem()

def show_login_register_page():
    st.title("🔐 DTF Pricing Calculator - Login")
    
    if 'auth_token' in st.session_state and 'current_user' in st.session_state:
        st.success("Você já está logado!")
        if st.button("Ir para o Dashboard"):
            st.session_state.current_page = "calculator"
            st.rerun()
        return
    
    tab1, tab2 = st.tabs(["Login", "Registro"])
    
    with tab1:
        st.subheader("Login")
        with st.form("login_form"):
            username = st.text_input("Usuário ou Email")
            password = st.text_input("Senha", type="password")
            submit_login = st.form_submit_button("Entrar")
        
        if submit_login:
            if not username or not password:
                st.error("Preencha todos os campos")
            else:
                with st.spinner("Autenticando..."):
                    success, user, token = auth_system.login_user(username, password)
                    if success and user:
                        st.session_state.auth_token = token
                        st.session_state.current_user = user.to_dict()
                        st.session_state.current_page = "calculator"
                        st.success("Login realizado com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Falha no login: {token}")
    
    with tab2:
        st.subheader("Registro")
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Nome de usuário")
                new_email = st.text_input("Email")
            with col2:
                new_full_name = st.text_input("Nome completo")
                new_password = st.text_input("Senha", type="password")
                confirm_password = st.text_input("Confirmar Senha", type="password")
            
            submit_register = st.form_submit_button("Registrar")
        
        if submit_register:
            if not all([new_username, new_email, new_password, confirm_password]):
                st.error("Preencha todos os campos obrigatórios")
            elif new_password != confirm_password:
                st.error("As senhas não coincidem")
            elif len(new_password) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres")
            else:
                with st.spinner("Registrando..."):
                    success, message = auth_system.register_user(new_username, new_email, new_password, new_full_name)
                    if success:
                        st.success(message)
                        success, user, token = auth_system.login_user(new_username, new_password)
                        if success and user:
                            st.session_state.auth_token = token
                            st.session_state.current_user = user.to_dict()
                            st.session_state.current_page = "calculator"
                            st.rerun()
                    else:
                        st.error(message)

def require_auth():
    def decorator(func):
        def wrapper(*args, **kwargs):
            if 'auth_token' not in st.session_state or 'current_user' not in st.session_state:
                show_login_register_page()
                st.stop()
                return
            
            user_id = auth_system.verify_jwt_token(st.session_state.auth_token)
            if not user_id:
                st.warning("Sessão expirada. Por favor, faça login novamente.")
                auth_system.logout_user()
                st.rerun()
            
            # Opcional: Recarregar usuário do banco para garantir dados frescos
            # Mas para performance, podemos confiar na session_state por enquanto
            return func(*args, **kwargs)
        return wrapper
    return decorator

def get_current_user():
    return st.session_state.get('current_user', {})

def is_admin():
    user = get_current_user()
    return user.get('is_admin', False)
