import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import tempfile
import sys
import os

st.set_page_config(
    page_title="Seja Capricho - Sistema",
    page_icon="👕",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# --- IMPORTAÇÕES ---
try:
    from auth import require_auth, get_current_user, show_login_register_page, auth_system, is_admin
    from models import init_db, get_db, SessionLocal, User, Product, Customer, Supplier, Order, Budget, SystemConfig
    from security import hash_password, verify_password, validate_email, validate_password_strength
    from config import config
    
    # Inicializar banco de dados
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
    
except Exception as e:
    st.error(f"❌ Erro ao inicializar o sistema: {e}")
    print(f"❌ Erro detalhado: {e}")
    st.stop()

# --- CONSTANTES E CORES ---
COR_ROXA = "#9370DB"
COR_AZUL_ARDOSIA = "#836FFF"
COR_LARANJA = "#FF7F00"
COR_FUNDO = "#0D1117"
COR_CARTAO = "#161B22"
COR_TEXTO = "#E6EDF3"
COR_BOTAO = "#1F6FEB"
COR_VERDE = "#238636"
COR_VERMELHA = "#DA3633"
COR_CINZA = "#30363D"
COR_AMARELA = "#FFD700"
COR_AZUL = "#1F6FEB"

# --- FUNÇÕES UTILITÁRIAS ---
def carregar_dados():
    """Carrega dados do banco de dados para o contexto atual"""
    db = SessionLocal()
    try:
        # Obter configurações do sistema
        configs = {}
        system_configs = db.query(SystemConfig).all()
        for cfg in system_configs:
            configs[cfg.key] = cfg.get_value()
        
        # Obter produtos
        products = [p.to_dict() for p in db.query(Product).filter(Product.is_active == True).all()]
        
        # Obter orçamentos
        budgets = [b.to_dict() for b in db.query(Budget).all()]
        
        # Obter clientes
        customers = [c.to_dict() for c in db.query(Customer).all()]
        
        # Obter fornecedores
        suppliers = [s.to_dict() for s in db.query(Supplier).all()]
        
        # Obter pedidos
        orders = [o.to_dict() for o in db.query(Order).all()]
        
        return {
            "config": configs,
            "produtos": products,
            "orcamentos": budgets,
            "clientes": customers,
            "fornecedores": suppliers,
            "pedidos": orders,
            "ultimo_numero_orcamento": max([b.get('budget_number', 0) for b in budgets], default=0),
            "ultimo_id_cliente": max([c.get('id', 0) for c in customers], default=0),
            "ultimo_id_fornecedor": max([s.get('id', 0) for s in suppliers], default=0),
            "ultimo_id_pedido": max([o.get('id', 0) for o in orders], default=0),
        }
    finally:
        db.close()

def formatar_moeda(valor):
    """Formata valor em moeda brasileira"""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def formatar_cpf(cpf):
    """Formata CPF"""
    cpf = str(cpf).replace(".", "").replace("-", "")
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def formatar_cnpj(cnpj):
    """Formata CNPJ"""
    cnpj = str(cnpj).replace(".", "").replace("-", "").replace("/", "")
    if len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def get_cor_status_pedido(pedido):
    """Retorna a cor baseada no status do pedido"""
    agora = datetime.now()
    data_criacao = datetime.fromisoformat(pedido['created_at']) if 'created_at' in pedido else datetime.now()
    
    if pedido.get('delivery_status') == 'delivered':
        return COR_AZUL  # Azul para entregue
    elif pedido.get('payment_status') == 'paid':
        return COR_VERDE  # Verde para pago
    elif (agora - data_criacao) > timedelta(hours=24):
        return COR_VERMELHA  # Vermelho para pendente > 24h
    else:
        return COR_AMARELA  # Amarelo para recente

def gerar_pdf(orcamento):
    """Gera PDF para um orçamento"""
    try:
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Criar documento
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Título
        title = Paragraph(f"ORÇAMENTO #{orcamento.get('budget_number', orcamento.get('numero', ''))}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Informações da empresa
        empresa_info = [
            ["Criatividade, Personalidade e muito Capricho!", ""],
            ["DTF Pricing Calculator", ""],
            [f"Data: {orcamento.get('created_at', orcamento.get('data', ''))}", ""]
        ]
        
        empresa_table = Table(empresa_info, colWidths=[doc.width/2.0]*2)
        empresa_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(empresa_table)
        elements.append(Spacer(1, 20))
        
        # Dados do Cliente
        cliente_data = [
            ["DADOS DO CLIENTE", ""],
            ["Cliente:", orcamento.get('client_name', orcamento.get('cliente', ''))],
            ["Endereço:", orcamento.get('address', orcamento.get('endereco', ''))],
            ["Tipo de Entrega:", orcamento.get('delivery_type', orcamento.get('tipo_entrega', ''))],
            ["Tipo de Venda:", orcamento.get('sale_type', orcamento.get('tipo_venda', ''))],
            ["Prazo de Produção:", orcamento.get('production_deadline', orcamento.get('prazo_producao', ''))]
        ]
        
        cliente_table = Table(cliente_data, colWidths=[doc.width/3.0, doc.width*2/3.0])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_ROXA)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(cliente_table)
        elements.append(Spacer(1, 20))
        
        # Itens do Orçamento
        items_data = [["ITENS DO ORÇAMENTO", "", "", ""], 
                     ["Produto", "Quantidade", "Valor Unitário (R$)", "Valor Total (R$)"]]
        
        items = orcamento.get('items', [])
        if isinstance(items, str):
            items = json.loads(items)
        
        for item in items:
            item_total = float(item.get('valor_unitario', item.get('unit_price', 0))) * float(item.get('quantidade', item.get('quantity', 0)))
            items_data.append([
                item.get('nome', item.get('name', '')),
                f"{item.get('quantidade', item.get('quantity', 0)):.0f}",
                formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0))),
                formatar_moeda(item_total)
            ])
        
        items_table = Table(items_data, colWidths=[doc.width*0.4, doc.width*0.2, doc.width*0.2, doc.width*0.2])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_LARANJA)),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(COR_AZUL_ARDOSIA)),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
            ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f9f9f9')),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('PADDING', (0, 2), (-1, 2), 8),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 20))
        
        # Resumo
        resumo_data = [
            ["RESUMO DO ORÇAMENTO", ""],
            ["Valor Total:", formatar_moeda(orcamento.get('total_amount', orcamento.get('valor_total', 0)))]
        ]
        
        resumo_table = Table(resumo_data, colWidths=[doc.width/2.0]*2)
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_VERDE)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('PADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (1, 1), (1, 1), colors.HexColor('#f0f8ff')),
        ]))
        
        elements.append(resumo_table)
        
        # Observações (se existirem)
        if orcamento.get('observacoes') or orcamento.get('notes'):
            elements.append(Spacer(1, 20))
            obs_text = orcamento.get('observacoes') or orcamento.get('notes', '')
            obs_data = [
                ["OBSERVAÇÕES"],
                [obs_text]
            ]
            
            obs_table = Table(obs_data, colWidths=[doc.width])
            obs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_CINZA)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 1), (-1, 1), 'LEFT'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('PADDING', (0, 1), (-1, 1), 8),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f5f5f5')),
            ]))
            
            elements.append(obs_table)
        
        # Rodapé
        elements.append(Spacer(1, 30))
        rodape = Paragraph(
            "CONDIÇÕES E INFORMAÇÕES ADICIONAIS<br/>"
            "1. Este orçamento tem validade de 30 dias a partir da data de emissão.<br/>"
            "2. O prazo de produção começa a contar após a confirmação do pedido e pagamento.<br/>"
            "3. Preços sujeitos a alteração sem aviso prévio.<br/>"
            "4. Para dúvidas, acesse nossos canais de atendimento.<br/>"
            "(75) 9155-5968 | @sejacapricho | sejacapricho.com.br",
            ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
        )
        elements.append(rodape)
        
        # Construir PDF
        doc.build(elements)
        return pdf_path
        
    except Exception as e:
        st.error(f"Erro ao gerar PDF: {str(e)}")
        return None

def gerar_nota_fiscal(pedido, cliente):
    """Gera nota fiscal/recibo para um pedido"""
    try:
        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        pdf_path = temp_file.name
        temp_file.close()
        
        # Criar documento
        doc = SimpleDocTemplate(pdf_path, pagesize=A4, 
                               rightMargin=72, leftMargin=72,
                               topMargin=72, bottomMargin=72)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Estilos personalizados
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            alignment=TA_CENTER,
            spaceAfter=12
        )
        
        # Título
        title = Paragraph(f"RECIBO / NOTA FISCAL", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Informações da empresa
        empresa_info = [
            ["Criatividade, Personalidade e muito Capricho!", ""],
            ["DTF Pricing Calculator", ""],
            [f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ""],
            [f"Nº do Pedido: #{pedido.get('order_number', pedido.get('id', ''))}", ""]
        ]
        
        empresa_table = Table(empresa_info, colWidths=[doc.width/2.0]*2)
        empresa_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(empresa_table)
        elements.append(Spacer(1, 20))
        
        # Dados do Cliente
        cliente_data = [
            ["DADOS DO CLIENTE", ""],
            ["Cliente:", cliente.get('name', '') if cliente else ''],
            ["Documento:", cliente.get('document', '') if cliente else ''],
            ["Endereço:", cliente.get('address', '') if cliente else ''],
            ["Telefone:", cliente.get('phone', '') if cliente else ''],
            ["Email:", cliente.get('email', '') if cliente else ''],
            ["Tipo de Entrega:", pedido.get('delivery_type', '')],
            ["Prazo de Entrega:", pedido.get('delivery_deadline', '')]
        ]
        
        cliente_table = Table(cliente_data, colWidths=[doc.width/3.0, doc.width*2/3.0])
        cliente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_ROXA)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f5f5f5')),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('PADDING', (0, 1), (-1, -1), 6),
        ]))
        
        elements.append(cliente_table)
        elements.append(Spacer(1, 20))
        
        # Itens do Pedido
        items_data = [["ITENS DO PEDIDO", "", "", ""], 
                     ["Produto", "Quantidade", "Valor Unitário (R$)", "Valor Total (R$)"]]
        
        items = pedido.get('items', [])
        if isinstance(items, str):
            items = json.loads(items)
        
        for item in items:
            item_total = float(item.get('valor_unitario', item.get('unit_price', 0))) * float(item.get('quantidade', item.get('quantity', 0)))
            items_data.append([
                item.get('nome', item.get('name', '')),
                f"{item.get('quantidade', item.get('quantity', 0)):.0f}",
                formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0))),
                formatar_moeda(item_total)
            ])
        
        items_table = Table(items_data, colWidths=[doc.width*0.4, doc.width*0.2, doc.width*0.2, doc.width*0.2])
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_LARANJA)),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(COR_AZUL_ARDOSIA)),
            ('TEXTCOLOR', (0, 0), (-1, 1), colors.white),
            ('ALIGN', (0, 0), (-1, 1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 2), (-1, 2), 'CENTER'),
            ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f9f9f9')),
            ('FONTSIZE', (0, 2), (-1, 2), 10),
            ('PADDING', (0, 2), (-1, 2), 8),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 20))
        
        # Resumo do Pedido
        resumo_data = [
            ["RESUMO DO PEDIDO", ""],
            ["Subtotal:", formatar_moeda(pedido.get('total_amount', 0))],
            ["Status de Pagamento:", "PAGO" if pedido.get('payment_status') == 'paid' else "PENDENTE"],
            ["Status de Entrega:", "ENTREGUE" if pedido.get('delivery_status') == 'delivered' else "EM PRODUÇÃO"]
        ]
        
        if pedido.get('payment_method'):
            resumo_data.insert(3, ["Forma de Pagamento:", pedido.get('payment_method')])
        
        resumo_table = Table(resumo_data, colWidths=[doc.width/2.0]*2)
        resumo_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_VERDE)),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('PADDING', (0, 1), (-1, -1), 8),
        ]))
        
        elements.append(resumo_table)
        
        # Observações
        if pedido.get('notes'):
            elements.append(Spacer(1, 20))
            obs_data = [
                ["OBSERVAÇÕES"],
                [pedido['notes']]
            ]
            
            obs_table = Table(obs_data, colWidths=[doc.width])
            obs_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COR_CINZA)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 1), (-1, 1), 'LEFT'),
                ('FONTSIZE', (0, 1), (-1, 1), 10),
                ('PADDING', (0, 1), (-1, 1), 8),
                ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f5f5f5')),
            ]))
            
            elements.append(obs_table)
        
        # Rodapé
        elements.append(Spacer(1, 30))
        rodape = Paragraph(
            "INFORMAÇÕES IMPORTANTES<br/>"
            "1. Este documento serve como recibo/nota fiscal simplificada.<br/>"
            "2. Guarde este comprovante para futuras referências.<br/>"
            "3. Para dúvidas ou reclamações, entre em contato.<br/>"
            "(75) 9155-5968 | @sejacapricho | sejacapricho.com.br<br/><br/>"
            f"Emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
        )
        elements.append(rodape)
        
        # Assinatura
        elements.append(Spacer(1, 40))
        assinatura_data = [
            ["________________________________"],
            ["Assinatura do Responsável"]
        ]
        
        assinatura_table = Table(assinatura_data, colWidths=[doc.width])
        assinatura_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ]))
        elements.append(assinatura_table)
        
        # Construir PDF
        doc.build(elements)
        return pdf_path
        
    except Exception as e:
        st.error(f"Erro ao gerar nota fiscal: {str(e)}")
        return None

