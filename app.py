import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import tempfile
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# --- IMPORTAÇÕES CORRIGIDAS ---
from auth import require_auth, get_current_user, show_login_register_page, auth_system, is_admin
from models import init_db, get_db, SessionLocal, User, Product, Customer, Supplier, Order, Budget, SystemConfig
from security import hash_password, verify_password, validate_email, validate_password_strength
from config import config

# Inicializar banco de dados
init_db()

# --- CONSTANTES E CORES ---
COLOR_PURPLE = "#9370DB"
COLOR_SLATE = "#836FFF"
COLOR_ORANGE = "#FF7F00"
COLOR_BG = "#0D1117"
COLOR_CARD = "#161B22"
COLOR_TEXT = "#E6EDF3"
COLOR_BTN = "#1F6FEB"
COLOR_GREEN = "#238636"
COLOR_RED = "#DA3633"
COLOR_GRAY = "#30363D"
COLOR_YELLOW = "#FFD700"
COLOR_BLUE = "#1F6FEB"

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

def salvar_dados(data):
    """Salva os dados no banco de dados"""
    # Esta função é mantida para compatibilidade com código existente
    # Mas agora os dados são salvos diretamente no banco em cada operação
    pass

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
        return COLOR_BLUE  # Azul para entregue
    elif pedido.get('payment_status') == 'paid':
        return COLOR_GREEN  # Verde para pago
    elif (agora - data_criacao) > timedelta(hours=24):
        return COLOR_RED  # Vermelho para pendente > 24h
    else:
        return COLOR_YELLOW  # Amarelo para recente

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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_PURPLE)),
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_ORANGE)),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(COLOR_SLATE)),
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_GREEN)),
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
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_GRAY)),
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
        st.error(f"Error generating PDF: {str(e)}")
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_PURPLE)),
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_ORANGE)),
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor(COLOR_SLATE)),
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
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_GREEN)),
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
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(COLOR_GRAY)),
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
        st.error(f"Error generating invoice: {str(e)}")
        return None

# --- TELA: CALCULATOR ---
@require_auth()
def mostrar_calculator():
    st.title("📱 Calculator - New Estimate")
    
    # Inicializar session state se necessário
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = []
    
    data = carregar_dados()
    
    col1, col2 = st.columns([3, 2])
    
    with col1:
        st.subheader("Product Configuration")
        
        # Seleção de produto
        product_names = [p['nome'] for p in data['produtos']]
        if not product_names:
            product_names = ["No products available"]
        
        produto_selecionado = st.selectbox("Product", product_names)
        
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
                incluir_custos_fixos = st.toggle("Include Fixed Costs", value=True)
            
            # Dimensões
            st.subheader("Dimensions (cm)")
            dim_cols = st.columns(4)
            with dim_cols[0]:
                frente_altura = st.number_input("Front Height", min_value=0.0, value=0.0, step=0.5)
            with dim_cols[1]:
                frente_largura = st.number_input("Front Width", min_value=0.0, value=0.0, step=0.5)
            with dim_cols[2]:
                costas_altura = st.number_input("Back Height", min_value=0.0, value=0.0, step=0.5)
            with dim_cols[3]:
                costas_largura = st.number_input("Back Width", min_value=0.0, value=0.0, step=0.5)
            
            # Quantidade e Margem
            qtd_cols = st.columns(2)
            with qtd_cols[0]:
                quantidade = st.number_input("Quantity", min_value=1, value=1)
            with qtd_cols[1]:
                margem = st.number_input("Margin %", min_value=0.0, value=data['config'].get('default_margin', 50.0), step=1.0)
            
            # Botão calcular
            if st.button("Calculate Price", type="primary", use_container_width=True):
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
                
                st.success(f"Price calculated: {formatar_moeda(preco_total)}")
    
    with col2:
        st.subheader("Results")
        
        if 'calculation_result' in st.session_state:
            result = st.session_state.calculation_result
            
            st.metric(
                label="Total Price",
                value=formatar_moeda(result['preco_total']),
                delta=None
            )
            
            st.write(f"**Product:** {result['produto']}")
            st.write(f"**Unit Price:** {formatar_moeda(result['preco_unitario'])}")
            st.write(f"**Quantity:** {result['quantidade']}")
            st.write(f"**Total Area:** {result['area_total']:.2f} cm²")
            st.write(f"**DTF:** {'Yes' if result['usa_dtf'] else 'No'}")
            
            # Botões para adicionar à seleção
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Add to Selection", use_container_width=True):
                    novo_item = {
                        'nome': result['produto'],
                        'preco_unitario': result['preco_unitario'],
                        'quantidade': result['quantidade'],
                        'preco_total': result['preco_total']
                    }
                    st.session_state.selected_products.append(novo_item)
                    st.success("Product added to selection!")
                    st.rerun()
            
            with col_btn2:
                if st.button("Clear Selection", use_container_width=True):
                    st.session_state.selected_products = []
                    st.rerun()
        else:
            st.info("Calculate a price to see results here")
        
        # Lista de produtos selecionados
        if st.session_state.selected_products:
            st.subheader("Selected Products")
            selected_df = pd.DataFrame(st.session_state.selected_products)
            st.dataframe(selected_df, use_container_width=True, hide_index=True)
            
            total_selecionado = sum(p['preco_total'] for p in st.session_state.selected_products)
            st.metric("Total Selected", formatar_moeda(total_selecionado))
            
            # Botão para criar orçamento
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("📋 Create Budget", type="primary", use_container_width=True):
                    st.session_state.current_page = "create_budget"
                    st.rerun()
            with col_btn2:
                if st.button("🛒 Create Order", type="secondary", use_container_width=True):
                    st.session_state.current_page = "novo_pedido"
                    st.rerun()
        else:
            st.info("No products selected yet")

