from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime
import sys
import os

# Adicionar o diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import config

# Configurar engine do banco de dados
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

# CRIAR A SESSÃO (Faltava isso no seu código original)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos (strings para evitar dependência circular se houver outras classes)
    # customers = relationship("Customer", backref="user_ref") # Descomente se tiver a classe Customer

class SystemConfig(Base):
    __tablename__ = 'system_configs'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text)
    value_type = Column(String(20))
    category = Column(String(50))
    description = Column(String(200))

# --- Funções de Inicialização ---

def init_db():
    """Inicializa o banco de dados e cria tabelas se não existirem"""
    try:
        Base.metadata.create_all(bind=engine)
        
        db = SessionLocal()
        
        # Configurações padrão
        default_configs = [
            ('price_per_meter', '100.00', 'number', 'pricing', 'Preço por metro linear'),
            ('default_production_days', '5', 'number', 'general', 'Dias padrão para produção')
        ]
        
        for key, value, value_type, category, description in default_configs:
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                config_item = SystemConfig(
                    key=key,
                    value=value,
                    value_type=value_type,
                    category=category,
                    description=description
                )
                db.add(config_item)
        
        # Verificar se existe usuário admin
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            # Import aqui para evitar ciclo
            try:
                from security import hash_password
                admin_user = User(
                    username='admin',
                    email='admin@sejacapricho.com.br',
                    password_hash=hash_password('admin123'),
                    full_name='Administrador',
                    is_admin=True
                )
                db.add(admin_user)
                print("👤 Usuário admin criado (senha: admin123)")
            except ImportError:
                print("⚠️ Não foi possível criar admin: security module not found")
        
        db.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inicializar dados: {e}")
    finally:
        db.close()

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
