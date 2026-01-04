from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, Text, DateTime, JSON, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import Numeric
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from config import config

# Configurar engine do banco de dados
engine = create_engine(
    config.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_recycle=3600
)

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
    
    # Relacionamentos
    customers = relationship("Customer", back_populates="user", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SystemConfig(Base):
    __tablename__ = 'system_configs'
    
    key = Column(String(50), primary_key=True)
    value = Column(Text)
    value_type = Column(String(20))
    category = Column(String(50))
    description = Column(String(200))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    def get_value(self):
        """Retorna o valor no tipo correto"""
        if self.value_type == 'number':
            try:
                return float(self.value)
            except (ValueError, TypeError):
                return 0.0
        elif self.value_type == 'boolean':
            return self.value.lower() in ('true', '1', 'yes')
        elif self.value_type == 'json':
            try:
                return json.loads(self.value)
            except:
                return {}
        else:
            return self.value
    
    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'value_type': self.value_type,
            'category': self.category,
            'description': self.description
        }

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, unique=True)
    cost = Column(Numeric(10, 2), default=0.0)  # Custo base
    energy_cost = Column(Numeric(10, 2), default=0.0)  # Custo de energia
    transport_cost = Column(Numeric(10, 2), default=0.0)  # Custo de transporte
    packaging_cost = Column(Numeric(10, 2), default=0.0)  # Custo de embalagem
    uses_dtf = Column(Boolean, default=True)  # Se usa DTF
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="products")
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.name,
            'custo': float(self.cost) if self.cost else 0.0,
            'energy_cost': float(self.energy_cost) if self.energy_cost else 0.0,
            'transport_cost': float(self.transport_cost) if self.transport_cost else 0.0,
            'packaging_cost': float(self.packaging_cost) if self.packaging_cost else 0.0,
            'energia': float(self.energy_cost) if self.energy_cost else 0.0,
            'transp': float(self.transport_cost) if self.transport_cost else 0.0,
            'emb': float(self.packaging_cost) if self.packaging_cost else 0.0,
            'usa_dtf': self.uses_dtf,
            'uses_dtf': self.uses_dtf,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    document_type = Column(String(10))  # CPF, CNPJ
    document = Column(String(20))
    address = Column(Text)
    zip_code = Column(String(10))
    city = Column(String(50))
    state = Column(String(2))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'document_type': self.document_type,
            'document': self.document,
            'address': self.address,
            'zip_code': self.zip_code,
            'city': self.city,
            'state': self.state,
            'notes': self.notes,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'pedidos': [order.id for order in self.orders]
        }

class Supplier(Base):
    __tablename__ = 'suppliers'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    trade_name = Column(String(100))
    supplier_type = Column(String(50))  # Camisaria, Serviços, etc
    document_type = Column(String(10))  # CPF, CNPJ
    document = Column(String(20))
    address = Column(Text)
    phone = Column(String(20))
    email = Column(String(100))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="suppliers")
    
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
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Order(Base):
    __tablename__ = 'orders'
    
    id = Column(Integer, primary_key=True)
    order_number = Column(String(20), unique=True, nullable=False)
    total_amount = Column(Numeric(10, 2), nullable=False)
    items = Column(JSON)  # Lista de itens em JSON
    delivery_type = Column(String(50))  # Pronta Entrega, Sob Encomenda
    delivery_deadline = Column(String(50))
    delivery_status = Column(String(20), default='production')  # production, delivered
    payment_method = Column(String(50))
    payment_status = Column(String(20), default='pending')  # pending, paid
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    paid_at = Column(DateTime)
    delivered_at = Column(DateTime)
    
    # Relacionamentos
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    customer = relationship("Customer", back_populates="orders")
    
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="orders")
    
    def to_dict(self):
        return {
            'id': self.id,
            'order_number': self.order_number,
            'customer_id': self.customer_id,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'items': self.items if self.items else [],
            'delivery_type': self.delivery_type,
            'delivery_deadline': self.delivery_deadline,
            'delivery_status': self.delivery_status,
            'payment_method': self.payment_method,
            'payment_status': self.payment_status,
            'notes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None
        }