# --- TELA: PRODUCTS ---
@require_auth()
def mostrar_products():
    st.title("📦 Product Management")
    
    data = carregar_dados()
    db = SessionLocal()
    
    try:
        # Formulário para adicionar/editar produto
        with st.expander("Add/Edit Product", expanded=True):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                nome = st.text_input("Product Name")
                custo = st.number_input("Cost (R$)", min_value=0.0, value=0.0, step=0.1)
            
            with col2:
                energia = st.number_input("Energy (R$)", min_value=0.0, value=0.0, step=0.1)
                transporte = st.number_input("Transport (R$)", min_value=0.0, value=0.0, step=0.1)
            
            with col3:
                embalagem = st.number_input("Packaging (R$)", min_value=0.0, value=0.0, step=0.1)
                usa_dtf = st.checkbox("Use DTF", value=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("Add Product", type="primary", use_container_width=True):
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
                            st.success(f"Product '{nome}' updated!")
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
                            st.success(f"Product '{nome}' added!")
                        
                        db.commit()
                        st.rerun()
                    else:
                        st.error("Product name is required")
    finally:
        db.close()
    
    # Lista de produtos
    st.subheader("Product List")
    
    if data['produtos']:
        # Criar DataFrame para exibição
        produtos_data = []
        for p in data['produtos']:
            produtos_data.append({
                "Product": p['nome'],
                "Cost": formatar_moeda(p.get('custo', p.get('cost', 0))),
                "DTF": "✓" if p.get('usa_dtf', p.get('uses_dtf', False)) else "✗",
                "Energy": formatar_moeda(p.get('energy_cost', p.get('energia', 0))),
                "Transport": formatar_moeda(p.get('transport_cost', p.get('transp', 0))),
                "Packaging": formatar_moeda(p.get('packaging_cost', p.get('emb', 0)))
            })
        
        df = pd.DataFrame(produtos_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Opções para editar/excluir
        st.subheader("Manage Products")
        produto_para_gerenciar = st.selectbox(
            "Select product to manage",
            [p['nome'] for p in data['produtos']]
        )
        
        if produto_para_gerenciar:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("Edit Product", use_container_width=True):
                    # Preencher formulário com dados do produto
                    for p in data['produtos']:
                        if p['nome'] == produto_para_gerenciar:
                            st.session_state.edit_product = p
                            st.info(f"Editing {p['nome']} - fill the form above")
                            break
            
            with col_del:
                if st.button("Delete Product", type="secondary", use_container_width=True):
                    db = SessionLocal()
                    try:
                        produto = db.query(Product).filter(Product.name == produto_para_gerenciar).first()
                        if produto:
                            produto.is_active = False
                            db.commit()
                            st.success(f"Product '{produto_para_gerenciar}' deleted!")
                            st.rerun()
                    finally:
                        db.close()
    else:
        st.info("No products registered. Add your first product above.")

# --- TELA: ORÇAMENTOS ---
@require_auth()
def mostrar_orcamentos():
    st.title("📋 Budgets")
    
    data = carregar_dados()
    
    # Estatísticas
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total Budgets", len(data['orcamentos']))
    with col_stats2:
        last_number = data['ultimo_numero_orcamento']
        st.metric("Last Number", f"#{last_number:04d}")
    with col_stats3:
        total_valor = sum(o.get('total_amount', o.get('valor_total', 0)) for o in data['orcamentos'])
        st.metric("Total Value", formatar_moeda(total_valor))
    
    # Botão para novo orçamento
    if st.button("+ New Budget", type="primary"):
        st.session_state.current_page = "create_budget"
        st.rerun()
    
    # Lista de orçamentos
    st.subheader("Budget List")
    
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
                            produto_info = f"Multiple Items ({len(items)})"
                        else:
                            produto_info = items[0].get('nome', items[0].get('name', 'Item'))
                        quantidade = sum(float(it.get('quantidade', it.get('quantity', 0))) for it in items)
                    else:
                        produto_info = "No data"
                        quantidade = 0
                    
                    budget_num = orcamento.get('budget_number', orcamento.get('numero', ''))
                    created_date = orcamento.get('created_at', orcamento.get('data', ''))
                    client_name = orcamento.get('client_name', orcamento.get('cliente', ''))
                    total_val = orcamento.get('total_amount', orcamento.get('valor_total', 0))
                    
                    st.write(f"**#{budget_num}** - {created_date}")
                    st.write(f"**Client:** {client_name}")
                    st.write(f"**Product:** {produto_info} | **Qty:** {quantidade:.0f}")
                    st.write(f"**Total:** {formatar_moeda(total_val)}")
                
                with col_acoes:
                    if st.button("Open", key=f"open_{budget_num}"):
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
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name=f"Orcamento_{budget_num}.pdf",
                                mime="application/pdf"
                            )
                    
                    if st.button("Delete", key=f"del_{budget_num}", type="secondary"):
                        db = SessionLocal()
                        try:
                            budget = db.query(Budget).filter(Budget.budget_number == budget_num).first()
                            if budget:
                                db.delete(budget)
                                db.commit()
                                st.success(f"Budget #{budget_num} deleted!")
                                st.rerun()
                        finally:
                            db.close()
                
                st.divider()
    else:
        st.info("No budgets created yet. Create your first budget!")

# --- TELA: CREATE BUDGET ---
@require_auth()
def mostrar_create_budget():
    st.title("📝 Create New Budget")
    
    data = carregar_dados()
    
    # Inicializar variáveis
    if 'manual_items' not in st.session_state:
        st.session_state.manual_items = []
    
    # Formulário principal
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Client *", placeholder="Client name")
            endereco = st.text_area("Address", placeholder="Full address")
            tipo_entrega = st.radio("Delivery Type", ["Pronta Entrega", "Sob Encomenda"])
            prazo_producao = st.text_input("Production Deadline", value="5 dias úteis")
        
        with col2:
            data_orcamento = st.date_input("Date", value=datetime.now())
            tipo_venda = st.radio("Sale Type", ["Revenda", "Personalizado"])
            observacoes = st.text_area("Observations", placeholder="Additional information")
        
        # Seção para adicionar itens manualmente
        with st.expander("Add Item Manually", expanded=False):
            prod_col1, prod_col2, prod_col3 = st.columns(3)
            with prod_col1:
                produto_manual = st.selectbox(
                    "Product",
                    ["Apenas DTF"] + [p['nome'] for p in data['produtos']],
                    key="produto_manual_select"
                )
            with prod_col2:
                quantidade_manual = st.number_input("Quantity", min_value=1, value=1, key="qtd_manual")
            with prod_col3:
                valor_unitario_manual = st.number_input("Unit Value (R$)", min_value=0.0, value=0.0, step=0.01, key="valor_manual")
            
            if st.form_submit_button("Add Item to Budget", type="secondary", use_container_width=True, key="add_item_btn"):
                if produto_manual and quantidade_manual > 0:
                    novo_item = {
                        "nome": produto_manual,
                        "quantidade": quantidade_manual,
                        "valor_unitario": valor_unitario_manual,
                        "preco_total": valor_unitario_manual * quantidade_manual
                    }
                    st.session_state.manual_items.append(novo_item)
                    st.success(f"Item '{produto_manual}' added!")
        
        # Mostrar itens adicionados manualmente
        if st.session_state.manual_items:
            st.write("**Manual Items Added:**")
            for i, item in enumerate(st.session_state.manual_items):
                col_item1, col_item2, col_item3 = st.columns([3, 1, 2])
                with col_item1:
                    st.write(f"• {item['nome']}")
                with col_item2:
                    st.write(f"Qty: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['valor_unitario'])}")
                    
                    if st.form_submit_button(f"Remove", key=f"remove_{i}"):
                        st.session_state.manual_items.pop(i)
                        st.rerun()
        
        # Mostrar itens da calculadora
        if st.session_state.get('selected_products'):
            st.write("**Items from Calculator:**")
            for i, item in enumerate(st.session_state.selected_products):
                col_item1, col_item2, col_item3 = st.columns([3, 1, 2])
                with col_item1:
                    st.write(f"• {item['nome']}")
                with col_item2:
                    st.write(f"Qty: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['preco_unitario'])}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            save_clicked = st.form_submit_button("Save Budget", type="primary", use_container_width=True, key="save_budget")
        
        with col_btn2:
            save_pdf_clicked = st.form_submit_button("Save and Generate PDF", use_container_width=True, key="save_pdf")
        
        with col_btn3:
            cancel_clicked = st.form_submit_button("Cancel", type="secondary", use_container_width=True, key="cancel_budget")
    
    # Processar ações APÓS o formulário
    if cancel_clicked:
        if 'manual_items' in st.session_state:
            st.session_state.manual_items = []
        st.session_state.current_page = "calculator"
        st.rerun()
    
    if save_clicked or save_pdf_clicked:
        if not cliente or not cliente.strip():
            st.error("❌ Client name is required!")
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
                st.warning("⚠️ Add at least one item to the budget!")
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
                    
                    st.success(f"✅ Budget #{ultimo_numero:04d} saved successfully!")
                    
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
                                label="📄 Download PDF",
                                data=pdf_bytes,
                                file_name=f"Orcamento_{ultimo_numero:04d}.pdf",
                                mime="application/pdf",
                                type="primary"
                            )
                    
                    # Opção para ir para a lista de orçamentos
                    if st.button("View Budgets List"):
                        st.session_state.current_page = "orcamentos"
                        st.rerun()
                        
                except Exception as e:
                    db.rollback()
                    st.error(f"Erro ao salvar orçamento: {str(e)}")
                finally:
                    db.close()

# --- TELA: VIEW BUDGET ---
@require_auth()
def mostrar_view_budget():
    if 'view_budget' not in st.session_state:
        st.session_state.current_page = "orcamentos"
        st.rerun()
    
    orcamento = st.session_state.view_budget
    
    st.title(f"Budget #{orcamento.get('budget_number', orcamento.get('numero', ''))}")
    
    # Informações principais
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write(f"**Client:** {orcamento.get('client_name', orcamento.get('cliente', ''))}")
        st.write(f"**Date:** {orcamento.get('created_at', orcamento.get('data', ''))}")
        st.write(f"**Delivery Type:** {orcamento.get('delivery_type', orcamento.get('tipo_entrega', ''))}")
    
    with col_info2:
        st.write(f"**Sale Type:** {orcamento.get('sale_type', orcamento.get('tipo_venda', ''))}")
        st.write(f"**Address:** {orcamento.get('address', orcamento.get('endereco', ''))}")
        st.write(f"**Deadline:** {orcamento.get('production_deadline', orcamento.get('prazo_producao', ''))}")
    
    # Itens
    st.subheader("Items")
    items = orcamento.get('items', [])
    if isinstance(items, str):
        items = json.loads(items)
    
    if items:
        itens_data = []
        for item in items:
            itens_data.append({
                "Product": item.get('nome', item.get('name', 'Unnamed')),
                "Quantity": item.get('quantidade', item.get('quantity', 0)),
                "Unit Value": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0))),
                "Total": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0)) * item.get('quantidade', item.get('quantity', 1)))
            })
        
        df = pd.DataFrame(itens_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif 'produto' in orcamento:
        st.write(f"**Product:** {orcamento['produto']}")
        st.write(f"**Quantity:** {orcamento.get('quantidade', 0)}")
        st.write(f"**Unit Value:** {formatar_moeda(orcamento.get('valor_unitario', 0))}")
    
    # Total
    st.metric("Total Value", formatar_moeda(orcamento.get('total_amount', orcamento.get('valor_total', 0))))
    
    # Observações
    if orcamento.get('observacoes') or orcamento.get('notes'):
        st.subheader("Observations")
        st.write(orcamento.get('observacoes') or orcamento.get('notes', ''))
    
    # Botões de ação
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Generate PDF", type="primary", use_container_width=True):
            pdf_path = gerar_pdf(orcamento)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="Download PDF",
                    data=pdf_bytes,
                    file_name=f"Orcamento_{orcamento.get('budget_number', orcamento.get('numero', ''))}.pdf",
                    mime="application/pdf"
                )
    
    with col_btn2:
        if st.button("Edit", use_container_width=True):
            st.warning("Edit function not implemented in web version")
    
    with col_btn3:
        if st.button("Back to List", type="secondary", use_container_width=True):
            del st.session_state.view_budget
            st.session_state.current_page = "orcamentos"
            st.rerun()