# --- TELA: CALCULADORA ---
@require_auth()
def mostrar_calculadora():
    st.title("📱 Calculadora - Novo Orçamento")
    
    # Inicializar session state se necessário
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = []
    
    data = carregar_dados()
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Configuração do Produto")
        
        # Seleção de produto
        product_names = [p['nome'] for p in data['produtos']]
        if not product_names:
            product_names = ["Nenhum produto disponível"]
        
        produto_selecionado = st.selectbox("Produto", product_names)
        
        # Obter produto selecionado
        produto_atual = None
        for p in data['produtos']:
            if p['nome'] == produto_selecionado:
                produto_atual = p
                break
        
        if produto_atual:
            # Toggle DTF
            col_a, col_b = st.columns(2)
            with col_a:
                usa_dtf = st.toggle("DTF", value=produto_atual.get('usa_dtf', True))
            
            with col_b:
                incluir_custos_fixos = st.toggle("Incluir Custos Fixos", value=True)
            
            # Dimensões
            st.subheader("Dimensões (cm)")
            dim_cols = st.columns(4)
            with dim_cols[0]:
                frente_altura = st.number_input("Altura Frente", min_value=0.0, value=0.0, step=0.5)
            with dim_cols[1]:
                frente_largura = st.number_input("Largura Frente", min_value=0.0, value=0.0, step=0.5)
            with dim_cols[2]:
                costas_altura = st.number_input("Altura Costas", min_value=0.0, value=0.0, step=0.5)
            with dim_cols[3]:
                costas_largura = st.number_input("Largura Costas", min_value=0.0, value=0.0, step=0.5)
            
            # Quantidade e Margem
            qtd_cols = st.columns(2)
            with qtd_cols[0]:
                quantidade = st.number_input("Quantidade", min_value=1, value=1)
            with qtd_cols[1]:
                margem = st.number_input("Margem %", min_value=0.0, value=data['config'].get('default_margin', 50.0), step=1.0)
            
            # Botão calcular
            if st.button("Calcular Preço", type="primary", use_container_width=True):
                # Cálculo da área
                area_frente = frente_altura * frente_largura
                area_costas = costas_altura * costas_largura
                area_total = area_frente + area_costas
                
                # Cálculo DTF
                custo_dtf = 0
                if usa_dtf and area_total > 0:
                    preco_metro = data['config'].get('dtf_price_per_meter', 80.0)
                    largura_rolo = data['config'].get('roll_width', 58.0)
                    altura_rolo = data['config'].get('roll_height', 100)
                    area_metro_linear = largura_rolo * altura_rolo
                    custo_cm2 = preco_metro / area_metro_linear
                    custo_dtf = area_total * custo_cm2
                
                # Custos fixos
                custos_fixos = 0
                if incluir_custos_fixos:
                    custos_fixos = (produto_atual.get('energy_cost', produto_atual.get('energia', 0)) + 
                                   produto_atual.get('transport_cost', produto_atual.get('transp', 0)) + 
                                   produto_atual.get('packaging_cost', produto_atual.get('emb', 0)))
                    
                    # Adicionar custos fixos globais
                    custos_fixos += (data['config'].get('energy_cost_value', 1.0) + 
                                    data['config'].get('transport_cost_value', 2.0) + 
                                    data['config'].get('packaging_cost_value', 1.0))
                
                # Cálculo final
                custo_unitario = produto_atual.get('custo', produto_atual.get('cost', 0)) + custo_dtf + custos_fixos
                preco_unitario = custo_unitario * (1 + margem / 100)
                preco_total = preco_unitario * quantidade
                
                # Armazenar resultado na session
                st.session_state.calculation_result = {
                    'produto': produto_atual.get('nome', produto_atual.get('name', '')),
                    'preco_unitario': preco_unitario,
                    'quantidade': quantidade,
                    'preco_total': preco_total,
                    'area_total': area_total,
                    'usa_dtf': usa_dtf
                }
                
                st.success(f"Preço calculado: {formatar_moeda(preco_total)}")
    
    with col2:
        st.subheader("Resultados")
        
        if 'calculation_result' in st.session_state:
            result = st.session_state.calculation_result
            
            st.metric(
                label="Preço Total",
                value=formatar_moeda(result['preco_total']),
                delta=None
            )
            
            st.write(f"**Produto:** {result['produto']}")
            st.write(f"**Preço Unitário:** {formatar_moeda(result['preco_unitario'])}")
            st.write(f"**Quantidade:** {result['quantidade']}")
            st.write(f"**Área Total:** {result['area_total']:.2f} cm²")
            st.write(f"**DTF:** {'Sim' if result['usa_dtf'] else 'Não'}")
            
            # Botões para adicionar à seleção
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Adicionar à Seleção", use_container_width=True):
                    novo_item = {
                        'nome': result['produto'],
                        'preco_unitario': result['preco_unitario'],
                        'quantidade': result['quantidade'],
                        'preco_total': result['preco_total']
                    }
                    st.session_state.selected_products.append(novo_item)
                    st.success("Produto adicionado à seleção!")
                    st.rerun()
            
            with col_btn2:
                if st.button("Limpar Seleção", use_container_width=True):
                    st.session_state.selected_products = []
                    st.rerun()
        else:
            st.info("Calcule um preço para ver resultados aqui")
        
        # Lista de produtos selecionados
        if st.session_state.selected_products:
            st.subheader("Produtos Selecionados")
            selected_df = pd.DataFrame(st.session_state.selected_products)
            st.dataframe(selected_df, use_container_width=True, hide_index=True)
            
            total_selecionado = sum(p['preco_total'] for p in st.session_state.selected_products)
            st.metric("Total Selecionado", formatar_moeda(total_selecionado))
            
            # Botão para criar orçamento
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📋 Criar Orçamento", type="primary", use_container_width=True):
                    st.session_state.current_page = "create_budget"
                    st.rerun()
            with col_btn2:
                if st.button("🛒 Criar Pedido", type="secondary", use_container_width=True):
                    st.session_state.current_page = "novo_pedido"
                    st.rerun()
        else:
            st.info("Nenhum produto selecionado ainda")

