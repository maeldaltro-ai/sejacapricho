from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey
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

# CRIAR A SESSÃO (Correção essencial)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# --- MODELOS ---

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

class SystemConfig(Base):
    __tablename__ = 'system_configs'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text)
    value_type = Column(String(20))
    category = Column(String(50))
    description = Column(String(200))

# Adicione aqui seus outros modelos (Product, Customer, etc) se eles existiam no original.
# Como não tenho acesso a eles, deixei a estrutura pronta para você colar se necessário.
# Exemplo básico para não quebrar referências:
class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    # ... outros campos

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    user_id = Column(Integer, ForeignKey('users.id'))
    # ... outros campos

class Supplier(Base):
    __tablename__ = 'suppliers'
    id = Column(Integer, primary_key=True)
    name = Column(String(100))

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)

class Budget(Base):
    __tablename__ = 'budgets'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.now)


# --- INICIALIZAÇÃO ---

def init_db():
    """Inicializa o banco de dados e cria tabelas"""
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
                    key=key, value=value, value_type=value_type, 
                    category=category, description=description
                )
                db.add(config_item)
        
        # Criar admin se não existir
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
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
                print("👤 Usuário admin criado")
            except ImportError:
                pass
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"❌ Erro DB: {e}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