# --- TELA: CLIENTES ---
@require_auth()
def mostrar_clientes():
    st.title("👥 Clients")
    
    data = carregar_dados()
    
    # Estatísticas
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total Clients", len(data['clientes']))
    with col_stats2:
        pedidos_totais = sum(len(cliente.get('pedidos', [])) for cliente in data['clientes'])
        st.metric("Total Orders", pedidos_totais)
    with col_stats3:
        clientes_com_pedidos = sum(1 for cliente in data['clientes'] if len(cliente.get('pedidos', [])) > 0)
        st.metric("Active Clients", clientes_com_pedidos)
    
    # Botão para novo cliente
    if st.button("+ New Client", type="primary"):
        st.session_state.current_page = "novo_cliente"
        st.rerun()
    
    # Lista de clientes
    st.subheader("Client List")
    
    if data['clientes']:
        for cliente in data['clientes']:
            cor_borda = COLOR_GREEN if len(cliente.get('pedidos', [])) > 0 else COLOR_GRAY
            
            with st.container():
                st.markdown(f"""
                <div style="border-left: 5px solid {cor_borda}; padding-left: 10px; margin-bottom: 10px;">
                """, unsafe_allow_html=True)
                
                col_info, col_acoes = st.columns([3, 1])
                
                with col_info:
                    st.write(f"**{cliente['name']}**")
                    if cliente.get('document'):
                        st.write(f"**Document:** {cliente['document']}")
                    if cliente.get('address'):
                        st.write(f"**Address:** {cliente['address']}")
                    if cliente.get('zip_code'):
                        st.write(f"**ZIP Code:** {cliente['zip_code']}")
                    
                    # Contar pedidos
                    num_pedidos = len(cliente.get('pedidos', []))
                    pedidos_pagos = sum(1 for pedido_id in cliente.get('pedidos', []) 
                                      for p in data['pedidos'] if p['id'] == pedido_id and p.get('payment_status') == 'paid')
                    
                    st.write(f"**Orders:** {num_pedidos} (Paid: {pedidos_pagos})")
                
                with col_acoes:
                    col_btn1, col_btn2 = st.columns(2)
                    
                    with col_btn1:
                        if st.button("📋", key=f"view_cliente_{cliente['id']}", help="View/Edit"):
                            st.session_state.view_cliente = cliente
                            st.session_state.current_page = "view_cliente"
                            st.rerun()
                    
                    with col_btn2:
                        if st.button("🛒", key=f"order_cliente_{cliente['id']}", help="New Order"):
                            st.session_state.novo_pedido_cliente = cliente
                            st.session_state.current_page = "novo_pedido"
                            st.rerun()
                
                st.markdown("</div>", unsafe_allow_html=True)
                st.divider()
    else:
        st.info("No clients registered. Create your first client!")

# --- TELA: NOVO CLIENTE ---
@require_auth()
def mostrar_novo_cliente():
    st.title("👤 New Client")
    
    db = SessionLocal()
    
    with st.form("cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", placeholder="Full name")
            email = st.text_input("Email", placeholder="email@example.com")
            telefone = st.text_input("Phone", placeholder="(00) 00000-0000")
            
            tipo_documento = st.selectbox("Document Type", ["CPF", "CNPJ"])
            
            if tipo_documento == "CPF":
                documento = st.text_input("CPF", placeholder="000.000.000-00")
                if documento:
                    documento = formatar_cpf(documento)
            else:
                documento = st.text_input("CNPJ", placeholder="00.000.000/0000-00")
                if documento:
                    documento = formatar_cnpj(documento)
        
        with col2:
            endereco = st.text_area("Address", placeholder="Street, Number, Neighborhood")
            cep = st.text_input("ZIP Code", placeholder="00000-000")
            cidade = st.text_input("City", placeholder="City")
            estado = st.text_input("State", placeholder="State", max_chars=2)
            observacoes = st.text_area("Notes", placeholder="Additional information")
        
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            submit = st.form_submit_button("Save Client", type="primary", use_container_width=True)
        
        with col_btn2:
            save_and_order = st.form_submit_button("Save and Create Order", use_container_width=True)
        
        with col_btn3:
            cancel = st.form_submit_button("Cancel", type="secondary", use_container_width=True)
    
    if cancel:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    if submit or save_and_order:
        if not nome.strip():
            st.error("❌ Client name is required!")
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
                
                st.success(f"✅ Client '{nome}' saved successfully!")
                
                if save_and_order:
                    st.session_state.novo_pedido_cliente = novo_cliente.to_dict()
                    st.session_state.current_page = "novo_pedido"
                    st.rerun()
                else:
                    if st.button("Back to Clients List"):
                        st.session_state.current_page = "clientes"
                        st.rerun()
                        
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar cliente: {str(e)}")
            finally:
                db.close()