# --- TELA: PRODUTOS ---
@require_auth()
def mostrar_produtos():
    st.title("📦 Gerenciamento de Produtos")
    
    data = carregar_dados()
    db = SessionLocal()
    
    try:
        # Formulário para adicionar/editar produto
        with st.expander("Adicionar/Editar Produto", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nome = st.text_input("Nome do Produto")
                custo = st.number_input("Custo (R$)", min_value=0.0, value=0.0, step=0.1)
            
            with col2:
                energia = st.number_input("Energia (R$)", min_value=0.0, value=0.0, step=0.1)
                transporte = st.number_input("Transporte (R$)", min_value=0.0, value=0.0, step=0.1)
            
            with col3:
                embalagem = st.number_input("Embalagem (R$)", min_value=0.0, value=0.0, step=0.1)
                usa_dtf = st.checkbox("Usa DTF", value=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Adicionar Produto", type="primary", use_container_width=True):
                    if nome.strip():
                        # Verificar se produto já existe
                        produto_existente = db.query(Product).filter(Product.name.ilike(nome.strip())).first()
                        
                        current_user = get_current_user()
                        
                        if produto_existente:
                            produto_existente.name = nome.strip()
                            produto_existente.cost = custo
                            produto_existente.energy_cost = energia
                            produto_existente.transport_cost = transporte
                            produto_existente.packaging_cost = embalagem
                            produto_existente.uses_dtf = usa_dtf
                            st.success(f"Produto '{nome}' atualizado!")
                        else:
                            novo_produto = Product(
                                name=nome.strip(),
                                cost=custo,
                                energy_cost=energia,
                                transport_cost=transporte,
                                packaging_cost=embalagem,
                                uses_dtf=usa_dtf
                            )
                            db.add(novo_produto)
                            st.success(f"Produto '{nome}' adicionado!")
                        
                        db.commit()
                        st.rerun()
                    else:
                        st.error("Nome do produto é obrigatório")
    finally:
        db.close()
    
    # Lista de produtos
    st.subheader("Lista de Produtos")
    
    if data['produtos']:
        # Criar DataFrame para exibição
        produtos_data = []
        for p in data['produtos']:
            produtos_data.append({
                "Produto": p['nome'],
                "Custo": formatar_moeda(p.get('custo', p.get('cost', 0))),
                "DTF": "✓" if p.get('usa_dtf', p.get('uses_dtf', False)) else "✗",
                "Energia": formatar_moeda(p.get('energy_cost', p.get('energia', 0))),
                "Transporte": formatar_moeda(p.get('transport_cost', p.get('transp', 0))),
                "Embalagem": formatar_moeda(p.get('packaging_cost', p.get('emb', 0)))
            })
        
        df = pd.DataFrame(produtos_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Opções para editar/excluir
        st.subheader("Gerenciar Produtos")
        produto_para_gerenciar = st.selectbox(
            "Selecione um produto para gerenciar",
            [p['nome'] for p in data['produtos']]
        )
        
        if produto_para_gerenciar:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("Editar Produto", use_container_width=True):
                    # Preencher formulário com dados do produto
                    for p in data['produtos']:
                        if p['nome'] == produto_para_gerenciar:
                            st.session_state.edit_product = p
                            st.info(f"Editando {p['nome']} - preencha o formulário acima")
                            break
            
            with col_del:
                if st.button("Excluir Produto", type="secondary", use_container_width=True):
                    db = SessionLocal()
                    try:
                        produto = db.query(Product).filter(Product.name == produto_para_gerenciar).first()
                        if produto:
                            produto.is_active = False
                            db.commit()
                            st.success(f"Produto '{produto_para_gerenciar}' excluído!")
                            st.rerun()
                    finally:
                        db.close()
    else:
        st.info("Nenhum produto cadastrado. Adicione seu primeiro produto acima.")

# --- TELA: ORÇAMENTOS ---
@require_auth()
def mostrar_orcamentos():
    st.title("📋 Orçamentos")
    
    data = carregar_dados()
    
    # Estatísticas
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total de Orçamentos", len(data['orcamentos']))
    with col_stats2:
        last_number = data['ultimo_numero_orcamento']
        st.metric("Último Número", f"#{last_number:04d}")
    with col_stats3:
        total_valor = sum(o.get('total_amount', o.get('valor_total', 0)) for o in data['orcamentos'])
        st.metric("Valor Total", formatar_moeda(total_valor))
    
    # Botão para novo orçamento
    if st.button("+ Novo Orçamento", type="primary"):
        st.session_state.current_page = "create_budget"
        st.rerun()
    
    # Lista de orçamentos
    st.subheader("Lista de Orçamentos")
    
    if data['orcamentos']:
        # Ordenar por número (mais recente primeiro)
        orcamentos_ordenados = sorted(data['orcamentos'], key=lambda x: x.get('budget_number', x.get('numero', 0)), reverse=True)
        
        for orcamento in orcamentos_ordenados:
            with st.container():
                col_info, col_acoes = st.columns([3, 1])
                
                with col_info:
                    # Determinar produto/itens
                    items = orcamento.get('items', [])
                    if isinstance(items, str):
                        items = json.loads(items)
                    
                    if items:
                        if len(items) > 1:
                            produto_info = f"Múltiplos Itens ({len(items)})"
                        else:
                            produto_info = items[0].get('nome', items[0].get('name', 'Item'))
                        quantidade = sum(float(it.get('quantidade', it.get('quantity', 0))) for it in items)
                    else:
                        produto_info = "Sem dados"
                        quantidade = 0
                    
                    budget_num = orcamento.get('budget_number', orcamento.get('numero', ''))
                    created_date = orcamento.get('created_at', orcamento.get('data', ''))
                    client_name = orcamento.get('client_name', orcamento.get('cliente', ''))
                    total_val = orcamento.get('total_amount', orcamento.get('valor_total', 0))
                    
                    st.write(f"**#{budget_num}** - {created_date}")
                    st.write(f"**Cliente:** {client_name}")
                    st.write(f"**Produto:** {produto_info} | **Qtd:** {quantidade:.0f}")
                    st.write(f"**Total:** {formatar_moeda(total_val)}")
                
                with col_acoes:
                    if st.button("Abrir", key=f"open_{budget_num}"):
                        st.session_state.view_budget = orcamento
                        st.session_state.current_page = "view_budget"
                        st.rerun()
                    
                    if st.button("PDF", key=f"pdf_{budget_num}"):
                        # Gerar PDF
                        pdf_path = gerar_pdf(orcamento)
                        if pdf_path:
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="Baixar PDF",
                                data=pdf_bytes,
                                file_name=f"Orcamento_{budget_num}.pdf",
                                mime="application/pdf"
                            )
                    
                    if st.button("Excluir", key=f"del_{budget_num}", type="secondary"):
                        db = SessionLocal()
                        try:
                            budget = db.query(Budget).filter(Budget.budget_number == budget_num).first()
                            if budget:
                                db.delete(budget)
                                db.commit()
                                st.success(f"Orçamento #{budget_num} excluído!")
                                st.rerun()
                        finally:
                            db.close()
                
                st.divider()
    else:
        st.info("Nenhum orçamento criado ainda. Crie seu primeiro orçamento!")

# --- TELA: CRIAR ORÇAMENTO ---
@require_auth()
def mostrar_criar_orcamento():
    st.title("📝 Criar Novo Orçamento")
    
    data = carregar_dados()
    
    # Inicializar variáveis
    if 'manual_items' not in st.session_state:
        st.session_state.manual_items = []
    
    # Formulário principal
    with st.form("orcamento_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Cliente *", placeholder="Nome do cliente")
            endereco = st.text_area("Endereço", placeholder="Endereço completo")
            tipo_entrega = st.radio("Tipo de Entrega", ["Pronta Entrega", "Sob Encomenda"])
            prazo_producao = st.text_input("Prazo de Produção", value="5 dias úteis")
        
        with col2:
            data_orcamento = st.date_input("Data", value=datetime.now())
            tipo_venda = st.radio("Tipo de Venda", ["Revenda", "Personalizado"])
            observacoes = st.text_area("Observações", placeholder="Informações adicionais")
        
        # Seção para adicionar itens manualmente
        with st.expander("Adicionar Item Manualmente", expanded=False):
            prod_col1, prod_col2, prod_col3 = st.columns(3)
            with prod_col1:
                produto_manual = st.selectbox(
                    "Produto",
                    ["Apenas DTF"] + [p['nome'] for p in data['produtos']],
                    key="produto_manual_select"
                )
            with prod_col2:
                quantidade_manual = st.number_input("Quantidade", min_value=1, value=1, key="qtd_manual")
            with prod_col3:
                valor_unitario_manual = st.number_input("Valor Unitário (R$)", min_value=0.0, value=0.0, step=0.01, key="valor_manual")
            
            if st.form_submit_button("Adicionar Item ao Orçamento", type="secondary", use_container_width=True, key="add_item_btn"):
                if produto_manual and quantidade_manual > 0:
                    novo_item = {
                        "nome": produto_manual,
                        "quantidade": quantidade_manual,
                        "valor_unitario": valor_unitario_manual,
                        "preco_total": valor_unitario_manual * quantidade_manual
                    }
                    st.session_state.manual_items.append(novo_item)
                    st.success(f"Item '{produto_manual}' adicionado!")
        
        # Mostrar itens adicionados manualmente
        if st.session_state.manual_items:
            st.write("**Itens Manuais Adicionados:**")
            for i, item in enumerate(st.session_state.manual_items):
                col_item1, col_item2, col_item3 = st.columns([3, 1, 2])
                with col_item1:
                    st.write(f"• {item['nome']}")
                with col_item2:
                    st.write(f"Qtd: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['valor_unitario'])}")
                    
                    if st.form_submit_button(f"Remover", key=f"remove_{i}"):
                        st.session_state.manual_items.pop(i)
                        st.rerun()
        
        # Mostrar itens da calculadora
        if st.session_state.get('selected_products'):
            st.write("**Itens da Calculadora:**")
            for i, item in enumerate(st.session_state.selected_products):
                col_item1, col_item2, col_item3 = st.columns([3, 1, 2])
                with col_item1:
                    st.write(f"• {item['nome']}")
                with col_item2:
                    st.write(f"Qtd: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['preco_unitario'])}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            save_clicked = st.form_submit_button("Salvar Orçamento", type="primary", use_container_width=True, key="save_budget")
        
        with col_btn2:
            save_pdf_clicked = st.form_submit_button("Salvar e Gerar PDF", use_container_width=True, key="save_pdf")
        
        with col_btn3:
            cancel_clicked = st.form_submit_button("Cancelar", type="secondary", use_container_width=True, key="cancel_budget")
    
    # Processar ações APÓS o formulário
    if cancel_clicked:
        if 'manual_items' in st.session_state:
            st.session_state.manual_items = []
        st.session_state.current_page = "calculator"
        st.rerun()
    
    if save_clicked or save_pdf_clicked:
        if not cliente or not cliente.strip():
            st.error("❌ Nome do cliente é obrigatório!")
        else:
            # Calcular valor total
            total = 0
            
            # Somar itens da calculadora
            if st.session_state.get('selected_products'):
                total += sum(item['preco_total'] for item in st.session_state.selected_products)
            
            # Somar itens manuais
            if st.session_state.manual_items:
                total += sum(item['preco_total'] for item in st.session_state.manual_items)
            
            if total <= 0:
                st.warning("⚠️ Adicione pelo menos um item ao orçamento!")
            else:
                # Criar novo orçamento no banco de dados
                db = SessionLocal()
                try:
                    current_user = get_current_user()
                    user = db.query(User).filter(User.id == current_user['id']).first()
                    
                    # Gerar número do orçamento
                    ultimo_numero = db.query(Budget).count() + 1
                    
                    # Preparar itens para salvar
                    itens_para_salvar = []
                    
                    # Adicionar itens da calculadora
                    if st.session_state.get('selected_products'):
                        for item in st.session_state.selected_products:
                            itens_para_salvar.append({
                                "nome": item['nome'],
                                "quantidade": item['quantidade'],
                                "valor_unitario": item['preco_unitario']
                            })
                    
                    # Adicionar itens manuais
                    if st.session_state.manual_items:
                        for item in st.session_state.manual_items:
                            itens_para_salvar.append({
                                "nome": item['nome'],
                                "quantidade": item['quantidade'],
                                "valor_unitario": item['valor_unitario']
                            })
                    
                    novo_orcamento = Budget(
                        budget_number=str(ultimo_numero).zfill(4),
                        client_name=cliente.strip(),
                        address=endereco.strip(),
                        delivery_type=tipo_entrega,
                        sale_type=tipo_venda,
                        production_deadline=prazo_producao,
                        total_amount=total,
                        items=json.dumps(itens_para_salvar),
                        notes=observacoes.strip(),
                        user=user
                    )
                    
                    db.add(novo_orcamento)
                    db.commit()
                    
                    st.success(f"✅ Orçamento #{ultimo_numero:04d} salvo com sucesso!")
                    
                    # Limpar dados temporários
                    if 'selected_products' in st.session_state:
                        st.session_state.selected_products = []
                    if 'manual_items' in st.session_state:
                        st.session_state.manual_items = []
                    
                    # Gerar PDF se solicitado
                    if save_pdf_clicked:
                        pdf_path = gerar_pdf(novo_orcamento.to_dict())
                        if pdf_path:
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="📄 Baixar PDF",
                                data=pdf_bytes,
                                file_name=f"Orcamento_{ultimo_numero:04d}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                    
                    # Opção para ir para a lista de orçamentos
                    if st.button("Ver Lista de Orçamentos"):
                        st.session_state.current_page = "orcamentos"
                        st.rerun()
                        
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao salvar orçamento: {str(e)}")
                finally:
                    db.close()

# --- TELA: VER ORÇAMENTO ---
@require_auth()
def mostrar_ver_orcamento():
    if 'view_budget' not in st.session_state:
        st.session_state.current_page = "orcamentos"
        st.rerun()
    
    orcamento = st.session_state.view_budget
    
    st.title(f"Orçamento #{orcamento.get('budget_number', orcamento.get('numero', ''))}")
    
    # Informações principais
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write(f"**Cliente:** {orcamento.get('client_name', orcamento.get('cliente', ''))}")
        st.write(f"**Data:** {orcamento.get('created_at', orcamento.get('data', ''))}")
        st.write(f"**Tipo de Entrega:** {orcamento.get('delivery_type', orcamento.get('tipo_entrega', ''))}")
    
    with col_info2:
        st.write(f"**Tipo de Venda:** {orcamento.get('sale_type', orcamento.get('tipo_venda', ''))}")
        st.write(f"**Endereço:** {orcamento.get('address', orcamento.get('endereco', ''))}")
        st.write(f"**Prazo:** {orcamento.get('production_deadline', orcamento.get('prazo_producao', ''))}")
    
    # Itens
    st.subheader("Itens")
    items = orcamento.get('items', [])
    if isinstance(items, str):
        items = json.loads(items)
    
    if items:
        itens_data = []
        for item in items:
            itens_data.append({
                "Produto": item.get('nome', item.get('name', 'Sem nome')),
                "Quantidade": item.get('quantidade', item.get('quantity', 0)),
                "Valor Unitário": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0))),
                "Total": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0)) * item.get('quantidade', item.get('quantity', 1)))
            })
        
        df = pd.DataFrame(itens_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif 'produto' in orcamento:
        st.write(f"**Produto:** {orcamento['produto']}")
        st.write(f"**Quantidade:** {orcamento.get('quantidade', 0)}")
        st.write(f"**Valor Unitário:** {formatar_moeda(orcamento.get('valor_unitario', 0))}")
    
    # Total
    st.metric("Valor Total", formatar_moeda(orcamento.get('total_amount', orcamento.get('valor_total', 0))))
    
    # Observações
    if orcamento.get('observacoes') or orcamento.get('notes'):
        st.subheader("Observações")
        st.write(orcamento.get('observacoes') or orcamento.get('notes', ''))
    
    # Botões de ação
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Gerar PDF", type="primary", use_container_width=True):
            pdf_path = gerar_pdf(orcamento)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="Baixar PDF",
                    data=pdf_bytes,
                    file_name=f"Orcamento_{orcamento.get('budget_number', orcamento.get('numero', ''))}.pdf",
                    mime="application/pdf"
                )
    
    with col_btn2:
        if st.button("Editar", use_container_width=True):
            st.warning("Função de edição não implementada na versão web")
    
    with col_btn3:
        if st.button("Voltar para Lista", type="secondary", use_container_width=True):
            del st.session_state.view_budget
            st.session_state.current_page = "orcamentos"
            st.rerun()

# --- TELA: CLIENTES ---
@require_auth()
def mostrar_clientes():
    st.title("👥 Clientes")
    
    data = carregar_dados()
    
    # Estatísticas
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total de Clientes", len(data['clientes']))
    with col_stats2:
        pedidos_totais = sum(len(cliente.get('pedidos', [])) for cliente in data['clientes'])
        st.metric("Total de Pedidos", pedidos_totais)
    with col_stats3:
        clientes_com_pedidos = sum(1 for cliente in data['clientes'] if len(cliente.get('pedidos', [])) > 0)
        st.metric("Clientes Ativos", clientes_com_pedidos)
    
    # Botão para novo cliente
    if st.button("+ Novo Cliente", type="primary"):
        st.session_state.current_page = "novo_cliente"
        st.rerun()
    
    # Lista de clientes
    st.subheader("Lista de Clientes")
    
    if data['clientes']:
        for cliente in data['clientes']:
            cor_borda = COR_VERDE if len(cliente.get('pedidos', [])) > 0 else COR_CINZA
            
            with st.container():
                st.markdown(f"""
                <div style="border-left: 5px solid {cor_borda}; padding-left: 10px; margin-bottom: 10px;">
                """, unsafe_allow_html=True)
                
                col_info, col_acoes = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**{cliente['name']}**")
                    if cliente.get('document'):
                        st.write(f"**Documento:** {cliente['document']}")
                    if cliente.get('address'):
                        st.write(f"**Endereço:** {cliente['address']}")
                    if cliente.get('zip_code'):
                        st.write(f"**CEP:** {cliente['zip_code']}")
                    
                    # Contar pedidos
                    num_pedidos = len(cliente.get('pedidos', []))
                    pedidos_pagos = sum(1 for pedido_id in cliente.get('pedidos', []) 
                                      for p in data['pedidos'] if p['id'] == pedido_id and p.get('payment_status') == 'paid')
                    
                    st.write(f"**Pedidos:** {num_pedidos} (Pagos: {pedidos_pagos})")
                
                with col_acoes:
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("📋", key=f"view_cliente_{cliente['id']}", help="Visualizar/Editar"):
                            st.session_state.view_cliente = cliente
                            st.session_state.current_page = "view_cliente"
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🛒", key=f"order_cliente_{cliente['id']}", help="Novo Pedido"):
                            st.session_state.novo_pedido_cliente = cliente
                            st.session_state.current_page = "novo_pedido"
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.divider()
    else:
        st.info("Nenhum cliente cadastrado. Crie seu primeiro cliente!")

# --- TELA: NOVO CLIENTE ---
@require_auth()
def mostrar_novo_cliente():
    st.title("👤 Novo Cliente")
    
    db = SessionLocal()
    
    with st.form("cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome *", placeholder="Nome completo")
            email = st.text_input("Email", placeholder="email@exemplo.com")
            telefone = st.text_input("Telefone", placeholder="(00) 00000-0000")
            
            tipo_documento = st.selectbox("Tipo de Documento", ["CPF", "CNPJ"])
            
            if tipo_documento == "CPF":
                documento = st.text_input("CPF", placeholder="000.000.000-00")
                if documento:
                    documento = formatar_cpf(documento)
            else:
                documento = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                if documento:
                    documento = formatar_cnpj(documento)
        
        with col2:
            endereco = st.text_area("Endereço", placeholder="Rua, Número, Bairro")
            cep = st.text_input("CEP", placeholder="00000-000")
            cidade = st.text_input("Cidade", placeholder="Cidade")
            estado = st.text_input("Estado", placeholder="Estado", max_chars=2)
            observacoes = st.text_area("Observações", placeholder="Informações adicionais")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            submit = st.form_submit_button("Salvar Cliente", type="primary", use_container_width=True)
        
        with col_btn2:
            save_and_order = st.form_submit_button("Salvar e Criar Pedido", use_container_width=True)
        
        with col_btn3:
            cancel = st.form_submit_button("Cancelar", type="secondary", use_container_width=True)
    
    if cancel:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    if submit or save_and_order:
        if not nome.strip():
            st.error("❌ Nome do cliente é obrigatório!")
        else:
            try:
                current_user = get_current_user()
                user = db.query(User).filter(User.id == current_user['id']).first()
                
                novo_cliente = Customer(
                    name=nome.strip(),
                    email=email.strip(),
                    phone=telefone.strip(),
                    document_type=tipo_documento,
                    document=documento.strip() if documento else "",
                    address=endereco.strip(),
                    zip_code=cep.strip(),
                    city=cidade.strip(),
                    state=estado.strip(),
                    notes=observacoes.strip(),
                    user=user
                )
                
                db.add(novo_cliente)
                db.commit()
                
                st.success(f"✅ Cliente '{nome}' salvo com sucesso!")
                
                if save_and_order:
                    st.session_state.novo_pedido_cliente = novo_cliente.to_dict()
                    st.session_state.current_page = "novo_pedido"
                    st.rerun()
                else:
                    if st.button("Voltar para Lista de Clientes"):
                        st.session_state.current_page = "clientes"
                        st.rerun()
                        
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar cliente: {str(e)}")
            finally:
                db.close()