class Budget(Base):
    __tablename__ = 'budgets'
    
    id = Column(Integer, primary_key=True)
    budget_number = Column(String(20), unique=True, nullable=False)
    client_name = Column(String(100), nullable=False)
    address = Column(Text)
    delivery_type = Column(String(50))
    sale_type = Column(String(50))  # Revenda, Personalizado
    production_deadline = Column(String(50))
    total_amount = Column(Numeric(10, 2), nullable=False)
    items = Column(JSON)  # Lista de itens em JSON
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relacionamentos
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="budgets")
    
    def to_dict(self):
        return {
            'id': self.id,
            'budget_number': self.budget_number,
            'numero': self.budget_number,
            'client_name': self.client_name,
            'cliente': self.client_name,
            'address': self.address,
            'endereco': self.address,
            'delivery_type': self.delivery_type,
            'tipo_entrega': self.delivery_type,
            'sale_type': self.sale_type,
            'tipo_venda': self.sale_type,
            'production_deadline': self.production_deadline,
            'prazo_producao': self.production_deadline,
            'total_amount': float(self.total_amount) if self.total_amount else 0.0,
            'valor_total': float(self.total_amount) if self.total_amount else 0.0,
            'items': self.items if self.items else [],
            'notes': self.notes,
            'observacoes': self.notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'data': self.created_at.strftime('%d/%m/%Y') if self.created_at else None
        }

# Adicionar relacionamentos ausentes no User
User.products = relationship("Product", back_populates="user", cascade="all, delete-orphan")

# --- INICIALIZAÇÃO ---

def init_db():
    """Inicializa o banco de dados e cria tabelas"""
    try:
        print("🔄 Criando tabelas do banco de dados...")
        Base.metadata.create_all(bind=engine)
        db = SessionLocal()

        from sqlalchemy import inspect
        
        # Configurações padrão do sistema
        default_configs = [
            ('dtf_price_per_meter', '80.0', 'number', 'dtf', 'Preço do DTF por metro linear'),
            ('roll_width', '58.0', 'number', 'dtf', 'Largura do rolo de DTF (cm)'),
            ('roll_height', '100.0', 'number', 'dtf', 'Altura do rolo de DTF (cm)'),
            ('energy_cost_label', 'Energia (R$)', 'string', 'labels', 'Rótulo para custo de energia'),
            ('transport_cost_label', 'Transporte (R$)', 'string', 'labels', 'Rótulo para custo de transporte'),
            ('packaging_cost_label', 'Embalagem (R$)', 'string', 'labels', 'Rótulo para custo de embalagem'),
            ('energy_cost_value', '1.0', 'number', 'fixed_costs', 'Valor padrão para custo de energia'),
            ('transport_cost_value', '2.0', 'number', 'fixed_costs', 'Valor padrão para custo de transporte'),
            ('packaging_cost_value', '1.0', 'number', 'fixed_costs', 'Valor padrão para custo de embalagem'),
            ('default_margin', '50.0', 'number', 'pricing', 'Margem padrão em porcentagem'),
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
        
        # Criar usuário admin se não existir
        admin_user = db.query(User).filter(User.username == 'admin').first()
        if not admin_user:
            try:
                from security import hash_password
                admin_user = User(
                    username='admin',
                    email='admin@sejacapricho.com.br',
                    password_hash=hash_password('admin123'),
                    full_name='Administrador',
                    is_admin=True,
                    is_active=True
                )
                db.add(admin_user)
                print("👤 Usuário admin criado com senha: admin123")
            except ImportError:
                print("⚠️ Não foi possível criar usuário admin - módulo security não encontrado")
        
        db.commit()
        print("✅ Banco de dados inicializado com sucesso!")
        
    except Exception as e:
        if 'db' in locals():
            db.rollback()
        print(f"❌ Erro ao inicializar banco de dados: {e}")
        raise
    finally:
        if 'db' in locals():
            db.close()

def get_db():
    """Retorna uma sessão do banco de dados"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
