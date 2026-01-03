from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import json

from config import config

# Configurar engine do banco de dados
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    echo=False,  # Setar True para ver queries SQL no console (apenas dev)
    pool_pre_ping=True,  # Verificar conexão antes de usar
    pool_recycle=3600,  # Reciclar conexões a cada hora
)

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
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    cost = Column(Float, default=0.00)
    energy_cost = Column(Float, default=0.00)
    transport_cost = Column(Float, default=0.00)
    packaging_cost = Column(Float, default=0.00)
    uses_dtf = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.name,
            'custo': self.cost,
            'energia': self.energy_cost,
            'transp': self.transport_cost,
            'emb': self.packaging_cost,
            'usa_dtf': self.uses_dtf,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    document_type = Column(String(10))
    document = Column(String(20))
    address = Column(Text)
    zip_code = Column(String(10))
    city = Column(String(50))
    state = Column(String(2))
    phone = Column(String(20))
    email = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'document_type': self.document_type,
            'document': self.document,
            'address': self.address,
            'zip_code': self.zip_code,
            'city': self.city,
            'state': self.state,
            'phone': self.phone,
            'email': self.email,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    trade_name = Column(String(100))
    supplier_type = Column(String(50))
    document_type = Column(String(10))
    document = Column(String(20))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'trade_name': self.trade_name,
            'supplier_type': self.supplier_type,
            'document_type': self.document_type,
            'document': self.document,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True)
    customer_id = Column(Integer)
    user_id = Column(Integer)
    total_amount = Column(Float, default=0.00)
    items = Column(JSON)
    delivery_type = Column(String(50))
    delivery_deadline = Column(String(50))
    payment_method = Column(String(50))
    payment_status = Column(String(20), default='pending')
    delivery_status = Column(String(20), default='production')
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    paid_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'items': self.items,
            'delivery_type': self.delivery_type,
            'delivery_deadline': self.delivery_deadline,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'delivery_status': self.delivery_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    budget_number = Column(String(20), unique=True)
    client_name = Column(String(100))
    address = Column(Text)
    delivery_type = Column(String(50))
    sale_type = Column(String(50))
    production_deadline = Column(String(50))
    total_amount = Column(Float, default=0.00)
    items = Column(JSON)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    user_id = Column(Integer)
    
    def to_dict(self):
        return {
            'id': self.id,
            'budget_number': self.budget_number,
            'client_name': self.client_name,
            'address': self.address,
            'delivery_type': self.delivery_type,
            'sale_type': self.sale_type,
            'production_deadline': self.production_deadline,
            'total_amount': self.total_amount,
            'items': self.items,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_id': self.user_id
        }

class SystemConfig(Base):
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20))
    category = Column(String(50))
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def get_value(self):
        if self.value_type == 'number':
            try:
                return float(self.value)
            except:
                return 0.0
        elif self.value_type == 'boolean':
            return self.value.lower() in ['true', '1', 'yes']
        else:
            return self.value
    
    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.get_value(),
            'value_type': self.value_type,
            'category': self.category,
            'description': self.description,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

# Criar sessão do banco de dados
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializa o banco de dados, criando todas as tabelas se não existirem"""
    Base.metadata.create_all(bind=engine)
    
    # Inserir configurações padrão se não existirem
    db = SessionLocal()
    try:
        # Configurações padrão do sistema
        default_configs = [
            ('dtf_price_per_meter', '80.0', 'number', 'dtf', 'Preço do DTF por metro linear'),
            ('roll_width', '58.0', 'number', 'dtf', 'Largura do rolo DTF em cm'),
            ('roll_height', '100', 'number', 'dtf', 'Altura do rolo DTF em cm'),
            ('energy_cost_label', 'Energia (R$)', 'string', 'labels', 'Rótulo para custo de energia'),
            ('transport_cost_label', 'Transporte (R$)', 'string', 'labels', 'Rótulo para custo de transporte'),
            ('packaging_cost_label', 'Embalagem (R$)', 'string', 'labels', 'Rótulo para custo de embalagem'),
            ('energy_cost_value', '1.0', 'number', 'fixed_costs', 'Valor do custo de energia'),
            ('transport_cost_value', '2.0', 'number', 'fixed_costs', 'Valor do custo de transporte'),
            ('packaging_cost_value', '1.0', 'number', 'fixed_costs', 'Valor do custo de embalagem'),
            ('default_margin', '50.0', 'number', 'pricing', 'Margem de lucro padrão em %'),
            ('default_production_days', '5', 'number', 'general', 'Dias padrão para produção')
        ]
        
        for key, value, value_type, category, description in default_configs:
            existing = db.query(SystemConfig).filter(SystemConfig.key == key).first()
            if not existing:
                config = SystemConfig(
                    key=key,
                    value=value,
                    value_type=value_type,
                    category=category,
                    description=description
                )
                db.add(config)
        
        # Verificar se existe usuário admin
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            # Importar função de hash para criar admin
            from security import hash_password
            admin_user = User(
                username='admin',
                email='admin@sejacapricho.com.br',
                password_hash=hash_password('admin123'),
                full_name='Administrador',
                is_admin=True
            )
            db.add(admin_user)
        
        db.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao inicializar banco: {e}")
    finally:
        db.close()

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