# --- TELA: VER CLIENTE ---
@require_auth()
def mostrar_ver_cliente():
    if 'view_cliente' not in st.session_state:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    cliente = st.session_state.view_cliente
    data = carregar_dados()
    
    st.title(f"👤 {cliente['name']}")
    
    # Abas para informações do cliente
    tab1, tab2, tab3 = st.tabs(["📋 Informações", "🛒 Pedidos", "📊 Estatísticas"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Nome:** {cliente['name']}")
            if cliente.get('email'):
                st.write(f"**Email:** {cliente['email']}")
            if cliente.get('phone'):
                st.write(f"**Telefone:** {cliente['phone']}")
            if cliente.get('document'):
                st.write(f"**Documento ({cliente.get('document_type', '')}):** {cliente['document']}")
        
        with col2:
            if cliente.get('address'):
                st.write(f"**Endereço:** {cliente['address']}")
            if cliente.get('zip_code'):
                st.write(f"**CEP:** {cliente['zip_code']}")
            if cliente.get('city'):
                st.write(f"**Cidade:** {cliente['city']}")
            if cliente.get('state'):
                st.write(f"**Estado:** {cliente['state']}")
            if cliente.get('notes'):
                st.write(f"**Observações:** {cliente['notes']}")
        
        st.write(f"**Data de Cadastro:** {cliente.get('created_at', 'N/A')}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("Editar Cliente", type="primary", use_container_width=True):
                st.session_state.edit_cliente = cliente
                st.session_state.current_page = "edit_cliente"
                st.rerun()
        
        with col_btn2:
            if st.button("Novo Pedido", use_container_width=True):
                st.session_state.novo_pedido_cliente = cliente
                st.session_state.current_page = "novo_pedido"
                st.rerun()
        
        with col_btn3:
            if st.button("Voltar para Lista", type="secondary", use_container_width=True):
                del st.session_state.view_cliente
                st.session_state.current_page = "clientes"
                st.rerun()
    
    with tab2:
        st.subheader("Pedidos do Cliente")
        
        # Filtrar pedidos deste cliente
        pedidos_cliente = [p for p in data['pedidos'] if p.get('customer_id') == cliente['id']]
        
        if pedidos_cliente:
            # Ordenar por data (mais recente primeiro)
            pedidos_cliente.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            
            for pedido in pedidos_cliente:
                cor = get_cor_status_pedido(pedido)
                
                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 5px solid {cor}; padding-left: 10px; margin-bottom: 10px;">
                    """, unsafe_allow_html=True)
                    
                    col_info, col_status, col_acoes = st.columns([3, 2, 1])
                    
                    with col_info:
                        st.write(f"**Pedido #{pedido.get('order_number', pedido.get('id', ''))}** - {pedido.get('created_at', '')}")
                        st.write(f"**Total:** {formatar_moeda(pedido.get('total_amount', 0))}")
                        
                        # Mostrar produtos
                        items = pedido.get('items', [])
                        if isinstance(items, str):
                            items = json.loads(items)
                        
                        if items:
                            produtos = ", ".join([item.get('nome', item.get('name', '')) for item in items[:3]])
                            if len(items) > 3:
                                produtos += f" (+{len(items) - 3} mais)"
                            st.write(f"**Produtos:** {produtos}")
                    
                    with col_status:
                        # Status de pagamento
                        if pedido.get('payment_status') == 'paid':
                            st.write("🟢 **Pago**")
                            if pedido.get('payment_method'):
                                st.write(f"({pedido['payment_method']})")
                        else:
                            st.write("🔴 **Pagamento Pendente**")
                        
                        # Status de entrega
                        if pedido.get('delivery_status') == 'delivered':
                            st.write("✓ **Entregue**")
                        else:
                            st.write("⏳ **Em Produção**")
                    
                    with col_acoes:
                        if st.button("Visualizar", key=f"view_pedido_{pedido.get('id', '')}"):
                            st.session_state.view_pedido = pedido
                            st.session_state.current_page = "view_pedido"
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.divider()
        else:
            st.info("Este cliente ainda não tem pedidos.")
        
        # Botão para novo pedido
        if st.button("+ Novo Pedido para este Cliente", type="primary"):
            st.session_state.novo_pedido_cliente = cliente
            st.session_state.current_page = "novo_pedido"
            st.rerun()
    
    with tab3:
        st.subheader("Estatísticas do Cliente")
        
        # Filtrar pedidos deste cliente
        pedidos_cliente = [p for p in data['pedidos'] if p.get('customer_id') == cliente['id']]
        
        if pedidos_cliente:
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                total_pedidos = len(pedidos_cliente)
                st.metric("Total de Pedidos", total_pedidos)
            
            with col_stat2:
                pedidos_pagos = sum(1 for p in pedidos_cliente if p.get('payment_status') == 'paid')
                st.metric("Pedidos Pagos", pedidos_pagos)
            
            with col_stat3:
                pedidos_entregues = sum(1 for p in pedidos_cliente if p.get('delivery_status') == 'delivered')
                st.metric("Pedidos Entregues", pedidos_entregues)
            
            # Valor total gasto
            valor_total = sum(p.get('total_amount', 0) for p in pedidos_cliente)
            st.metric("Total Gasto", formatar_moeda(valor_total))
            
            # Último pedido
            if pedidos_cliente:
                ultimo_pedido = max(pedidos_cliente, key=lambda x: x.get('created_at', ''))
                st.write(f"**Último Pedido:** #{ultimo_pedido.get('order_number', ultimo_pedido.get('id', ''))} - {ultimo_pedido.get('created_at', '')}")
                st.write(f"**Status:** {'Pago' if ultimo_pedido.get('payment_status') == 'paid' else 'Pendente'} | {'Entregue' if ultimo_pedido.get('delivery_status') == 'delivered' else 'Em Produção'}")
        else:
            st.info("Nenhuma estatística disponível - cliente ainda não tem pedidos.")

# --- TELA: EDITAR CLIENTE ---
@require_auth()
def mostrar_editar_cliente():
    if 'edit_cliente' not in st.session_state:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    cliente = st.session_state.edit_cliente
    db = SessionLocal()
    
    st.title(f"✏️ Editar Cliente: {cliente['name']}")
    
    with st.form("edit_cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome *", value=cliente.get('name', ''), placeholder="Nome completo")
            email = st.text_input("Email", value=cliente.get('email', ''), placeholder="email@exemplo.com")
            telefone = st.text_input("Telefone", value=cliente.get('phone', ''), placeholder="(00) 00000-0000")
            
            tipo_documento = st.selectbox("Tipo de Documento", ["CPF", "CNPJ"], 
                                         index=0 if cliente.get('document_type') == 'CPF' else 1)
            
            if tipo_documento == "CPF":
                documento = st.text_input("CPF", value=cliente.get('document', ''), placeholder="000.000.000-00")
                if documento:
                    documento = formatar_cpf(documento)
            else:
                documento = st.text_input("CNPJ", value=cliente.get('document', ''), placeholder="00.000.000/0000-00")
                if documento:
                    documento = formatar_cnpj(documento)
        
        with col2:
            endereco = st.text_area("Endereço", value=cliente.get('address', ''), 
                                   placeholder="Rua, Número, Bairro")
            cep = st.text_input("CEP", value=cliente.get('zip_code', ''), placeholder="00000-000")
            cidade = st.text_input("Cidade", value=cliente.get('city', ''), placeholder="Cidade")
            estado = st.text_input("Estado", value=cliente.get('state', ''), placeholder="Estado", max_chars=2)
            observacoes = st.text_area("Observações", value=cliente.get('notes', ''), 
                                      placeholder="Informações adicionais")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submit = st.form_submit_button("Salvar Alterações", type="primary", use_container_width=True)
        
        with col_btn2:
            cancel = st.form_submit_button("Cancelar", type="secondary", use_container_width=True)
    
    if cancel:
        del st.session_state.edit_cliente
        st.session_state.current_page = "clientes"
        st.rerun()
    
    if submit:
        if not nome.strip():
            st.error("❌ Nome do cliente é obrigatório!")
        else:
            try:
                customer = db.query(Customer).filter(Customer.id == cliente['id']).first()
                if customer:
                    customer.name = nome.strip()
                    customer.email = email.strip()
                    customer.phone = telefone.strip()
                    customer.document_type = tipo_documento
                    customer.document = documento.strip() if documento else ""
                    customer.address = endereco.strip()
                    customer.zip_code = cep.strip()
                    customer.city = cidade.strip()
                    customer.state = estado.strip()
                    customer.notes = observacoes.strip()
                    
                    db.commit()
                    st.success(f"✅ Cliente '{nome}' atualizado com sucesso!")
                    
                    if st.button("Voltar para Cliente"):
                        del st.session_state.edit_cliente
                        st.session_state.view_cliente = customer.to_dict()
                        st.session_state.current_page = "view_cliente"
                        st.rerun()
                else:
                    st.error("Cliente não encontrado no banco de dados")
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao atualizar cliente: {str(e)}")
            finally:
                db.close()

# --- TELA: FORNECEDORES ---
@require_auth()
def mostrar_fornecedores():
    st.title("🏭 Fornecedores")
    
    data = carregar_dados()
    
    # Estatísticas
    col_stats1, col_stats2 = st.columns(2)
    with col_stats1:
        st.metric("Total de Fornecedores", len(data['fornecedores']))
    with col_stats2:
        tipos = set(f.get('supplier_type', '') for f in data['fornecedores'])
        st.metric("Categorias", len(tipos))
    
    # Botão para novo fornecedor
    if st.button("+ Novo Fornecedor", type="primary"):
        st.session_state.current_page = "novo_fornecedor"
        st.rerun()
    
    # Lista de fornecedores por categoria
    st.subheader("Lista de Fornecedores")
    
    if data['fornecedores']:
        # Agrupar por tipo
        fornecedores_por_tipo = {}
        for fornecedor in data['fornecedores']:
            tipo = fornecedor.get('supplier_type', 'Outros')
            if tipo not in fornecedores_por_tipo:
                fornecedores_por_tipo[tipo] = []
            fornecedores_por_tipo[tipo].append(fornecedor)
        
        for tipo, fornecedores in fornecedores_por_tipo.items():
            with st.expander(f"{tipo} ({len(fornecedores)})", expanded=True):
                for fornecedor in fornecedores:
                    with st.container():
                        col_info, col_acoes = st.columns([3, 1])
                        
                        with col_info:
                            st.write(f"**{fornecedor['name']}**")
                            if fornecedor.get('trade_name'):
                                st.write(f"**Nome Fantasia:** {fornecedor['trade_name']}")
                            if fornecedor.get('document'):
                                st.write(f"**Documento:** {fornecedor['document']}")
                            if fornecedor.get('address'):
                                st.write(f"**Endereço:** {fornecedor['address']}")
                            if fornecedor.get('notes'):
                                st.write(f"**Observações:** {fornecedor['notes']}")
                        
                        with col_acoes:
                            if st.button("Editar", key=f"edit_fornecedor_{fornecedor['id']}"):
                                st.session_state.edit_fornecedor = fornecedor
                                st.session_state.current_page = "edit_fornecedor"
                                st.rerun()
                        
                        st.divider()
    else:
        st.info("Nenhum fornecedor cadastrado. Crie seu primeiro fornecedor!")

# --- TELA: NOVO FORNECEDOR ---
@require_auth()
def mostrar_novo_fornecedor():
    st.title("🏭 Novo Fornecedor")
    
    db = SessionLocal()
    
    with st.form("fornecedor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome *", placeholder="Nome da empresa")
            nome_fantasia = st.text_input("Nome Fantasia", placeholder="Nome fantasia (opcional)")
            
            tipo = st.selectbox("Tipo", ["Camisaria", "Serviços", "Canecas e Brindes", 
                                        "DTF e Estamparia", "Acessórios", "Outros"])
            
            tipo_documento = st.selectbox("Tipo de Documento", ["Nenhum", "CPF", "CNPJ"])
            
            if tipo_documento != "Nenhum":
                if tipo_documento == "CPF":
                    documento = st.text_input("CPF", placeholder="000.000.000-00")
                    if documento:
                        documento = formatar_cpf(documento)
                else:
                    documento = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                    if documento:
                        documento = formatar_cnpj(documento)
            else:
                documento = ""
        
        with col2:
            endereco = st.text_area("Endereço", placeholder="Endereço completo")
            telefone = st.text_input("Telefone", placeholder="(00) 00000-0000")
            email = st.text_input("Email", placeholder="email@exemplo.com")
            observacoes = st.text_area("Observações", placeholder="Informações adicionais")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submit = st.form_submit_button("Salvar Fornecedor", type="primary", use_container_width=True)
        
        with col_btn2:
            cancel = st.form_submit_button("Cancelar", type="secondary", use_container_width=True)
    
    if cancel:
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    if submit:
        if not nome.strip():
            st.error("❌ Nome do fornecedor é obrigatório!")
        else:
            try:
                current_user = get_current_user()
                user = db.query(User).filter(User.id == current_user['id']).first()
                
                novo_fornecedor = Supplier(
                    name=nome.strip(),
                    trade_name=nome_fantasia.strip(),
                    supplier_type=tipo,
                    document_type=tipo_documento if tipo_documento != "Nenhum" else "",
                    document=documento.strip(),
                    address=endereco.strip(),
                    phone=telefone.strip(),
                    email=email.strip(),
                    notes=observacoes.strip(),
                    user=user
                )
                
                db.add(novo_fornecedor)
                db.commit()
                
                st.success(f"✅ Fornecedor '{nome}' salvo com sucesso!")
                
                if st.button("Voltar para Lista de Fornecedores"):
                    st.session_state.current_page = "fornecedores"
                    st.rerun()
                    
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar fornecedor: {str(e)}")
            finally:
                db.close()

# --- TELA: EDITAR FORNECEDOR ---
@require_auth()
def mostrar_editar_fornecedor():
    if 'edit_fornecedor' not in st.session_state:
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    fornecedor = st.session_state.edit_fornecedor
    db = SessionLocal()
    
    st.title(f"✏️ Editar Fornecedor: {fornecedor['name']}")
    
    with st.form("edit_fornecedor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Nome *", value=fornecedor.get('name', ''), placeholder="Nome da empresa")
            nome_fantasia = st.text_input("Nome Fantasia", value=fornecedor.get('trade_name', ''), 
                                         placeholder="Nome fantasia (opcional)")
            
            tipo = st.selectbox("Tipo", ["Camisaria", "Serviços", "Canecas e Brindes", 
                                        "DTF e Estamparia", "Acessórios", "Outros"],
                               index=["Camisaria", "Serviços", "Canecas e Brindes", 
                                     "DTF e Estamparia", "Acessórios", "Outros"].index(
                                         fornecedor.get('supplier_type', 'Outros')))
            
            tipo_documento_atual = fornecedor.get('document_type', 'Nenhum')
            tipo_documento = st.selectbox("Tipo de Documento", ["Nenhum", "CPF", "CNPJ"],
                                         index=["Nenhum", "CPF", "CNPJ"].index(
                                             tipo_documento_atual if tipo_documento_atual in ["Nenhum", "CPF", "CNPJ"] else "Nenhum"))
            
            if tipo_documento != "Nenhum":
                if tipo_documento == "CPF":
                    documento = st.text_input("CPF", value=fornecedor.get('document', ''), 
                                             placeholder="000.000.000-00")
                    if documento:
                        documento = formatar_cpf(documento)
                else:
                    documento = st.text_input("CNPJ", value=fornecedor.get('document', ''), 
                                             placeholder="00.000.000/0000-00")
                    if documento:
                        documento = formatar_cnpj(documento)
            else:
                documento = ""
        
        with col2:
            endereco = st.text_area("Endereço", value=fornecedor.get('address', ''), 
                                   placeholder="Endereço completo")
            telefone = st.text_input("Telefone", value=fornecedor.get('phone', ''), 
                                    placeholder="(00) 00000-0000")
            email = st.text_input("Email", value=fornecedor.get('email', ''), 
                                 placeholder="email@exemplo.com")
            observacoes = st.text_area("Observações", value=fornecedor.get('notes', ''), 
                                      placeholder="Informações adicionais")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submit = st.form_submit_button("Salvar Alterações", type="primary", use_container_width=True)
        
        with col_btn2:
            cancel = st.form_submit_button("Cancelar", type="secondary", use_container_width=True)
    
    if cancel:
        del st.session_state.edit_fornecedor
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    if submit:
        if not nome.strip():
            st.error("❌ Nome do fornecedor é obrigatório!")
        else:
            try:
                supplier = db.query(Supplier).filter(Supplier.id == fornecedor['id']).first()
                if supplier:
                    supplier.name = nome.strip()
                    supplier.trade_name = nome_fantasia.strip()
                    supplier.supplier_type = tipo
                    supplier.document_type = tipo_documento if tipo_documento != "Nenhum" else ""
                    supplier.document = documento.strip()
                    supplier.address = endereco.strip()
                    supplier.phone = telefone.strip()
                    supplier.email = email.strip()
                    supplier.notes = observacoes.strip()
                    
                    db.commit()
                    st.success(f"✅ Fornecedor '{nome}' atualizado com sucesso!")
                    
                    if st.button("Voltar para Fornecedores"):
                        del st.session_state.edit_fornecedor
                        st.session_state.current_page = "fornecedores"
                        st.rerun()
                else:
                    st.error("Fornecedor não encontrado no banco de dados")
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao atualizar fornecedor: {str(e)}")
            finally:
                db.close()

# --- TELA: PEDIDOS ---
@require_auth()
def mostrar_pedidos():
    st.title("🛒 Pedidos")
    
    data = carregar_dados()
    
    # Estatísticas
    pedidos_pendentes = sum(1 for p in data['pedidos'] if p.get('payment_status') != 'paid')
    pedidos_pagos = sum(1 for p in data['pedidos'] if p.get('payment_status') == 'paid')
    pedidos_entregues = sum(1 for p in data['pedidos'] if p.get('delivery_status') == 'delivered')
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    with col_stats1:
        st.metric("Total de Pedidos", len(data['pedidos']))
    with col_stats2:
        st.metric("Pagamento Pendente", pedidos_pendentes)
    with col_stats3:
        st.metric("Pagos", pedidos_pagos)
    with col_stats4:
        st.metric("Entregues", pedidos_entregues)
    
    # Botão para novo pedido
    if st.button("+ Novo Pedido", type="primary"):
        st.session_state.current_page = "novo_pedido"
        st.rerun()
    
    # Filtros
    st.subheader("Filtros")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        filtro_status = st.multiselect("Status de Pagamento", 
                                      ["Todos", "Pendente", "Pago"],
                                      default=["Todos"])
    
    with col_filtro2:
        filtro_entrega = st.multiselect("Status de Entrega",
                                       ["Todos", "Pendente", "Entregue"],
                                       default=["Todos"])
    
    with col_filtro3:
        # Filtro por cliente
        clientes_nomes = ["Todos"] + [c['name'] for c in data['clientes']]
        filtro_cliente = st.selectbox("Cliente", clientes_nomes)
    
    # Lista de pedidos
    st.subheader("Lista de Pedidos")
    
    if data['pedidos']:
        # Ordenar por data (mais recente primeiro)
        pedidos_ordenados = sorted(data['pedidos'], key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Aplicar filtros
        pedidos_filtrados = []
        for pedido in pedidos_ordenados:
            # Filtro de status de pagamento
            if "Todos" not in filtro_status:
                status_pagamento = "Pago" if pedido.get('payment_status') == 'paid' else "Pendente"
                if status_pagamento not in filtro_status:
                    continue
            
            # Filtro de status de entrega
            if "Todos" not in filtro_entrega:
                status_entrega = "Entregue" if pedido.get('delivery_status') == 'delivered' else "Pendente"
                if status_entrega not in filtro_entrega:
                    continue
            
            # Filtro por cliente
            if filtro_cliente != "Todos":
                cliente = next((c for c in data['clientes'] if c['id'] == pedido.get('customer_id')), None)
                if not cliente or cliente['name'] != filtro_cliente:
                    continue
            
            pedidos_filtrados.append(pedido)
        
        if not pedidos_filtrados:
            st.info("Nenhum pedido corresponde aos filtros selecionados.")
        else:
            for pedido in pedidos_filtrados:
                cor = get_cor_status_pedido(pedido)
                
                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 5px solid {cor}; padding-left: 10px; margin-bottom: 10px;">
                    """, unsafe_allow_html=True)
                    
                    col_info, col_status, col_acoes = st.columns([3, 2, 1])
                    
                    with col_info:
                        # Obter nome do cliente
                        cliente_nome = "Desconhecido"
                        for cliente in data['clientes']:
                            if cliente['id'] == pedido.get('customer_id'):
                                cliente_nome = cliente['name']
                                break
                        
                        st.write(f"**Pedido #{pedido.get('order_number', pedido.get('id', ''))}** - {pedido.get('created_at', '')}")
                        st.write(f"**Cliente:** {cliente_nome}")
                        st.write(f"**Total:** {formatar_moeda(pedido.get('total_amount', 0))}")
                        
                        # Mostrar produtos
                        items = pedido.get('items', [])
                        if isinstance(items, str):
                            items = json.loads(items)
                        
                        if items:
                            produtos = ", ".join([item.get('nome', item.get('name', '')) for item in items[:2]])
                            if len(items) > 2:
                                produtos += f" (+{len(items) - 2} mais)"
                            st.write(f"**Produtos:** {produtos}")
                    
                    with col_status:
                        # Status de pagamento
                        if pedido.get('payment_status') == 'paid':
                            st.write("🟢 **Pago**")
                            if pedido.get('payment_method'):
                                st.write(f"({pedido['payment_method']})")
                        else:
                            # Verificar se está atrasado
                            data_criacao = datetime.fromisoformat(pedido.get('created_at')) if pedido.get('created_at') else datetime.now()
                            if (datetime.now() - data_criacao) > timedelta(hours=24):
                                st.write("🔴 **Pagamento Atrasado**")
                            else:
                                st.write("🟡 **Pagamento Pendente**")
                        
                        # Status de entrega
                        if pedido.get('delivery_status') == 'delivered':
                            st.write("✓ **Entregue**")
                        else:
                            st.write("⏳ **Em Produção**")
                    
                    with col_acoes:
                        if st.button("Visualizar", key=f"view_pedido_main_{pedido.get('id', '')}"):
                            st.session_state.view_pedido = pedido
                            st.session_state.current_page = "view_pedido"
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.divider()
    else:
        st.info("Nenhum pedido criado ainda. Crie seu primeiro pedido!")

# --- TELA: NOVO PEDIDO ---
@require_auth()
def mostrar_novo_pedido():
    st.title("🛒 Novo Pedido")
    
    # VERIFICAR SE É UM NOVO PEDIDO (resetar estado se necessário)
    reset_pedido = False
    
    # Se veio da tela de clientes ou de pedidos, resetar
    if 'novo_pedido_cliente' in st.session_state:
        reset_pedido = True
    
    # Se está na etapa 3 (finalização) e clicou em novo pedido, resetar
    if 'pedido_etapa' in st.session_state and st.session_state.pedido_etapa == 3:
        reset_pedido = True
    
    # Resetar todos os estados do pedido se necessário
    if reset_pedido or 'pedido_etapa' not in st.session_state:
        st.session_state.pedido_etapa = 1  # Sempre começar na etapa 1
        st.session_state.pedido_cliente_selecionado = None
        st.session_state.pedido_itens_calculados = []
        st.session_state.pedido_info = {
            'tipo_entrega': 'Pronta Entrega',
            'prazo_entrega': '5 dias úteis',
            'forma_pagamento': 'Não Definido',
            'observacoes': ''
        }
        # Limpar cálculo atual se existir
        if 'calculo_atual' in st.session_state:
            del st.session_state.calculo_atual
    
    # Carregar dados do banco de dados
    data = carregar_dados()
    
    # Se veio da tela de clientes, configurar cliente pré-selecionado
    if 'novo_pedido_cliente' in st.session_state and st.session_state.pedido_etapa == 1:
        cliente_pre = st.session_state.novo_pedido_cliente
        st.session_state.pedido_cliente_selecionado = cliente_pre
    
    # ETAPA 1: SELEÇÃO DO CLIENTE
    if st.session_state.pedido_etapa == 1:
        st.subheader("1️⃣ Seleção do Cliente")
        
        # Seleção de cliente
        clientes_options = [c['name'] for c in data['clientes']]
        
        # Determinar cliente inicialmente selecionado
        index = 0
        cliente_selecionado_nome = ""
        
        if st.session_state.pedido_cliente_selecionado:
            # Usar cliente já selecionado (se houver)
            cliente_selecionado_nome = st.session_state.pedido_cliente_selecionado['name']
            if cliente_selecionado_nome in clientes_options:
                index = clientes_options.index(cliente_selecionado_nome)
        elif 'novo_pedido_cliente' in st.session_state:
            # Usar cliente que veio da tela de clientes
            cliente_pre_selecionado = st.session_state.novo_pedido_cliente['name']
            if cliente_pre_selecionado in clientes_options:
                index = clientes_options.index(cliente_pre_selecionado)
                cliente_selecionado_nome = cliente_pre_selecionado
        
        cliente_selecionado = st.selectbox(
            "Selecione o cliente *", 
            clientes_options,
            index=index,
            key="cliente_selecionado_pedido"
        )
        
        # Obter cliente selecionado
        cliente_atual = None
        for c in data['clientes']:
            if c['name'] == cliente_selecionado:
                cliente_atual = c
                break
        
        # Atualizar cliente selecionado no session state
        st.session_state.pedido_cliente_selecionado = cliente_atual
        
        # Mostrar informações do cliente
        if cliente_atual:
            st.success(f"✅ Cliente selecionado: **{cliente_atual['name']}**")
            
            with st.container(border=True):
                col_info1, col_info2 = st.columns(2)
                with col_info1:
                    st.write(f"**📋 Documento:** {cliente_atual.get('document', 'N/A')}")
                    st.write(f"**📍 Endereço:** {cliente_atual.get('address', 'N/A')}")
                with col_info2:
                    st.write(f"**📞 Telefone:** {cliente_atual.get('phone', 'N/A')}")
                    st.write(f"**📧 Email:** {cliente_atual.get('email', 'N/A')}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            if st.button("← Cancelar", type="secondary", use_container_width=True):
                # Limpar dados temporários
                if 'novo_pedido_cliente' in st.session_state:
                    del st.session_state.novo_pedido_cliente
                st.session_state.current_page = "pedidos"
                st.rerun()
        
        with col_btn2:
            if cliente_atual:
                if st.button("🔄 Limpar Seleção", type="secondary", use_container_width=True):
                    st.session_state.pedido_cliente_selecionado = None
                    st.rerun()
        
        with col_btn3:
            if cliente_atual and st.button("👉 Avançar", type="primary", use_container_width=True):
                # Remover indicador de novo pedido vindo de clientes
                if 'novo_pedido_cliente' in st.session_state:
                    del st.session_state.novo_pedido_cliente
                st.session_state.pedido_etapa = 2
                st.rerun()
   
    # ETAPA 2: CONFIGURAÇÃO DO PEDIDO
    elif st.session_state.pedido_etapa == 2:
        cliente = st.session_state.pedido_cliente_selecionado
        
        if not cliente:
            st.error("❌ Nenhum cliente selecionado!")
            st.session_state.pedido_etapa = 1
            st.rerun()
        
        st.subheader(f"2️⃣ Configurar Pedido para {cliente['name']}")
        
        # Informações do cliente (fixas)
        with st.container(border=True):
            col_cliente1, col_cliente2 = st.columns(2)
            with col_cliente1:
                st.write(f"**👤 Cliente:** {cliente['name']}")
                st.write(f"**📋 Documento:** {cliente.get('document', 'N/A')}")
            with col_cliente2:
                st.write(f"**📍 Endereço:** {cliente.get('address', 'N/A')}")
                st.write(f"**📞 Telefone:** {cliente.get('phone', 'N/A')}")
        
        st.divider()
        
        # CONFIGURAR PRODUTOS (simulando calculadora)
        st.subheader("➕ Adicionar Produtos ao Pedido")
        
        col_prod1, col_prod2 = st.columns([2, 1])
        
        with col_prod1:
            # Seleção de produto
            product_names = [p['nome'] for p in data['produtos']]
            if not product_names:
                product_names = ["Nenhum produto disponível"]
            
            produto_selecionado = st.selectbox("Produto", product_names, key="produto_pedido_calc")
            
            # Obter produto selecionado
            produto_atual = None
            for p in data['produtos']:
                if p['nome'] == produto_selecionado:
                    produto_atual = p
                    break
            
            if produto_atual:
                # Toggle DTF
                col_toggle1, col_toggle2 = st.columns(2)
                with col_toggle1:
                    usa_dtf = st.toggle("DTF", value=produto_atual.get('usa_dtf', True), key="usa_dtf_pedido")
                
                with col_toggle2:
                    incluir_custos_fixos = st.toggle("Incluir Custos Fixos", value=True, key="custos_fixos_pedido")
                
                # Dimensões (somente se usa_dtf for True)
                if usa_dtf:
                    st.subheader("📏 Dimensões da Estampa (cm)")
                    dim_cols = st.columns(4)
                    with dim_cols[0]:
                        frente_altura = st.number_input("Altura Frente", min_value=0.0, value=10.0, step=0.5, key="frente_altura_pedido")
                    with dim_cols[1]:
                        frente_largura = st.number_input("Largura Frente", min_value=0.0, value=10.0, step=0.5, key="frente_largura_pedido")
                    with dim_cols[2]:
                        costas_altura = st.number_input("Altura Costas", min_value=0.0, value=0.0, step=0.5, key="costas_altura_pedido")
                    with dim_cols[3]:
                        costas_largura = st.number_input("Largura Costas", min_value=0.0, value=0.0, step=0.5, key="costas_largura_pedido")
                else:
                    frente_altura = frente_largura = costas_altura = costas_largura = 0.0
                
                # Quantidade e Margem
                qtd_cols = st.columns(2)
                with qtd_cols[0]:
                    quantidade = st.number_input("Quantidade", min_value=1, value=1, key="quantidade_pedido")
                with qtd_cols[1]:
                    margem = st.number_input("Margem %", min_value=0.0, value=data['config'].get('default_margin', 50.0), step=1.0, key="margem_pedido")
        
        with col_prod2:
            st.subheader("📊 Resultado")
            
            if produto_atual and st.button("Calcular Preço", type="primary", use_container_width=True, key="calcular_preco_pedido"):
                # Cálculo da área
                area_frente = frente_altura * frente_largura
                area_costas = costas_altura * costas_largura
                area_total = area_frente + area_costas
                
                # Cálculo DTF
                custo_dtf = 0
                if usa_dtf and area_total > 0:
                    preco_metro = data['config'].get('dtf_price_per_meter', 80.0)
                    largura_rolo = data['config'].get('roll_width', 58.0)
                    altura_rolo = data['config'].get('roll_height', 100)
                    area_metro_linear = largura_rolo * altura_rolo
                    custo_cm2 = preco_metro / area_metro_linear
                    custo_dtf = area_total * custo_cm2
                
                # Custos fixos
                custos_fixos = 0
                if incluir_custos_fixos:
                    custos_fixos = (produto_atual.get('energy_cost', produto_atual.get('energia', 0)) + 
                                   produto_atual.get('transport_cost', produto_atual.get('transp', 0)) + 
                                   produto_atual.get('packaging_cost', produto_atual.get('emb', 0)))
                    
                    # Adicionar custos fixos globais
                    custos_fixos += (data['config'].get('energy_cost_value', 1.0) + 
                                    data['config'].get('transport_cost_value', 2.0) + 
                                    data['config'].get('packaging_cost_value', 1.0))
                
                # Cálculo final
                custo_unitario = produto_atual.get('custo', produto_atual.get('cost', 0)) + custo_dtf + custos_fixos
                preco_unitario = custo_unitario * (1 + margem / 100)
                preco_total = preco_unitario * quantidade
                
                # Armazenar cálculo
                st.session_state.calculo_atual = {
                    'produto': produto_atual['nome'],
                    'preco_unitario': preco_unitario,
                    'quantidade': quantidade,
                    'preco_total': preco_total,
                    'area_total': area_total,
                    'usa_dtf': usa_dtf,
                    'dimensoes': {
                        'frente_altura': frente_altura,
                        'frente_largura': frente_largura,
                        'costas_altura': costas_altura,
                        'costas_largura': costas_largura
                    }
                }
                st.success(f"Preço calculado: {formatar_moeda(preco_total)}")
            
            # Mostrar cálculo atual
            if 'calculo_atual' in st.session_state:
                calc = st.session_state.calculo_atual
                
                st.metric("Preço Total", formatar_moeda(calc['preco_total']))
                st.write(f"**Produto:** {calc['produto']}")
                st.write(f"**Preço Unitário:** {formatar_moeda(calc['preco_unitario'])}")
                st.write(f"**Quantidade:** {calc['quantidade']}")
                if calc['usa_dtf']:
                    st.write(f"**Área Total:** {calc['area_total']:.2f} cm²")
                
                # Botão para adicionar ao pedido
                if st.button("➕ Adicionar ao Pedido", type="primary", use_container_width=True, key="adicionar_calculo_pedido"):
                    novo_item = {
                        'nome': calc['produto'],
                        'preco_unitario': calc['preco_unitario'],
                        'quantidade': calc['quantidade'],
                        'preco_total': calc['preco_total'],
                        'detalhes': {
                            'usa_dtf': calc['usa_dtf'],
                            'area_total': calc['area_total'],
                            'dimensoes': calc['dimensoes']
                        }
                    }
                    
                    # Verificar se item já existe
                    item_existente = None
                    for i, item in enumerate(st.session_state.pedido_itens_calculados):
                        if item['nome'] == novo_item['nome'] and item['preco_unitario'] == novo_item['preco_unitario']:
                            item_existente = i
                            break
                    
                    if item_existente is not None:
                        # Atualizar quantidade
                        st.session_state.pedido_itens_calculados[item_existente]['quantidade'] += novo_item['quantidade']
                        st.session_state.pedido_itens_calculados[item_existente]['preco_total'] += novo_item['preco_total']
                        st.success(f"Quantidade do item '{novo_item['nome']}' atualizada!")
                    else:
                        st.session_state.pedido_itens_calculados.append(novo_item)
                        st.success(f"Item '{novo_item['nome']}' adicionado ao pedido!")
                    
                    st.rerun()
        
        # LISTA DE ITENS NO PEDIDO
        st.divider()
        st.subheader("📋 Itens no Pedido")
        
        if st.session_state.pedido_itens_calculados:
            total_geral = 0
            
            for i, item in enumerate(st.session_state.pedido_itens_calculados):
                with st.container(border=True):
                    col_item1, col_item2, col_item3 = st.columns([3, 1, 1])
                    
                    with col_item1:
                        st.write(f"**{item['nome']}**")
                        if item['detalhes']['usa_dtf']:
                            st.write(f"Área: {item['detalhes']['area_total']:.2f} cm²")
                    
                    with col_item2:
                        st.write(f"Qtd: {item['quantidade']}")
                        st.write(f"Unit: {formatar_moeda(item['preco_unitario'])}")
                    
                    with col_item3:
                        st.write(f"**Total:** {formatar_moeda(item['preco_total'])}")
                        total_geral += item['preco_total']
                        
                        if st.button("🗑️", key=f"remover_item_{i}", help="Remover item"):
                            st.session_state.pedido_itens_calculados.pop(i)
                            st.rerun()
            
            st.metric("💰 Total do Pedido", formatar_moeda(total_geral))
        else:
            st.info("Nenhum item adicionado ao pedido ainda. Calcule e adicione produtos acima.")
        
        # CONFIGURAÇÕES ADICIONAIS
        st.divider()
        st.subheader("⚙️ Configurações do Pedido")
        
        col_config1, col_config2 = st.columns(2)
        with col_config1:
            st.session_state.pedido_info['tipo_entrega'] = st.radio(
                "Tipo de Entrega", 
                ["Pronta Entrega", "Sob Encomenda"],
                index=0 if st.session_state.pedido_info['tipo_entrega'] == 'Pronta Entrega' else 1
            )
            st.session_state.pedido_info['prazo_entrega'] = st.text_input(
                "Prazo de Entrega", 
                value=st.session_state.pedido_info['prazo_entrega']
            )
        
        with col_config2:
            st.session_state.pedido_info['forma_pagamento'] = st.selectbox(
                "Forma de Pagamento", 
                ["Não Definido", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Transferência Bancária"],
                index=["Não Definido", "Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Transferência Bancária"].index(
                    st.session_state.pedido_info['forma_pagamento']
                )
            )
            st.session_state.pedido_info['observacoes'] = st.text_area(
                "Observações", 
                value=st.session_state.pedido_info['observacoes'],
                placeholder="Informações adicionais sobre o pedido..."
            )
        
        # BOTÕES DE NAVEGAÇÃO
        st.divider()
        col_nav1, col_nav2, col_nav3, col_nav4 = st.columns(4)
        
        with col_nav1:
            if st.button("← Voltar", type="secondary", use_container_width=True):
                st.session_state.pedido_etapa = 1
                st.rerun()
        
        with col_nav2:
            if st.button("💾 Salvar", type="secondary", use_container_width=True, 
                        disabled=len(st.session_state.pedido_itens_calculados) == 0):
                # Salvar pedido como rascunho (sem status de pagamento/entrega)
                db = SessionLocal()
                try:
                    current_user = get_current_user()
                    user = db.query(User).filter(User.id == current_user['id']).first()
                    
                    customer = db.query(Customer).filter(Customer.id == cliente['id']).first()
                    
                    # Gerar número do pedido
                    ultimo_numero = db.query(Order).count() + 1
                    
                    # Preparar itens para salvar
                    itens_para_salvar = []
                    for item in st.session_state.pedido_itens_calculados:
                        itens_para_salvar.append({
                            "nome": item['nome'],
                            "quantidade": item['quantidade'],
                            "valor_unitario": item['preco_unitario']
                        })
                    
                    novo_pedido = Order(
                        order_number=str(ultimo_numero).zfill(4),
                        customer=customer,
                        user=user,
                        total_amount=sum(item['preco_total'] for item in st.session_state.pedido_itens_calculados),
                        items=json.dumps(itens_para_salvar),
                        delivery_type=st.session_state.pedido_info['tipo_entrega'],
                        delivery_deadline=st.session_state.pedido_info['prazo_entrega'],
                        payment_method=st.session_state.pedido_info['forma_pagamento'] if st.session_state.pedido_info['forma_pagamento'] != "Não Definido" else "",
                        payment_status='pending',
                        delivery_status='production',
                        notes=st.session_state.pedido_info['observacoes'].strip()
                    )
                    
                    db.add(novo_pedido)
                    db.commit()
                    
                    st.success(f"✅ Pedido #{ultimo_numero} salvo como rascunho!")
                    
                    # Limpar dados temporários, mas manter na mesma etapa
                    if 'calculo_atual' in st.session_state:
                        del st.session_state.calculo_atual
                    
                    st.rerun()
                    
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao salvar pedido: {str(e)}")
                finally:
                    db.close()
        
        with col_nav3:
            if st.button("❌ Cancelar", type="secondary", use_container_width=True):
                # Limpar todos os dados do pedido
                st.session_state.pedido_etapa = 1
                st.session_state.pedido_cliente_selecionado = None
                st.session_state.pedido_itens_calculados = []
                st.session_state.pedido_info = {
                    'tipo_entrega': 'Pronta Entrega',
                    'prazo_entrega': '5 dias úteis',
                    'forma_pagamento': 'Não Definido',
                    'observacoes': ''
                }
                if 'calculo_atual' in st.session_state:
                    del st.session_state.calculo_atual
                
                st.success("Pedido cancelado!")
                st.rerun()
        
        with col_nav4:
            if len(st.session_state.pedido_itens_calculados) > 0:
                if st.button("✅ Finalizar", type="primary", use_container_width=True):
                    st.session_state.pedido_etapa = 3
                    st.rerun()
            else:
                st.button("✅ Finalizar", type="primary", use_container_width=True, disabled=True)
    
    # ETAPA 3: FINALIZAÇÃO
    elif st.session_state.pedido_etapa == 3:
        cliente = st.session_state.pedido_cliente_selecionado
        
        st.subheader(f"3️⃣ Finalizar Pedido para {cliente['name']}")
        
        # RESUMO DO PEDIDO
        with st.container(border=True):
            st.write("### 📋 Resumo do Pedido")
            
            # Informações do cliente
            st.write("**👤 Cliente:**")
            col_cli1, col_cli2 = st.columns(2)
            with col_cli1:
                st.write(f"- **Nome:** {cliente['name']}")
                st.write(f"- **Documento:** {cliente.get('document', 'N/A')}")
            with col_cli2:
                st.write(f"- **Endereço:** {cliente.get('address', 'N/A')}")
                st.write(f"- **Telefone:** {cliente.get('phone', 'N/A')}")
            
            st.divider()
            
            # Itens do pedido
            st.write("**🛒 Itens do Pedido:**")
            total_geral = 0
            
            for i, item in enumerate(st.session_state.pedido_itens_calculados):
                with st.container():
                    col_res1, col_res2, col_res3 = st.columns([3, 1, 2])
                    
                    with col_res1:
                        st.write(f"**{item['nome']}**")
                        if item['detalhes']['usa_dtf']:
                            st.write(f"Área: {item['detalhes']['area_total']:.2f} cm²")
                    
                    with col_res2:
                        st.write(f"Qtd: {item['quantidade']}")
                        st.write(f"Unit: {formatar_moeda(item['preco_unitario'])}")
                    
                    with col_res3:
                        item_total = item['preco_total']
                        st.write(f"**Total:** {formatar_moeda(item_total)}")
                        total_geral += item_total
            
            st.divider()
            
            # Configurações do pedido
            st.write("**⚙️ Configurações:**")
            col_conf1, col_conf2 = st.columns(2)
            with col_conf1:
                st.write(f"- **Tipo de Entrega:** {st.session_state.pedido_info['tipo_entrega']}")
                st.write(f"- **Prazo de Entrega:** {st.session_state.pedido_info['prazo_entrega']}")
            with col_conf2:
                st.write(f"- **Forma de Pagamento:** {st.session_state.pedido_info['forma_pagamento']}")
                if st.session_state.pedido_info['observacoes']:
                    st.write(f"- **Observações:** {st.session_state.pedido_info['observacoes']}")
            
            st.divider()
            
            # Total final
            st.metric("💰 **TOTAL DO PEDIDO**", formatar_moeda(total_geral))
        
        # BOTÕES FINAIS
        st.divider()
        col_final1, col_final2, col_final3 = st.columns(3)
        
        with col_final1:
            if st.button("← Voltar", type="secondary", use_container_width=True):
                st.session_state.pedido_etapa = 2
                st.rerun()
        
        with col_final2:
            if st.button("💾 Salvar Pedido", type="secondary", use_container_width=True):
                # Salvar pedido como rascunho (igual à etapa 2)
                db = SessionLocal()
                try:
                    current_user = get_current_user()
                    user = db.query(User).filter(User.id == current_user['id']).first()
                    
                    customer = db.query(Customer).filter(Customer.id == cliente['id']).first()
                    
                    ultimo_numero = db.query(Order).count() + 1
                    
                    itens_para_salvar = []
                    for item in st.session_state.pedido_itens_calculados:
                        itens_para_salvar.append({
                            "nome": item['nome'],
                            "quantidade": item['quantidade'],
                            "valor_unitario": item['preco_unitario']
                        })
                    
                    novo_pedido = Order(
                        order_number=str(ultimo_numero).zfill(4),
                        customer=customer,
                        user=user,
                        total_amount=total_geral,
                        items=json.dumps(itens_para_salvar),
                        delivery_type=st.session_state.pedido_info['tipo_entrega'],
                        delivery_deadline=st.session_state.pedido_info['prazo_entrega'],
                        payment_method=st.session_state.pedido_info['forma_pagamento'] if st.session_state.pedido_info['forma_pagamento'] != "Não Definido" else "",
                        payment_status='pending',
                        delivery_status='production',
                        notes=st.session_state.pedido_info['observacoes'].strip()
                    )
                    
                    db.add(novo_pedido)
                    db.commit()
                    
                    st.success(f"✅ Pedido #{ultimo_numero} salvo como rascunho!")
                    
                    # Limpar e voltar à lista
                    st.session_state.current_page = "pedidos"
                    st.rerun()
                    
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao salvar pedido: {str(e)}")
                finally:
                    db.close()
        
        with col_final3:
            if st.button("✅ Finalizar Pedido", type="primary", use_container_width=True):
                # Salvar pedido como finalizado
                db = SessionLocal()
                try:
                    current_user = get_current_user()
                    user = db.query(User).filter(User.id == current_user['id']).first()
                    
                    customer = db.query(Customer).filter(Customer.id == cliente['id']).first()
                    
                    ultimo_numero = db.query(Order).count() + 1
                    
                    itens_para_salvar = []
                    for item in st.session_state.pedido_itens_calculados:
                        itens_para_salvar.append({
                            "nome": item['nome'],
                            "quantidade": item['quantidade'],
                            "valor_unitario": item['preco_unitario']
                        })
                    
                    novo_pedido = Order(
                        order_number=str(ultimo_numero).zfill(4),
                        customer=customer,
                        user=user,
                        total_amount=total_geral,
                        items=json.dumps(itens_para_salvar),
                        delivery_type=st.session_state.pedido_info['tipo_entrega'],
                        delivery_deadline=st.session_state.pedido_info['prazo_entrega'],
                        payment_method=st.session_state.pedido_info['forma_pagamento'] if st.session_state.pedido_info['forma_pagamento'] != "Não Definido" else "",
                        payment_status='pending',  # Inicia como pendente
                        delivery_status='production',
                        notes=st.session_state.pedido_info['observacoes'].strip()
                    )
                    
                    db.add(novo_pedido)
                    db.commit()
                    
                    st.success(f"✅ Pedido #{ultimo_numero} finalizado com sucesso!")
                    
                    # Gerar nota fiscal
                    pdf_path = gerar_nota_fiscal(novo_pedido.to_dict(), cliente)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="📄 Baixar Nota Fiscal",
                            data=pdf_bytes,
                            file_name=f"Nota_Pedido_{ultimo_numero}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                    
                    # Limpar todos os dados
                    st.session_state.pedido_etapa = 1
                    st.session_state.pedido_cliente_selecionado = None
                    st.session_state.pedido_itens_calculados = []
                    st.session_state.pedido_info = {
                        'tipo_entrega': 'Pronta Entrega',
                        'prazo_entrega': '5 dias úteis',
                        'forma_pagamento': 'Não Definido',
                        'observacoes': ''
                    }
                    if 'calculo_atual' in st.session_state:
                        del st.session_state.calculo_atual
                    if 'novo_pedido_cliente' in st.session_state:
                        del st.session_state.novo_pedido_cliente
                    
                    # Opção para continuar
                    if st.button("Ir para Lista de Pedidos"):
                        st.session_state.current_page = "pedidos"
                        st.rerun()
                    
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao finalizar pedido: {str(e)}")
                finally:
                    db.close()

# --- TELA: VER PEDIDO ---

@require_auth()
def mostrar_ver_pedido():
    if 'view_pedido' not in st.session_state:
        st.session_state.current_page = "pedidos"
        st.rerun()
    
    pedido = st.session_state.view_pedido
    data = carregar_dados()
    
    # Obter cliente
    cliente = next((c for c in data['clientes'] if c['id'] == pedido.get('customer_id')), None)
    
    st.title(f"🛒 Pedido #{pedido.get('order_number', pedido.get('id', ''))}")
    
    # Informações principais
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write(f"**Cliente:** {cliente['name'] if cliente else 'Desconhecido'}")
        st.write(f"**Data de Criação:** {pedido.get('created_at', '')}")
        st.write(f"**Tipo de Entrega:** {pedido.get('delivery_type', '')}")
        st.write(f"**Prazo de Entrega:** {pedido.get('delivery_deadline', '')}")
    
    with col_info2:
        st.write(f"**Forma de Pagamento:** {pedido.get('payment_method', 'Não definido')}")
        if pedido.get('paid_at'):
            st.write(f"**Data de Pagamento:** {pedido.get('paid_at')}")
        if pedido.get('delivered_at'):
            st.write(f"**Data de Entrega:** {pedido.get('delivered_at')}")
    
    # Status
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        if pedido.get('payment_status') == 'paid':
            st.success("✅ **PAGO**")
        else:
            st.error("❌ **PAGAMENTO PENDENTE**")
    
    with col_status2:
        if pedido.get('delivery_status') == 'delivered':
            st.success("✅ **ENTREGUE**")
        else:
            st.warning("⏳ **EM PRODUÇÃO**")
    
    # Itens
    st.subheader("Itens")
    items = pedido.get('items', [])
    if isinstance(items, str):
        items = json.loads(items)
    
    if items:
        itens_data = []
        for item in items:
            itens_data.append({
                "Produto": item.get('nome', item.get('name', 'Sem nome')),
                "Quantidade": item.get('quantidade', item.get('quantity', 0)),
                "Valor Unitário": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0))),
                "Total": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0)) * item.get('quantidade', item.get('quantity', 1)))
            })
        
        df = pd.DataFrame(itens_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Total
    st.metric("Valor Total", formatar_moeda(pedido.get('total_amount', 0)))
    
    # Observações
    if pedido.get('notes'):
        st.subheader("Observações")
        st.write(pedido['notes'])
    
    # Controles de status
    st.subheader("Atualizar Status")
    
    col_status_btn1, col_status_btn2, col_status_btn3 = st.columns(3)
    
    with col_status_btn1:
        if pedido.get('payment_status') != 'paid':
            if st.button("Marcar como Pago", type="primary", use_container_width=True, key="marcar_pago"):
                # Mostrar opções de pagamento
                st.session_state.pagar_pedido = pedido
                st.rerun()
        else:
            st.info("✅ Pedido já está pago")
    
    with col_status_btn2:
        if pedido.get('delivery_status') != 'delivered':
            if st.button("Marcar como Entregue", type="primary", use_container_width=True, key="marcar_entregue"):
                db = SessionLocal()
                try:
                    order = db.query(Order).filter(Order.id == pedido['id']).first()
                    if order:
                        order.delivery_status = 'delivered'
                        order.delivered_at = datetime.now()
                        db.commit()
                        st.success("✅ Pedido marcado como entregue!")
                        # Atualizar o pedido na session_state
                        st.session_state.view_pedido = order.to_dict()
                        # Forçar recarregamento imediato
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro: {str(e)}")
                finally:
                    db.close()
        else:
            st.info("✅ Pedido já está entregue")
    
    with col_status_btn3:
        if st.button("Gerar Nota Fiscal", type="secondary", use_container_width=True, key="gerar_nota"):
            # Gerar PDF do pedido
            pdf_path = gerar_nota_fiscal(pedido, cliente)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="📄 Baixar Nota Fiscal",
                    data=pdf_bytes,
                    file_name=f"Nota_Pedido_{pedido.get('order_number', pedido.get('id', ''))}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
    
    # Seção para marcar como pago
    if st.session_state.get('pagar_pedido') == pedido:
        st.subheader("Confirmar Pagamento")
        
        forma_pagamento = st.selectbox("Forma de Pagamento", 
                                      ["Dinheiro", "Cartão de Crédito", "Cartão de Débito", "PIX", "Transferência Bancária"])
        
        col_confirm1, col_confirm2 = st.columns(2)
        
        with col_confirm1:
            if st.button("Confirmar Pagamento", type="primary", use_container_width=True, key="confirmar_pagamento"):
                db = SessionLocal()
                try:
                    order = db.query(Order).filter(Order.id == pedido['id']).first()
                    if order:
                        order.payment_status = 'paid'
                        order.payment_method = forma_pagamento
                        order.paid_at = datetime.now()
                        db.commit()
                        # Atualizar session_state
                        st.session_state.view_pedido = order.to_dict()
                        del st.session_state.pagar_pedido
                        st.success("✅ Pagamento confirmado!")
                        st.rerun()
                finally:
                    db.close()
        
        with col_confirm2:
            if st.button("Cancelar", type="secondary", use_container_width=True, key="cancelar_pagamento"):
                del st.session_state.pagar_pedido
                st.rerun()
    
    # Botão para voltar
    if st.button("← Voltar para Lista de Pedidos", type="secondary", use_container_width=True):
        if 'pagar_pedido' in st.session_state:
            del st.session_state.pagar_pedido
        st.session_state.current_page = "pedidos"
        st.rerun()

# --- TELA: CONFIGURAÇÕES ---
@require_auth()
def mostrar_configuracoes():
    st.title("⚙️ Configurações")
    
    if not is_admin():
        st.error("⚠️ Você precisa de privilégios de administrador para acessar as configurações.")
        return
    
    data = carregar_dados()
    db = SessionLocal()
    
    try:
        # Custos DTF
        st.subheader("Custos DTF")
        col_dtf1, col_dtf2, col_dtf3 = st.columns(3)
        
        with col_dtf1:
            preco_metro = st.number_input("Preço por Metro (R$)", 
                                        value=data['config'].get('dtf_price_per_meter', 80.0), 
                                        min_value=0.0, step=0.1, key="preco_metro")
        
        with col_dtf2:
            largura_rolo = st.number_input("Largura do Rolo (cm)", 
                                         value=data['config'].get('roll_width', 58.0), 
                                         min_value=0.0, step=0.1, key="largura_rolo")
        
        with col_dtf3:
            altura_rolo = st.number_input("Altura do Rolo (cm)", 
                                        value=data['config'].get('roll_height', 100), 
                                        min_value=0.0, step=0.1, key="altura_rolo")
        
        # Rótulos Personalizados e Custos Fixos
        st.subheader("Rótulos Personalizados e Custos Fixos")
        
        col_label1, col_label2, col_label3 = st.columns(3)
        
        with col_label1:
            st.write("**Energia**")
            label_energia = st.text_input("Rótulo", value=data['config'].get('energy_cost_label', 'Energia (R$)'), key="label_energia")
            valor_energia = st.number_input("Valor (R$)", value=data['config'].get('energy_cost_value', 1.0), 
                                           min_value=0.0, step=0.1, key="val_energia")
        
        with col_label2:
            st.write("**Transporte**")
            label_transporte = st.text_input("Rótulo", value=data['config'].get('transport_cost_label', 'Transporte (R$)'), key="label_transporte")
            valor_transporte = st.number_input("Valor (R$)", value=data['config'].get('transport_cost_value', 2.0), 
                                              min_value=0.0, step=0.1, key="val_transporte")
        
        with col_label3:
            st.write("**Embalagem**")
            label_embalagem = st.text_input("Rótulo", value=data['config'].get('packaging_cost_label', 'Embalagem (R$)'), key="label_embalagem")
            valor_embalagem = st.number_input("Valor (R$)", value=data['config'].get('packaging_cost_value', 1.0), 
                                             min_value=0.0, step=0.1, key="val_embalagem")
        
        # Configurações Gerais
        st.subheader("Configurações Gerais")
        col_gen1, col_gen2 = st.columns(2)
        
        with col_gen1:
            default_margin = st.number_input("Margem Padrão %", 
                                           value=data['config'].get('default_margin', 50.0), 
                                           min_value=0.0, step=1.0, key="default_margin")
        
        with col_gen2:
            default_production_days = st.number_input("Dias Padrão de Produção", 
                                                    value=data['config'].get('default_production_days', 5), 
                                                    min_value=1, step=1, key="default_production_days")
        
        # Botão salvar
        if st.button("Salvar Todas as Configurações", type="primary", use_container_width=True):
            try:
                # Atualizar ou criar configurações
                configs_to_update = {
                    'dtf_price_per_meter': preco_metro,
                    'roll_width': largura_rolo,
                    'roll_height': altura_rolo,
                    'energy_cost_label': label_energia,
                    'transport_cost_label': label_transporte,
                    'packaging_cost_label': label_embalagem,
                    'energy_cost_value': valor_energia,
                    'transport_cost_value': valor_transporte,
                    'packaging_cost_value': valor_embalagem,
                    'default_margin': default_margin,
                    'default_production_days': default_production_days
                }
                
                for key, value in configs_to_update.items():
                    config_item = db.query(SystemConfig).filter(SystemConfig.key == key).first()
                    if config_item:
                        config_item.value = str(value)
                        if key in ['dtf_price_per_meter', 'roll_width', 'roll_height', 'energy_cost_value', 
                                  'transport_cost_value', 'packaging_cost_value', 'default_margin']:
                            config_item.value_type = 'number'
                        else:
                            config_item.value_type = 'string'
                    else:
                        value_type = 'number' if isinstance(value, (int, float)) else 'string'
                        category = 'dtf' if 'dtf' in key or 'roll' in key else \
                                  'labels' if 'label' in key else \
                                  'fixed_costs' if 'value' in key else \
                                  'pricing' if 'margin' in key else 'general'
                        
                        config_item = SystemConfig(
                            key=key,
                            value=str(value),
                            value_type=value_type,
                            category=category,
                            description=f"Gerado automaticamente da página de configurações"
                        )
                        db.add(config_item)
                
                db.commit()
                st.success("Configurações salvas com sucesso!")
                
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar configurações: {str(e)}")
    finally:
        db.close()

# --- TELA: MINHA CONTA ---
@require_auth()
def mostrar_minha_conta():
    st.title("👤 Minha Conta")
    
    current_user = get_current_user()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Informações do Perfil")
        
        with st.form("profile_form"):
            username = st.text_input("Nome de Usuário", value=current_user['username'], disabled=True)
            email = st.text_input("Email", value=current_user['email'])
            full_name = st.text_input("Nome Completo", value=current_user.get('full_name', ''))
            
            if st.form_submit_button("Atualizar Perfil", type="primary"):
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == current_user['id']).first()
                    if user:
                        if validate_email(email):
                            user.email = email.strip()
                        user.full_name = full_name.strip()
                        db.commit()
                        st.session_state.current_user = user.to_dict()
                        st.success("Perfil atualizado com sucesso!")
                    else:
                        st.error("Usuário não encontrado")
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao atualizar perfil: {str(e)}")
                finally:
                    db.close()
    
    with col2:
        st.subheader("Status da Conta")
        st.write(f"**Função:** {'Administrador' if current_user.get('is_admin') else 'Usuário'}")
        st.write(f"**Status:** {'Ativo' if current_user.get('is_active') else 'Inativo'}")
        st.write(f"**Membro desde:** {current_user.get('created_at', 'N/A')}")
    
    st.divider()
    
    # Alteração de senha
    st.subheader("Alterar Senha")
    
    with st.form("password_form"):
        current_password = st.text_input("Senha Atual", type="password")
        new_password = st.text_input("Nova Senha", type="password")
        confirm_password = st.text_input("Confirmar Nova Senha", type="password")
        
        if st.form_submit_button("Alterar Senha", type="secondary"):
            if not current_password or not new_password or not confirm_password:
                st.warning("Preencha todos os campos de senha")
            elif new_password != confirm_password:
                st.error("As novas senhas não coincidem")
            elif len(new_password) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres")
            else:
                success, message = auth_system.update_user_password(
                    current_user['id'], current_password, new_password
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

# --- APP PRINCIPAL ---
def main():
    # Configuração da página
    st.set_page_config(
        page_title="DTF Pricing Calculator",
        page_icon="🖨️",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': 'https://sejacapricho.com.br',
            'Report a bug': 'mailto:contato@sejacapricho.com.br',
            'About': '''
            ## DTF Pricing Calculator v2.0
            
            Sistema completo de gerenciamento para DTF e estamparia.
            
            **Desenvolvido para:** Seja Capricho
            **Contato:** (75) 9155-5968
            **Website:** sejacapricho.com.br
            '''
        }
    )
    
    # Verificar autenticação
    if 'auth_token' not in st.session_state or 'current_user' not in st.session_state:
        show_login_register_page()
        st.stop()
    
    # Obter usuário atual
    current_user = get_current_user()
    
    # Sidebar com menu
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 20px;'>
            <h1 style='color: {COR_ROXA};'>🖨️ DTF PRICING</h1>
            <p style='color: {COR_CINZA}; font-size: 0.8em;'>Sistema Completo de Gerenciamento</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Informações do usuário
        with st.container():
            st.write(f"👤 **{current_user['full_name'] or current_user['username']}**")
            st.write(f"📧 {current_user['email']}")
            if current_user.get('is_admin'):
                st.write("👑 **Administrador**")
            
            if st.button("🚪 Sair", use_container_width=True, type="secondary"):
                auth_system.logout_user()
                st.rerun()
        
        st.divider()
        
        # Menu de navegação
        menu_options = {
            "📱 Calculadora": "calculator",
            "📦 Produtos": "products",
            "👥 Clientes": "clientes",
            "🏭 Fornecedores": "fornecedores",
            "🛒 Pedidos": "pedidos",
            "📋 Orçamentos": "orcamentos",
            "⚙️ Configurações": "settings",
            "👤 Minha Conta": "account"
        }
        
        # Verificar se é admin para mostrar configurações
        if not current_user.get('is_admin'):
            menu_options.pop("⚙️ Configurações", None)
        
        for label, page in menu_options.items():
            if st.button(label, 
                        use_container_width=True,
                        type="primary" if st.session_state.get('current_page') == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()
        
        st.divider()
        
        # Dashboard rápido (pendências)
        data = carregar_dados()
        
        # Contar pedidos pendentes
        pedidos_pendentes = []
        pedidos_producao = []
        for pedido in data['pedidos']:
            if pedido.get('payment_status') != 'paid':
                created_at = pedido.get('created_at')
                if created_at:
                    try:
                        data_criacao = datetime.fromisoformat(created_at)
                        if (datetime.now() - data_criacao) > timedelta(hours=24):
                            pedidos_pendentes.append(pedido)
                    except:
                        pass
            
            # Pedidos pagos mas não entregues
            if pedido.get('payment_status') == 'paid' and pedido.get('delivery_status') != 'delivered':
                pedidos_producao.append(pedido)
        
        if pedidos_pendentes or pedidos_producao:
            st.subheader("📊 Dashboard Rápido")
            
            if pedidos_pendentes:
                st.error(f"⚠️ {len(pedidos_pendentes)} pedidos atrasados!")
                with st.expander("Ver pedidos atrasados"):
                    for p in pedidos_pendentes[:3]:  # Mostrar apenas 3
                        cliente = next((c for c in data['clientes'] if c['id'] == p.get('customer_id')), None)
                        cliente_nome = cliente['name'] if cliente else 'Desconhecido'
                        st.write(f"• #{p.get('order_number')} - {cliente_nome} - {formatar_moeda(p.get('total_amount', 0))}")
                    if len(pedidos_pendentes) > 3:
                        st.write(f"... e mais {len(pedidos_pendentes) - 3}")
            
            if pedidos_producao:
                st.warning(f"⏳ {len(pedidos_producao)} pedidos em produção")
                with st.expander("Ver pedidos em produção"):
                    for p in pedidos_producao[:3]:
                        cliente = next((c for c in data['clientes'] if c['id'] == p.get('customer_id')), None)
                        cliente_nome = cliente['name'] if cliente else 'Desconhecido'
                        st.write(f"• #{p.get('order_number')} - {cliente_nome}")
        
        # Informações da sessão
        st.divider()
        st.caption(f"📦 Produtos: {len(data['produtos'])}")
        st.caption(f"👥 Clientes: {len(data['clientes'])}")
        st.caption(f"🏭 Fornecedores: {len(data['fornecedores'])}")
        st.caption(f"🛒 Pedidos: {len(data['pedidos'])}")
        st.caption(f"📋 Orçamentos: {len(data['orcamentos'])}")
    
    # Conteúdo principal baseado na página atual
    page = st.session_state.get('current_page', 'calculator')
    
    if page == "calculator":
        mostrar_calculadora()
    elif page == "products":
        mostrar_produtos()
    elif page == "clientes":
        mostrar_clientes()
    elif page == "novo_cliente":
        mostrar_novo_cliente()
    elif page == "view_cliente":
        mostrar_ver_cliente()
    elif page == "edit_cliente":
        mostrar_editar_cliente()
    elif page == "fornecedores":
        mostrar_fornecedores()
    elif page == "novo_fornecedor":
        mostrar_novo_fornecedor()
    elif page == "edit_fornecedor":
        mostrar_editar_fornecedor()
    elif page == "pedidos":
        mostrar_pedidos()
    elif page == "novo_pedido":
        mostrar_novo_pedido()
    elif page == "view_pedido":
        mostrar_ver_pedido()
    elif page == "orcamentos":
        mostrar_orcamentos()
    elif page == "create_budget":
        mostrar_criar_orcamento()
    elif page == "view_budget":
        mostrar_ver_orcamento()
    elif page == "settings":
        mostrar_configuracoes()
    elif page == "account":
        mostrar_minha_conta()
    else:
        mostrar_calculadora()

if __name__ == "__main__":
    main()