# --- TELA: VIEW CLIENTE ---
@require_auth()
def mostrar_view_cliente():
    if 'view_cliente' not in st.session_state:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    cliente = st.session_state.view_cliente
    data = carregar_dados()
    
    st.title(f"👤 {cliente['name']}")
    
    # Abas para informações do cliente
    tab1, tab2, tab3 = st.tabs(["📋 Client Info", "🛒 Orders", "📊 Statistics"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {cliente['name']}")
            if cliente.get('email'):
                st.write(f"**Email:** {cliente['email']}")
            if cliente.get('phone'):
                st.write(f"**Phone:** {cliente['phone']}")
            if cliente.get('document'):
                st.write(f"**Document ({cliente.get('document_type', '')}):** {cliente['document']}")
        
        with col2:
            if cliente.get('address'):
                st.write(f"**Address:** {cliente['address']}")
            if cliente.get('zip_code'):
                st.write(f"**ZIP Code:** {cliente['zip_code']}")
            if cliente.get('city'):
                st.write(f"**City:** {cliente['city']}")
            if cliente.get('state'):
                st.write(f"**State:** {cliente['state']}")
            if cliente.get('notes'):
                st.write(f"**Notes:** {cliente['notes']}")
        
        st.write(f"**Registration Date:** {cliente.get('created_at', 'N/A')}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            if st.button("Edit Client", type="primary", use_container_width=True):
                st.session_state.edit_cliente = cliente
                st.session_state.current_page = "edit_cliente"
                st.rerun()
        
        with col_btn2:
            if st.button("New Order", use_container_width=True):
                st.session_state.novo_pedido_cliente = cliente
                st.session_state.current_page = "novo_pedido"
                st.rerun()
        
        with col_btn3:
            if st.button("Back to List", type="secondary", use_container_width=True):
                del st.session_state.view_cliente
                st.session_state.current_page = "clientes"
                st.rerun()
    
    with tab2:
        st.subheader("Client Orders")
        
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
                        st.write(f"**Order #{pedido.get('order_number', pedido.get('id', ''))}** - {pedido.get('created_at', '')}")
                        st.write(f"**Total:** {formatar_moeda(pedido.get('total_amount', 0))}")
                        
                        # Mostrar produtos
                        items = pedido.get('items', [])
                        if isinstance(items, str):
                            items = json.loads(items)
                        
                        if items:
                            produtos = ", ".join([item.get('nome', item.get('name', '')) for item in items[:3]])
                            if len(items) > 3:
                                produtos += f" (+{len(items) - 3} more)"
                            st.write(f"**Products:** {produtos}")
                    
                    with col_status:
                        # Status de pagamento
                        if pedido.get('payment_status') == 'paid':
                            st.write("🟢 **Paid**")
                            if pedido.get('payment_method'):
                                st.write(f"({pedido['payment_method']})")
                        else:
                            st.write("🔴 **Pending Payment**")
                        
                        # Status de entrega
                        if pedido.get('delivery_status') == 'delivered':
                            st.write("✓ **Delivered**")
                        else:
                            st.write("⏳ **In Production**")
                    
                    with col_acoes:
                        if st.button("View", key=f"view_pedido_{pedido.get('id', '')}"):
                            st.session_state.view_pedido = pedido
                            st.session_state.current_page = "view_pedido"
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.divider()
        else:
            st.info("This client has no orders yet.")
        
        # Botão para novo pedido
        if st.button("+ New Order for this Client", type="primary"):
            st.session_state.novo_pedido_cliente = cliente
            st.session_state.current_page = "novo_pedido"
            st.rerun()
    
    with tab3:
        st.subheader("Client Statistics")
        
        # Filtrar pedidos deste cliente
        pedidos_cliente = [p for p in data['pedidos'] if p.get('customer_id') == cliente['id']]
        
        if pedidos_cliente:
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                total_pedidos = len(pedidos_cliente)
                st.metric("Total Orders", total_pedidos)
            
            with col_stat2:
                pedidos_pagos = sum(1 for p in pedidos_cliente if p.get('payment_status') == 'paid')
                st.metric("Paid Orders", pedidos_pagos)
            
            with col_stat3:
                pedidos_entregues = sum(1 for p in pedidos_cliente if p.get('delivery_status') == 'delivered')
                st.metric("Delivered Orders", pedidos_entregues)
            
            # Valor total gasto
            valor_total = sum(p.get('total_amount', 0) for p in pedidos_cliente)
            st.metric("Total Spent", formatar_moeda(valor_total))
            
            # Último pedido
            if pedidos_cliente:
                ultimo_pedido = max(pedidos_cliente, key=lambda x: x.get('created_at', ''))
                st.write(f"**Last Order:** #{ultimo_pedido.get('order_number', ultimo_pedido.get('id', ''))} - {ultimo_pedido.get('created_at', '')}")
                st.write(f"**Status:** {'Paid' if ultimo_pedido.get('payment_status') == 'paid' else 'Pending'} | {'Delivered' if ultimo_pedido.get('delivery_status') == 'delivered' else 'In Production'}")
        else:
            st.info("No statistics available - client has no orders yet.")

# --- TELA: EDIT CLIENTE ---
@require_auth()
def mostrar_edit_cliente():
    if 'edit_cliente' not in st.session_state:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    cliente = st.session_state.edit_cliente
    db = SessionLocal()
    
    st.title(f"✏️ Edit Client: {cliente['name']}")
    
    with st.form("edit_cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", value=cliente.get('name', ''), placeholder="Full name")
            email = st.text_input("Email", value=cliente.get('email', ''), placeholder="email@example.com")
            telefone = st.text_input("Phone", value=cliente.get('phone', ''), placeholder="(00) 00000-0000")
            
            tipo_documento = st.selectbox("Document Type", ["CPF", "CNPJ"], 
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
            endereco = st.text_area("Address", value=cliente.get('address', ''), 
                                   placeholder="Street, Number, Neighborhood")
            cep = st.text_input("ZIP Code", value=cliente.get('zip_code', ''), placeholder="00000-000")
            cidade = st.text_input("City", value=cliente.get('city', ''), placeholder="City")
            estado = st.text_input("State", value=cliente.get('state', ''), placeholder="State", max_chars=2)
            observacoes = st.text_area("Notes", value=cliente.get('notes', ''), 
                                      placeholder="Additional information")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submit = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
        
        with col_btn2:
            cancel = st.form_submit_button("Cancel", type="secondary", use_container_width=True)
    
    if cancel:
        del st.session_state.edit_cliente
        st.session_state.current_page = "clientes"
        st.rerun()
    
    if submit:
        if not nome.strip():
            st.error("❌ Client name is required!")
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
                    st.success(f"✅ Client '{nome}' updated successfully!")
                    
                    if st.button("Back to Client"):
                        del st.session_state.edit_cliente
                        st.session_state.view_cliente = customer.to_dict()
                        st.session_state.current_page = "view_cliente"
                        st.rerun()
                else:
                    st.error("Client not found in database")
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao atualizar cliente: {str(e)}")
            finally:
                db.close()

# --- TELA: FORNECEDORES ---
@require_auth()
def mostrar_fornecedores():
    st.title("🏭 Suppliers")
    
    data = carregar_dados()
    
    # Estatísticas
    col_stats1, col_stats2 = st.columns(2)
    with col_stats1:
        st.metric("Total Suppliers", len(data['fornecedores']))
    with col_stats2:
        tipos = set(f.get('supplier_type', '') for f in data['fornecedores'])
        st.metric("Categories", len(tipos))
    
    # Botão para novo fornecedor
    if st.button("+ New Supplier", type="primary"):
        st.session_state.current_page = "novo_fornecedor"
        st.rerun()
    
    # Lista de fornecedores por categoria
    st.subheader("Supplier List")
    
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
                                st.write(f"**Trade Name:** {fornecedor['trade_name']}")
                            if fornecedor.get('document'):
                                st.write(f"**Document:** {fornecedor['document']}")
                            if fornecedor.get('address'):
                                st.write(f"**Address:** {fornecedor['address']}")
                            if fornecedor.get('notes'):
                                st.write(f"**Notes:** {fornecedor['notes']}")
                        
                        with col_acoes:
                            if st.button("Edit", key=f"edit_fornecedor_{fornecedor['id']}"):
                                st.session_state.edit_fornecedor = fornecedor
                                st.session_state.current_page = "edit_fornecedor"
                                st.rerun()
                        
                        st.divider()
    else:
        st.info("No suppliers registered. Create your first supplier!")

# --- TELA: NOVO FORNECEDOR ---
@require_auth()
def mostrar_novo_fornecedor():
    st.title("🏭 New Supplier")
    
    db = SessionLocal()
    
    with st.form("fornecedor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", placeholder="Company name")
            nome_fantasia = st.text_input("Trade Name", placeholder="Trade name (optional)")
            
            tipo = st.selectbox("Type", ["Camisaria", "Serviços", "Canecas e Brindes", 
                                        "DTF e Estamparia", "Acessórios", "Outros"])
            
            tipo_documento = st.selectbox("Document Type", ["None", "CPF", "CNPJ"])
            
            if tipo_documento != "None":
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
            endereco = st.text_area("Address", placeholder="Full address")
            telefone = st.text_input("Phone", placeholder="(00) 00000-0000")
            email = st.text_input("Email", placeholder="email@example.com")
            observacoes = st.text_area("Notes", placeholder="Additional information")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submit = st.form_submit_button("Save Supplier", type="primary", use_container_width=True)
        
        with col_btn2:
            cancel = st.form_submit_button("Cancel", type="secondary", use_container_width=True)
    
    if cancel:
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    if submit:
        if not nome.strip():
            st.error("❌ Supplier name is required!")
        else:
            try:
                current_user = get_current_user()
                user = db.query(User).filter(User.id == current_user['id']).first()
                
                novo_fornecedor = Supplier(
                    name=nome.strip(),
                    trade_name=nome_fantasia.strip(),
                    supplier_type=tipo,
                    document_type=tipo_documento if tipo_documento != "None" else "",
                    document=documento.strip(),
                    address=endereco.strip(),
                    phone=telefone.strip(),
                    email=email.strip(),
                    notes=observacoes.strip(),
                    user=user
                )
                
                db.add(novo_fornecedor)
                db.commit()
                
                st.success(f"✅ Supplier '{nome}' saved successfully!")
                
                if st.button("Back to Suppliers List"):
                    st.session_state.current_page = "fornecedores"
                    st.rerun()
                    
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar fornecedor: {str(e)}")
            finally:
                db.close()

# --- TELA: EDIT FORNECEDOR ---
@require_auth()
def mostrar_edit_fornecedor():
    if 'edit_fornecedor' not in st.session_state:
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    fornecedor = st.session_state.edit_fornecedor
    db = SessionLocal()
    
    st.title(f"✏️ Edit Supplier: {fornecedor['name']}")
    
    with st.form("edit_fornecedor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", value=fornecedor.get('name', ''), placeholder="Company name")
            nome_fantasia = st.text_input("Trade Name", value=fornecedor.get('trade_name', ''), 
                                         placeholder="Trade name (optional)")
            
            tipo = st.selectbox("Type", ["Camisaria", "Serviços", "Canecas e Brindes", 
                                        "DTF e Estamparia", "Acessórios", "Outros"],
                               index=["Camisaria", "Serviços", "Canecas e Brindes", 
                                     "DTF e Estamparia", "Acessórios", "Outros"].index(
                                         fornecedor.get('supplier_type', 'Outros')))
            
            tipo_documento_atual = fornecedor.get('document_type', 'None')
            tipo_documento = st.selectbox("Document Type", ["None", "CPF", "CNPJ"],
                                         index=["None", "CPF", "CNPJ"].index(
                                             tipo_documento_atual if tipo_documento_atual in ["None", "CPF", "CNPJ"] else "None"))
            
            if tipo_documento != "None":
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
            endereco = st.text_area("Address", value=fornecedor.get('address', ''), 
                                   placeholder="Full address")
            telefone = st.text_input("Phone", value=fornecedor.get('phone', ''), 
                                    placeholder="(00) 00000-0000")
            email = st.text_input("Email", value=fornecedor.get('email', ''), 
                                 placeholder="email@example.com")
            observacoes = st.text_area("Notes", value=fornecedor.get('notes', ''), 
                                      placeholder="Additional information")
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            submit = st.form_submit_button("Save Changes", type="primary", use_container_width=True)
        
        with col_btn2:
            cancel = st.form_submit_button("Cancel", type="secondary", use_container_width=True)
    
    if cancel:
        del st.session_state.edit_fornecedor
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    if submit:
        if not nome.strip():
            st.error("❌ Supplier name is required!")
        else:
            try:
                supplier = db.query(Supplier).filter(Supplier.id == fornecedor['id']).first()
                if supplier:
                    supplier.name = nome.strip()
                    supplier.trade_name = nome_fantasia.strip()
                    supplier.supplier_type = tipo
                    supplier.document_type = tipo_documento if tipo_documento != "None" else ""
                    supplier.document = documento.strip()
                    supplier.address = endereco.strip()
                    supplier.phone = telefone.strip()
                    supplier.email = email.strip()
                    supplier.notes = observacoes.strip()
                    
                    db.commit()
                    st.success(f"✅ Supplier '{nome}' updated successfully!")
                    
                    if st.button("Back to Suppliers"):
                        del st.session_state.edit_fornecedor
                        st.session_state.current_page = "fornecedores"
                        st.rerun()
                else:
                    st.error("Supplier not found in database")
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao atualizar fornecedor: {str(e)}")
            finally:
                db.close()

# --- TELA: PEDIDOS ---
@require_auth()
def mostrar_pedidos():
    st.title("🛒 Orders")
    
    data = carregar_dados()
    
    # Estatísticas
    pedidos_pendentes = sum(1 for p in data['pedidos'] if p.get('payment_status') != 'paid')
    pedidos_pagos = sum(1 for p in data['pedidos'] if p.get('payment_status') == 'paid')
    pedidos_entregues = sum(1 for p in data['pedidos'] if p.get('delivery_status') == 'delivered')
    
    col_stats1, col_stats2, col_stats3, col_stats4 = st.columns(4)
    with col_stats1:
        st.metric("Total Orders", len(data['pedidos']))
    with col_stats2:
        st.metric("Pending Payment", pedidos_pendentes)
    with col_stats3:
        st.metric("Paid", pedidos_pagos)
    with col_stats4:
        st.metric("Delivered", pedidos_entregues)
    
    # Botão para novo pedido
    if st.button("+ New Order", type="primary"):
        st.session_state.current_page = "novo_pedido"
        st.rerun()
    
    # Filtros
    st.subheader("Filters")
    col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
    
    with col_filtro1:
        filtro_status = st.multiselect("Payment Status", 
                                      ["All", "Pending", "Paid"],
                                      default=["All"])
    
    with col_filtro2:
        filtro_entrega = st.multiselect("Delivery Status",
                                       ["All", "Pending", "Delivered"],
                                       default=["All"])
    
    with col_filtro3:
        # Filtro por cliente
        clientes_nomes = ["All"] + [c['name'] for c in data['clientes']]
        filtro_cliente = st.selectbox("Client", clientes_nomes)
    
    # Lista de pedidos
    st.subheader("Order List")
    
    if data['pedidos']:
        # Ordenar por data (mais recente primeiro)
        pedidos_ordenados = sorted(data['pedidos'], key=lambda x: x.get('created_at', ''), reverse=True)
        
        # Aplicar filtros
        pedidos_filtrados = []
        for pedido in pedidos_ordenados:
            # Filtro de status de pagamento
            if "All" not in filtro_status:
                status_pagamento = "Paid" if pedido.get('payment_status') == 'paid' else "Pending"
                if status_pagamento not in filtro_status:
                    continue
            
            # Filtro de status de entrega
            if "All" not in filtro_entrega:
                status_entrega = "Delivered" if pedido.get('delivery_status') == 'delivered' else "Pending"
                if status_entrega not in filtro_entrega:
                    continue
            
            # Filtro por cliente
            if filtro_cliente != "All":
                cliente = next((c for c in data['clientes'] if c['id'] == pedido.get('customer_id')), None)
                if not cliente or cliente['name'] != filtro_cliente:
                    continue
            
            pedidos_filtrados.append(pedido)
        
        if not pedidos_filtrados:
            st.info("No orders match the selected filters.")
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
                        cliente_nome = "Unknown"
                        for cliente in data['clientes']:
                            if cliente['id'] == pedido.get('customer_id'):
                                cliente_nome = cliente['name']
                                break
                        
                        st.write(f"**Order #{pedido.get('order_number', pedido.get('id', ''))}** - {pedido.get('created_at', '')}")
                        st.write(f"**Client:** {cliente_nome}")
                        st.write(f"**Total:** {formatar_moeda(pedido.get('total_amount', 0))}")
                        
                        # Mostrar produtos
                        items = pedido.get('items', [])
                        if isinstance(items, str):
                            items = json.loads(items)
                        
                        if items:
                            produtos = ", ".join([item.get('nome', item.get('name', '')) for item in items[:2]])
                            if len(items) > 2:
                                produtos += f" (+{len(items) - 2} more)"
                            st.write(f"**Products:** {produtos}")
                    
                    with col_status:
                        # Status de pagamento
                        if pedido.get('payment_status') == 'paid':
                            st.write("🟢 **Paid**")
                            if pedido.get('payment_method'):
                                st.write(f"({pedido['payment_method']})")
                        else:
                            # Verificar se está atrasado
                            data_criacao = datetime.fromisoformat(pedido.get('created_at')) if pedido.get('created_at') else datetime.now()
                            if (datetime.now() - data_criacao) > timedelta(hours=24):
                                st.write("🔴 **Overdue Payment**")
                            else:
                                st.write("🟡 **Pending Payment**")
                        
                        # Status de entrega
                        if pedido.get('delivery_status') == 'delivered':
                            st.write("✓ **Delivered**")
                        else:
                            st.write("⏳ **In Production**")
                    
                    with col_acoes:
                        if st.button("View", key=f"view_pedido_main_{pedido.get('id', '')}"):
                            st.session_state.view_pedido = pedido
                            st.session_state.current_page = "view_pedido"
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.divider()
    else:
        st.info("No orders created yet. Create your first order!")

# --- TELA: NOVO PEDIDO ---
@require_auth()
def mostrar_novo_pedido():
    st.title("🛒 New Order")
    
    data = carregar_dados()
    
    # Inicializar variáveis
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = []
    
    if 'manual_items' not in st.session_state:
        st.session_state.manual_items = []
    
    # Formulário principal
    with st.form("pedido_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Seleção de cliente
            clientes_options = [c['name'] for c in data['clientes']]
            
            if st.session_state.get('novo_pedido_cliente'):
                cliente_pre_selecionado = st.session_state.novo_pedido_cliente['name']
                cliente_selecionado = st.selectbox("Client *", clientes_options, 
                                                  index=clientes_options.index(cliente_pre_selecionado) 
                                                  if cliente_pre_selecionado in clientes_options else 0)
            else:
                cliente_selecionado = st.selectbox("Client *", clientes_options)
            
            # Obter cliente selecionado
            cliente_atual = None
            for c in data['clientes']:
                if c['name'] == cliente_selecionado:
                    cliente_atual = c
                    break
            
            if cliente_atual:
                st.write(f"**Document:** {cliente_atual.get('document', 'N/A')}")
                st.write(f"**Address:** {cliente_atual.get('address', 'N/A')}")
                if cliente_atual.get('phone'):
                    st.write(f"**Phone:** {cliente_atual['phone']}")
            
            prazo_entrega = st.text_input("Delivery Deadline", value="5 dias úteis")
        
        with col2:
            tipo_entrega = st.radio("Delivery Type", ["Pronta Entrega", "Sob Encomenda"])
            forma_pagamento = st.selectbox("Payment Method", 
                                          ["Not Defined", "Cash", "Credit Card", 
                                           "Debit Card", "PIX", "Bank Transfer"])
            observacoes = st.text_area("Observations", placeholder="Additional information")
        
        # Seção para adicionar produtos
        st.subheader("Add Products")
        
        col_prod1, col_prod2, col_prod3 = st.columns(3)
        with col_prod1:
            produto_selecionado = st.selectbox("Product", 
                                              ["Apenas DTF"] + [p['nome'] for p in data['produtos']])
        
        with col_prod2:
            quantidade = st.number_input("Quantity", min_value=1, value=1)
        
        with col_prod3:
            valor_unitario = st.number_input("Unit Value (R$)", min_value=0.0, value=0.0, step=0.01)
        
        if st.form_submit_button("Add Product to Order", type="secondary", use_container_width=True):
            if produto_selecionado and quantidade > 0:
                novo_item = {
                    "nome": produto_selecionado,
                    "quantidade": quantidade,
                    "valor_unitario": valor_unitario,
                    "preco_total": valor_unitario * quantidade
                }
                st.session_state.manual_items.append(novo_item)
                st.success(f"Product '{produto_selecionado}' added!")
        
        # Mostrar itens adicionados
        if st.session_state.manual_items:
            st.write("**Items in Order:**")
            total_pedido = 0
            
            for i, item in enumerate(st.session_state.manual_items):
                col_item1, col_item2, col_item3, col_item4 = st.columns([3, 1, 2, 1])
                with col_item1:
                    st.write(f"• {item['nome']}")
                with col_item2:
                    st.write(f"Qty: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['valor_unitario'])}")
                    total_item = item['valor_unitario'] * item['quantidade']
                    st.write(f"**Total:** {formatar_moeda(total_item)}")
                    total_pedido += total_item
                
                with col_item4:
                    if st.form_submit_button("❌", key=f"remove_item_{i}"):
                        st.session_state.manual_items.pop(i)
                        st.rerun()
            
            st.write(f"**Order Total:** {formatar_moeda(total_pedido)}")
        
        # Mostrar itens da calculadora se existirem
        if st.session_state.get('selected_products'):
            st.write("**Items from Calculator:**")
            for i, item in enumerate(st.session_state.selected_products):
                col_item1, col_item2, col_item3 = st.columns([3, 1, 2])
                with col_item1:
                    st.write(f"• {item['nome']}")
                with col_item2:
                    st.write(f"Qty: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['preco_unitario'])}")
        
        # Botões de ação
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            save_clicked = st.form_submit_button("Save Order", type="primary", use_container_width=True)
        
        with col_btn2:
            save_pdf_clicked = st.form_submit_button("Save and Generate Invoice", use_container_width=True)
        
        with col_btn3:
            cancel_clicked = st.form_submit_button("Cancel", type="secondary", use_container_width=True)
    
    # Processar ações APÓS o formulário
    if cancel_clicked:
        # Limpar dados temporários
        if 'manual_items' in st.session_state:
            st.session_state.manual_items = []
        if 'novo_pedido_cliente' in st.session_state:
            del st.session_state.novo_pedido_cliente
        st.session_state.current_page = "pedidos"
        st.rerun()
    
    if save_clicked or save_pdf_clicked:
        if not cliente_selecionado:
            st.error("❌ Client is required!")
        elif not st.session_state.manual_items and not st.session_state.get('selected_products'):
            st.warning("⚠️ Add at least one item to the order!")
        else:
            # Calcular valor total
            total = 0
            
            # Somar itens da calculadora
            if st.session_state.get('selected_products'):
                total += sum(item['preco_total'] for item in st.session_state.selected_products)
            
            # Somar itens manuais
            if st.session_state.manual_items:
                total += sum(item['preco_total'] for item in st.session_state.manual_items)
            
            # Criar novo pedido no banco
            db = SessionLocal()
            try:
                current_user = get_current_user()
                user = db.query(User).filter(User.id == current_user['id']).first()
                
                customer = db.query(Customer).filter(Customer.id == cliente_atual['id']).first()
                
                # Gerar número do pedido
                ultimo_numero = db.query(Order).count() + 1
                
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
                
                novo_pedido = Order(
                    order_number=str(ultimo_numero).zfill(4),
                    customer=customer,
                    user=user,
                    total_amount=total,
                    items=json.dumps(itens_para_salvar),
                    delivery_type=tipo_entrega,
                    delivery_deadline=prazo_entrega,
                    payment_method=forma_pagamento if forma_pagamento != "Not Defined" else "",
                    payment_status='pending',
                    delivery_status='production',
                    notes=observacoes.strip()
                )
                
                db.add(novo_pedido)
                db.commit()
                
                st.success(f"✅ Order #{ultimo_numero} saved successfully!")
                
                # Limpar dados temporários
                if 'selected_products' in st.session_state:
                    st.session_state.selected_products = []
                if 'manual_items' in st.session_state:
                    st.session_state.manual_items = []
                if 'novo_pedido_cliente' in st.session_state:
                    del st.session_state.novo_pedido_cliente
                
                # Gerar nota fiscal se solicitado
                if save_pdf_clicked:
                    pdf_path = gerar_nota_fiscal(novo_pedido.to_dict(), cliente_atual)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="📄 Download Invoice",
                            data=pdf_bytes,
                            file_name=f"Nota_Pedido_{ultimo_numero}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                
                # Opção para ir para a lista de pedidos
                if st.button("View Orders List"):
                    st.session_state.current_page = "pedidos"
                    st.rerun()
                    
            except Exception as e:
                db.rollback()
                st.error(f"Erro ao salvar pedido: {str(e)}")
            finally:
                db.close()

# --- TELA: VIEW PEDIDO ---
@require_auth()
def mostrar_view_pedido():
    if 'view_pedido' not in st.session_state:
        st.session_state.current_page = "pedidos"
        st.rerun()
    
    pedido = st.session_state.view_pedido
    data = carregar_dados()
    
    # Obter cliente
    cliente = next((c for c in data['clientes'] if c['id'] == pedido.get('customer_id')), None)
    
    st.title(f"🛒 Order #{pedido.get('order_number', pedido.get('id', ''))}")
    
    # Informações principais
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write(f"**Client:** {cliente['name'] if cliente else 'Unknown'}")
        st.write(f"**Creation Date:** {pedido.get('created_at', '')}")
        st.write(f"**Delivery Type:** {pedido.get('delivery_type', '')}")
        st.write(f"**Delivery Deadline:** {pedido.get('delivery_deadline', '')}")
    
    with col_info2:
        st.write(f"**Payment Method:** {pedido.get('payment_method', 'Not defined')}")
        if pedido.get('paid_at'):
            st.write(f"**Payment Date:** {pedido.get('paid_at')}")
        if pedido.get('delivered_at'):
            st.write(f"**Delivery Date:** {pedido.get('delivered_at')}")
    
    # Status
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        if pedido.get('payment_status') == 'paid':
            st.success("✅ **PAID**")
        else:
            st.error("❌ **PENDING PAYMENT**")
    
    with col_status2:
        if pedido.get('delivery_status') == 'delivered':
            st.success("✅ **DELIVERED**")
        else:
            st.warning("⏳ **IN PRODUCTION**")
    
    # Itens
    st.subheader("Items")
    items = pedido.get('items', [])
    if isinstance(items, str):
        items = json.loads(items)
    
    if items:
        itens_data = []
        for item in items:
            itens_data.append({
                "Product": item.get('nome', item.get('name', 'Unnamed')),
                "Quantity": item.get('quantidade', item.get('quantity', 0)),
                "Unit Value": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0))),
                "Total": formatar_moeda(item.get('valor_unitario', item.get('unit_price', 0)) * item.get('quantidade', item.get('quantity', 1)))
            })
        
        df = pd.DataFrame(itens_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Total
    st.metric("Total Value", formatar_moeda(pedido.get('total_amount', 0)))
    
    # Observações
    if pedido.get('notes'):
        st.subheader("Observations")
        st.write(pedido['notes'])
    
    # Controles de status
    st.subheader("Update Status")
    
    col_status_btn1, col_status_btn2, col_status_btn3 = st.columns(3)
    
    with col_status_btn1:
        if pedido.get('payment_status') != 'paid':
            if st.button("Mark as Paid", type="primary", use_container_width=True):
                # Mostrar opções de pagamento
                st.session_state.pagar_pedido = pedido
                st.rerun()
        else:
            st.info("✅ Order already paid")
    
    with col_status_btn2:
        if pedido.get('delivery_status') != 'delivered':
            if st.button("Mark as Delivered", type="primary", use_container_width=True):
                db = SessionLocal()
                try:
                    order = db.query(Order).filter(Order.id == pedido['id']).first()
                    if order:
                        order.delivery_status = 'delivered'
                        order.delivered_at = datetime.now()
                        db.commit()
                        st.success("✅ Order marked as delivered!")
                        # Atualizar o pedido na session_state
                        st.session_state.view_pedido = order.to_dict()
                        # Forçar recarregamento imediato
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
                finally:
                    db.close()
        else:
            st.info("✅ Order already delivered")
    
    with col_status_btn3:
        if st.button("Generate Invoice", type="secondary", use_container_width=True):
            # Gerar PDF do pedido
            pdf_path = gerar_nota_fiscal(pedido, cliente)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="📄 Download Invoice",
                    data=pdf_bytes,
                    file_name=f"Nota_Pedido_{pedido.get('order_number', pedido.get('id', ''))}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
    
    # Seção para marcar como pago
    if st.session_state.get('pagar_pedido') == pedido:
        st.subheader("Confirm Payment")
        
        forma_pagamento = st.selectbox("Payment Method", 
                                      ["Cash", "Credit Card", "Debit Card", "PIX", "Bank Transfer"])
        
        col_confirm1, col_confirm2 = st.columns(2)
        
        with col_confirm1:
            if st.button("Confirm Payment", type="primary", use_container_width=True):
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
                        st.success("✅ Payment confirmed!")
                        st.rerun()
                finally:
                    db.close()
        
        with col_confirm2:
            if st.button("Cancel", type="secondary", use_container_width=True):
                del st.session_state.pagar_pedido
                st.rerun()
    
    # Botão para voltar
    if st.button("← Back to Orders List", type="secondary", use_container_width=True):
        if 'pagar_pedido' in st.session_state:
            del st.session_state.pagar_pedido
        st.session_state.current_page = "pedidos"
        st.rerun()

# --- TELA: SETTINGS ---
@require_auth()
def mostrar_settings():
    st.title("⚙️ Settings")
    
    if not is_admin():
        st.error("⚠️ You need administrator privileges to access settings.")
        return
    
    data = carregar_dados()
    db = SessionLocal()
    
    try:
        # DTF Costs
        st.subheader("DTF Costs")
        col_dtf1, col_dtf2, col_dtf3 = st.columns(3)
        
        with col_dtf1:
            preco_metro = st.number_input("Price per Meter (R$)", 
                                        value=data['config'].get('dtf_price_per_meter', 80.0), 
                                        min_value=0.0, step=0.1, key="preco_metro")
        
        with col_dtf2:
            largura_rolo = st.number_input("Roll Width (cm)", 
                                         value=data['config'].get('roll_width', 58.0), 
                                         min_value=0.0, step=0.1, key="largura_rolo")
        
        with col_dtf3:
            altura_rolo = st.number_input("Roll Height (cm)", 
                                        value=data['config'].get('roll_height', 100), 
                                        min_value=0.0, step=0.1, key="altura_rolo")
        
        # Custom Labels and Fixed Costs
        st.subheader("Custom Labels and Fixed Costs")
        
        col_label1, col_label2, col_label3 = st.columns(3)
        
        with col_label1:
            st.write("**Energy**")
            label_energia = st.text_input("Label", value=data['config'].get('energy_cost_label', 'Energy (R$)'), key="label_energia")
            valor_energia = st.number_input("Value (R$)", value=data['config'].get('energy_cost_value', 1.0), 
                                           min_value=0.0, step=0.1, key="val_energia")
        
        with col_label2:
            st.write("**Transport**")
            label_transporte = st.text_input("Label", value=data['config'].get('transport_cost_label', 'Transport (R$)'), key="label_transporte")
            valor_transporte = st.number_input("Value (R$)", value=data['config'].get('transport_cost_value', 2.0), 
                                              min_value=0.0, step=0.1, key="val_transporte")
        
        with col_label3:
            st.write("**Packaging**")
            label_embalagem = st.text_input("Label", value=data['config'].get('packaging_cost_label', 'Packaging (R$)'), key="label_embalagem")
            valor_embalagem = st.number_input("Value (R$)", value=data['config'].get('packaging_cost_value', 1.0), 
                                             min_value=0.0, step=0.1, key="val_embalagem")
        
        # General Settings
        st.subheader("General Settings")
        col_gen1, col_gen2 = st.columns(2)
        
        with col_gen1:
            default_margin = st.number_input("Default Margin %", 
                                           value=data['config'].get('default_margin', 50.0), 
                                           min_value=0.0, step=1.0, key="default_margin")
        
        with col_gen2:
            default_production_days = st.number_input("Default Production Days", 
                                                    value=data['config'].get('default_production_days', 5), 
                                                    min_value=1, step=1, key="default_production_days")
        
        # Botão salvar
        if st.button("Save All Settings", type="primary", use_container_width=True):
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
                            description=f"Auto-generated from settings page"
                        )
                        db.add(config_item)
                
                db.commit()
                st.success("Settings saved successfully!")
                
            except Exception as e:
                db.rollback()
                st.error(f"Error saving settings: {str(e)}")
    finally:
        db.close()

# --- TELA: MINHA CONTA ---
@require_auth()
def mostrar_account():
    st.title("👤 My Account")
    
    current_user = get_current_user()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Profile Information")
        
        with st.form("profile_form"):
            username = st.text_input("Username", value=current_user['username'], disabled=True)
            email = st.text_input("Email", value=current_user['email'])
            full_name = st.text_input("Full Name", value=current_user.get('full_name', ''))
            
            if st.form_submit_button("Update Profile", type="primary"):
                db = SessionLocal()
                try:
                    user = db.query(User).filter(User.id == current_user['id']).first()
                    if user:
                        if validate_email(email):
                            user.email = email.strip()
                        user.full_name = full_name.strip()
                        db.commit()
                        st.session_state.current_user = user.to_dict()
                        st.success("Profile updated successfully!")
                    else:
                        st.error("User not found")
                except Exception as e:
                    db.rollback()
                    st.error(f"Error updating profile: {str(e)}")
                finally:
                    db.close()
    
    with col2:
        st.subheader("Account Status")
        st.write(f"**Role:** {'Administrator' if current_user.get('is_admin') else 'User'}")
        st.write(f"**Status:** {'Active' if current_user.get('is_active') else 'Inactive'}")
        st.write(f"**Member since:** {current_user.get('created_at', 'N/A')}")
    
    st.divider()
    
    # Alteração de senha
    st.subheader("Change Password")
    
    with st.form("password_form"):
        current_password = st.text_input("Current Password", type="password")
        new_password = st.text_input("New Password", type="password")
        confirm_password = st.text_input("Confirm New Password", type="password")
        
        if st.form_submit_button("Change Password", type="secondary"):
            if not current_password or not new_password or not confirm_password:
                st.warning("Please fill all password fields")
            elif new_password != confirm_password:
                st.error("New passwords don't match")
            elif len(new_password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                success, message = auth_system.update_user_password(
                    current_user['id'], current_password, new_password
                )
                if success:
                    st.success(message)
                else:
                    st.error(message)

# --- MAIN APP ---
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
            <h1 style='color: {COLOR_PURPLE};'>🖨️ DTF PRICING</h1>
            <p style='color: {COLOR_GRAY}; font-size: 0.8em;'>Complete Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Informações do usuário
        with st.container():
            st.write(f"👤 **{current_user['full_name'] or current_user['username']}**")
            st.write(f"📧 {current_user['email']}")
            if current_user.get('is_admin'):
                st.write("👑 **Administrator**")
            
            if st.button("🚪 Logout", use_container_width=True, type="secondary"):
                auth_system.logout_user()
                st.rerun()
        
        st.divider()
        
        # Menu de navegação
        menu_options = {
            "📱 Calculator": "calculator",
            "📦 Products": "products",
            "👥 Clients": "clientes",
            "🏭 Suppliers": "fornecedores",
            "🛒 Orders": "pedidos",
            "📋 Budgets": "orcamentos",
            "⚙️ Settings": "settings",
            "👤 My Account": "account"
        }
        
        # Verificar se é admin para mostrar settings
        if not current_user.get('is_admin'):
            menu_options.pop("⚙️ Settings", None)
        
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
            st.subheader("📊 Quick Dashboard")
            
            if pedidos_pendentes:
                st.error(f"⚠️ {len(pedidos_pendentes)} overdue orders!")
                with st.expander("View overdue orders"):
                    for p in pedidos_pendentes[:3]:  # Mostrar apenas 3
                        cliente = next((c for c in data['clientes'] if c['id'] == p.get('customer_id')), None)
                        cliente_nome = cliente['name'] if cliente else 'Unknown'
                        st.write(f"• #{p.get('order_number')} - {cliente_nome} - {formatar_moeda(p.get('total_amount', 0))}")
                    if len(pedidos_pendentes) > 3:
                        st.write(f"... and {len(pedidos_pendentes) - 3} more")
            
            if pedidos_producao:
                st.warning(f"⏳ {len(pedidos_producao)} orders in production")
                with st.expander("View production orders"):
                    for p in pedidos_producao[:3]:
                        cliente = next((c for c in data['clientes'] if c['id'] == p.get('customer_id')), None)
                        cliente_nome = cliente['name'] if cliente else 'Unknown'
                        st.write(f"• #{p.get('order_number')} - {cliente_nome}")
        
        # Informações da sessão
        st.divider()
        st.caption(f"📦 Products: {len(data['produtos'])}")
        st.caption(f"👥 Clients: {len(data['clientes'])}")
        st.caption(f"🏭 Suppliers: {len(data['fornecedores'])}")
        st.caption(f"🛒 Orders: {len(data['pedidos'])}")
        st.caption(f"📋 Budgets: {len(data['orcamentos'])}")
    
    # Conteúdo principal baseado na página atual
    page = st.session_state.get('current_page', 'calculator')
    
    if page == "calculator":
        mostrar_calculator()
    elif page == "products":
        mostrar_products()
    elif page == "clientes":
        mostrar_clientes()
    elif page == "novo_cliente":
        mostrar_novo_cliente()
    elif page == "view_cliente":
        mostrar_view_cliente()
    elif page == "edit_cliente":
        mostrar_edit_cliente()
    elif page == "fornecedores":
        mostrar_fornecedores()
    elif page == "novo_fornecedor":
        mostrar_novo_fornecedor()
    elif page == "edit_fornecedor":
        mostrar_edit_fornecedor()
    elif page == "pedidos":
        mostrar_pedidos()
    elif page == "novo_pedido":
        mostrar_novo_pedido()
    elif page == "view_pedido":
        mostrar_view_pedido()
    elif page == "orcamentos":
        mostrar_orcamentos()
    elif page == "create_budget":
        mostrar_create_budget()
    elif page == "view_budget":
        mostrar_view_budget()
    elif page == "settings":
        mostrar_settings()
    elif page == "account":
        mostrar_account()
    else:
        mostrar_calculator()

if __name__ == "__main__":
    main()
