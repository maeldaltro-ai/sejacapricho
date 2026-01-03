from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import json
import os

# Obter DATABASE_URL do ambiente ou usar padrão SQLite
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Tentar importar do config, se existir
    try:
        from config import config
        DATABASE_URL = config.DATABASE_URL
    except (ImportError, AttributeError):
        # Fallback para SQLite
        DATABASE_URL = "sqlite:///./app.db"

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
    
    # Relacionamentos
    orders = relationship("Order", back_populates="user")
    budgets = relationship("Budget", back_populates="user")
    
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
    cost = Column(Float, default=0.0)
    energy_cost = Column(Float, default=0.0)
    transport_cost = Column(Float, default=0.0)
    packaging_cost = Column(Float, default=0.0)
    uses_dtf = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.name,  # Para compatibilidade com código existente
            'name': self.name,
            'custo': self.cost,
            'cost': self.cost,
            'energy_cost': self.energy_cost,
            'energia': self.energy_cost,
            'transport_cost': self.transport_cost,
            'transp': self.transport_cost,
            'packaging_cost': self.packaging_cost,
            'emb': self.packaging_cost,
            'uses_dtf': self.uses_dtf,
            'usa_dtf': self.uses_dtf,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    document_type = Column(String(10))  # CPF/CNPJ
    document = Column(String(20))
    address = Column(Text)
    zip_code = Column(String(10))
    city = Column(String(50))
    state = Column(String(2))
    phone = Column(String(20))
    email = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    # Relacionamentos
    user = relationship("User")
    orders = relationship("Order", back_populates="customer")
    
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    trade_name = Column(String(100))
    supplier_type = Column(String(50))  # Camisaria, Serviços, etc.
    document_type = Column(String(10))
    document = Column(String(20))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    user = relationship("User")
    
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
    customer_id = Column(Integer, ForeignKey('customers.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    total_amount = Column(Float, default=0.0)
    items = Column(Text)  # JSON armazenado como Text
    delivery_type = Column(String(50))
    delivery_deadline = Column(String(50))
    payment_method = Column(String(50))
    payment_status = Column(String(20), default='pending')  # pending, paid
    delivery_status = Column(String(20), default='production')  # production, delivered
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    paid_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Relacionamentos
    customer = relationship("Customer", back_populates="orders")
    user = relationship("User", back_populates="orders")
    
    def to_dict(self):
        items_data = []
        try:
            if self.items:
                items_data = json.loads(self.items)
        except:
            items_data = []
            
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'user_id': self.user_id,
            'total_amount': self.total_amount,
            'items': items_data,
            'delivery_type': self.delivery_type,
            'delivery_deadline': self.delivery_deadline,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'delivery_status': self.delivery_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
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
    total_amount = Column(Float, default=0.0)
    items = Column(Text)  # JSON armazenado como Text
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    user_id = Column(Integer, ForeignKey('users.id'))
    
    user = relationship("User", back_populates="budgets")
    
    def to_dict(self):
        items_data = []
        try:
            if self.items:
                items_data = json.loads(self.items)
        except:
            items_data = []
            
        return {
            'id': self.id,
            'numero': self.budget_number,  # Para compatibilidade
            'budget_number': self.budget_number,
            'cliente': self.client_name,  # Para compatibilidade
            'client_name': self.client_name,
            'endereco': self.address,  # Para compatibilidade
            'address': self.address,
            'tipo_entrega': self.delivery_type,  # Para compatibilidade
            'delivery_type': self.delivery_type,
            'tipo_venda': self.sale_type,  # Para compatibilidade
            'sale_type': self.sale_type,
            'prazo_producao': self.production_deadline,  # Para compatibilidade
            'production_deadline': self.production_deadline,
            'valor_total': self.total_amount,  # Para compatibilidade
            'total_amount': self.total_amount,
            'items': items_data,
            'observacoes': self.notes,  # Para compatibilidade
            'notes': self.notes,
            'data': self.created_at.isoformat() if self.created_at else None,  # Para compatibilidade
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'user_id': self.user_id
        }

class SystemConfig(Base):
    __tablename__ = 'system_config'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(50), unique=True, nullable=False)
    value = Column(Text)
    value_type = Column(String(20))  # string, number, boolean, json
    category = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def get_value(self):
        if self.value_type == 'number':
            try:
                return float(self.value)
            except:
                return 0.0
        elif self.value_type == 'boolean':
            return self.value.lower() == 'true'
        elif self.value_type == 'json':
            try:
                return json.loads(self.value)
            except:
                return {}
        else:
            return self.value

# Criar engine e sessão APÓS definir todos os modelos
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Inicializa o banco de dados"""
    Base.metadata.create_all(bind=engine)
    
    # Criar usuário admin padrão se não existir
    db = SessionLocal()
    try:
        # Importar aqui para evitar import circular
        from utils.security import hash_password
        
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            admin_user = User(
                username='admin',
                email='admin@sejacapricho.com.br',
                password_hash=hash_password('admin123'),
                full_name='Administrador',
                is_active=True,
                is_admin=True
            )
            db.add(admin_user)
            db.commit()
        
        # Configurações padrão do sistema
        default_configs = [
            {'key': 'dtf_price_per_meter', 'value': '80.0', 'value_type': 'number', 'category': 'dtf', 'description': 'Preço do DTF por metro'},
            {'key': 'roll_width', 'value': '58.0', 'value_type': 'number', 'category': 'dtf', 'description': 'Largura do rolo em cm'},
            {'key': 'roll_height', 'value': '100', 'value_type': 'number', 'category': 'dtf', 'description': 'Altura do rolo em cm'},
            {'key': 'default_margin', 'value': '50.0', 'value_type': 'number', 'category': 'pricing', 'description': 'Margem padrão em %'},
            {'key': 'energy_cost_label', 'value': 'Energy (R$)', 'value_type': 'string', 'category': 'labels', 'description': 'Rótulo para custo de energia'},
            {'key': 'transport_cost_label', 'value': 'Transport (R$)', 'value_type': 'string', 'category': 'labels', 'description': 'Rótulo para custo de transporte'},
            {'key': 'packaging_cost_label', 'value': 'Packaging (R$)', 'value_type': 'string', 'category': 'labels', 'description': 'Rótulo para custo de embalagem'},
            {'key': 'energy_cost_value', 'value': '1.0', 'value_type': 'number', 'category': 'fixed_costs', 'description': 'Valor fixo para energia'},
            {'key': 'transport_cost_value', 'value': '2.0', 'value_type': 'number', 'category': 'fixed_costs', 'description': 'Valor fixo para transporte'},
            {'key': 'packaging_cost_value', 'value': '1.0', 'value_type': 'number', 'category': 'fixed_costs', 'description': 'Valor fixo para embalagem'},
            {'key': 'default_production_days', 'value': '5', 'value_type': 'number', 'category': 'general', 'description': 'Dias padrão para produção'},
        ]
        
        for config_data in default_configs:
            config_item = db.query(SystemConfig).filter(SystemConfig.key == config_data['key']).first()
            if not config_item:
                config_item = SystemConfig(**config_data)
                db.add(config_item)
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Erro ao inicializar banco de dados: {str(e)}")
        raise e
    finally:
        db.close()

def get_db():
    """Retorna uma sessão do banco de dados (para uso com FastAPI/Depends)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
