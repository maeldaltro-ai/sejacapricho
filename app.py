import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime, timedelta
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import tempfile

# Configuração da Página
st.set_page_config(
    page_title="DTF Pricing Calculator",
    page_icon="🖨️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
@st.cache_data
def carregar_dados():
    """Carrega os dados do arquivo JSON"""
    try:
        with open('dados_sistema.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Garantir estrutura básica
            if "config" not in data:
                data["config"] = {
                    "preco_metro": 80.0,
                    "largura_rolo": 58.0,
                    "labels": {
                        "energia": "Energy (R$)",
                        "transporte": "Transport (R$)",
                        "embalagem": "Packaging (R$)"
                    },
                    "fixed_costs": {
                        "energia": 1.0,
                        "transporte": 2.0,
                        "embalagem": 1.0
                    }
                }
            if "produtos" not in data:
                data["produtos"] = []
            if "orcamentos" not in data:
                data["orcamentos"] = []
            if "clientes" not in data:
                data["clientes"] = []
            if "fornecedores" not in data:
                data["fornecedores"] = []
            if "pedidos" not in data:
                data["pedidos"] = []
            if "ultimo_numero_orcamento" not in data:
                data["ultimo_numero_orcamento"] = 0
            if "ultimo_id_cliente" not in data:
                data["ultimo_id_cliente"] = 0
            if "ultimo_id_fornecedor" not in data:
                data["ultimo_id_fornecedor"] = 0
            if "ultimo_id_pedido" not in data:
                data["ultimo_id_pedido"] = 0
            return data
    except FileNotFoundError:
        # Criar estrutura padrão se arquivo não existir
        default_data = {
            "config": {
                "preco_metro": 80.0,
                "largura_rolo": 58.0,
                "labels": {
                    "energia": "Energy (R$)",
                    "transporte": "Transport (R$)",
                    "embalagem": "Packaging (R$)"
                },
                "fixed_costs": {
                    "energia": 1.0,
                    "transporte": 2.0,
                    "embalagem": 1.0
                }
            },
            "produtos": [
                {
                    "nome": "Camisa Classic",
                    "custo": 18.99,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": True
                },
                {
                    "nome": "Cropped Algodão",
                    "custo": 24.9,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": True
                },
                {
                    "nome": "Cropped Touch",
                    "custo": 26.99,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": True
                },
                {
                    "nome": "Camisa Premium REV",
                    "custo": 34.2,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": False
                },
                {
                    "nome": "Camisa Premium",
                    "custo": 26.5,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": True
                },
                {
                    "nome": "Camisa Classic REV",
                    "custo": 30.0,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": False
                },
                {
                    "nome": "EcoBag 32x40",
                    "custo": 9.0,
                    "energia": 0.0,
                    "transp": 0.0,
                    "emb": 0.0,
                    "usa_dtf": True
                }
            ],
            "orcamentos": [],
            "clientes": [],
            "fornecedores": [],
            "pedidos": [],
            "ultimo_numero_orcamento": 0,
            "ultimo_id_cliente": 0,
            "ultimo_id_fornecedor": 0,
            "ultimo_id_pedido": 0
        }
        with open('dados_sistema.json', 'w', encoding='utf-8') as f:
            json.dump(default_data, f, indent=4)
        return default_data

def salvar_dados(data):
    """Salva os dados no arquivo JSON"""
    with open('dados_sistema.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def parse_number(value_str):
    """Converte string para número"""
    if not value_str or str(value_str).strip() == "":
        return 0.0
    try:
        cleaned = str(value_str).strip().replace(',', '.')
        return float(cleaned)
    except ValueError:
        return 0.0

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

def validar_cpf(cpf):
    """Valida CPF"""
    cpf = str(cpf).replace(".", "").replace("-", "")
    if len(cpf) != 11 or not cpf.isdigit():
        return False
    # Validar dígitos verificadores
    # Implementação básica
    return True

def validar_cnpj(cnpj):
    """Valida CNPJ"""
    cnpj = str(cnpj).replace(".", "").replace("-", "").replace("/", "")
    if len(cnpj) != 14 or not cnpj.isdigit():
        return False
    # Validar dígitos verificadores
    # Implementação básica
    return True

def get_cor_status_pedido(pedido):
    """Retorna a cor baseada no status do pedido"""
    agora = datetime.now()
    data_criacao = datetime.strptime(pedido['data_criacao'], "%d/%m/%Y %H:%M")
    
    if pedido.get('entregue', False):
        return COLOR_BLUE  # Azul para entregue
    elif pedido.get('pago', False):
        return COLOR_GREEN  # Verde para pago
    elif (agora - data_criacao) > timedelta(hours=24):
        return COLOR_RED  # Vermelho para pendente > 24h
    else:
        return COLOR_YELLOW  # Amarelo para recente

# --- TELA: CALCULATOR ---
def mostrar_calculator():
    st.title("📱 Calculator - New Estimate")
    
    # Inicializar session state se necessário
    if 'selected_products' not in st.session_state:
        st.session_state.selected_products = []
    
    data = st.session_state.data
    
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
                margem = st.number_input("Margin %", min_value=0.0, value=50.0, step=1.0)
            
            # Botão calcular
            if st.button("Calculate Price", type="primary", use_container_width=True):
                # Cálculo da área
                area_frente = frente_altura * frente_largura
                area_costas = costas_altura * costas_largura
                area_total = area_frente + area_costas
                
                # Cálculo DTF
                custo_dtf = 0
                if usa_dtf and area_total > 0:
                    preco_metro = data['config']['preco_metro']
                    largura_rolo = data['config']['largura_rolo']
                    area_metro_linear = largura_rolo * 100  # cm² por metro linear
                    custo_cm2 = preco_metro / area_metro_linear
                    custo_dtf = area_total * custo_cm2
                
                # Custos fixos
                custos_fixos = 0
                if incluir_custos_fixos:
                    custos_fixos = (produto_atual.get('energia', 0) + 
                                   produto_atual.get('transp', 0) + 
                                   produto_atual.get('emb', 0))
                    
                    # Adicionar custos fixos globais
                    cfg = data['config']['fixed_costs']
                    custos_fixos += (cfg.get('energia', 0) + 
                                    cfg.get('transporte', 0) + 
                                    cfg.get('embalagem', 0))
                
                # Cálculo final
                custo_unitario = produto_atual['custo'] + custo_dtf + custos_fixos
                preco_unitario = custo_unitario * (1 + margem / 100)
                preco_total = preco_unitario * quantidade
                
                # Armazenar resultado na session
                st.session_state.calculation_result = {
                    'produto': produto_atual['nome'],
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
def mostrar_products():
    st.title("📦 Product Management")
    
    data = st.session_state.data
    
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
                    produto_existente = None
                    for i, p in enumerate(data['produtos']):
                        if p['nome'].lower() == nome.strip().lower():
                            produto_existente = i
                            break
                    
                    novo_produto = {
                        "nome": nome.strip(),
                        "custo": custo,
                        "energia": energia,
                        "transp": transporte,
                        "emb": embalagem,
                        "usa_dtf": usa_dtf
                    }
                    
                    if produto_existente is not None:
                        data['produtos'][produto_existente] = novo_produto
                        st.success(f"Product '{nome}' updated!")
                    else:
                        data['produtos'].append(novo_produto)
                        st.success(f"Product '{nome}' added!")
                    
                    salvar_dados(data)
                    st.session_state.data = data
                    st.rerun()
                else:
                    st.error("Product name is required")
    
    # Lista de produtos
    st.subheader("Product List")
    
    if data['produtos']:
        # Criar DataFrame para exibição
        produtos_data = []
        for p in data['produtos']:
            produtos_data.append({
                "Product": p['nome'],
                "Cost": formatar_moeda(p['custo']),
                "DTF": "✓" if p['usa_dtf'] else "✗",
                "Energy": formatar_moeda(p['energia']),
                "Transport": formatar_moeda(p['transp']),
                "Packaging": formatar_moeda(p['emb'])
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
                    data['produtos'] = [p for p in data['produtos'] if p['nome'] != produto_para_gerenciar]
                    salvar_dados(data)
                    st.session_state.data = data
                    st.success(f"Product '{produto_para_gerenciar}' deleted!")
                    st.rerun()
    else:
        st.info("No products registered. Add your first product above.")

# --- TELA: ORÇAMENTOS ---
def mostrar_orcamentos():
    st.title("📋 Budgets")
    
    data = st.session_state.data
    
    # Estatísticas
    col_stats1, col_stats2, col_stats3 = st.columns(3)
    with col_stats1:
        st.metric("Total Budgets", len(data['orcamentos']))
    with col_stats2:
        st.metric("Last Number", f"#{data['ultimo_numero_orcamento']:04d}")
    with col_stats3:
        total_valor = sum(o['valor_total'] for o in data['orcamentos'])
        st.metric("Total Value", formatar_moeda(total_valor))
    
    # Botão para novo orçamento
    if st.button("+ New Budget", type="primary"):
        st.session_state.current_page = "create_budget"
        st.rerun()
    
    # Lista de orçamentos
    st.subheader("Budget List")
    
    if data['orcamentos']:
        # Ordenar por número (mais recente primeiro)
        orcamentos_ordenados = sorted(data['orcamentos'], key=lambda x: x['numero'], reverse=True)
        
        for orcamento in orcamentos_ordenados:
            with st.container():
                col_info, col_acoes = st.columns([3, 1])
                
                with col_info:
                    # Determinar produto/itens
                    if 'produto' in orcamento:
                        produto_info = orcamento['produto']
                        quantidade = orcamento.get('quantidade', 0)
                    elif 'itens' in orcamento and orcamento['itens']:
                        if len(orcamento['itens']) > 1:
                            produto_info = f"Multiple Items ({len(orcamento['itens'])})"
                        else:
                            produto_info = orcamento['itens'][0].get('nome', 'Item')
                        quantidade = sum(float(it.get('quantidade', 0)) for it in orcamento['itens'])
                    else:
                        produto_info = "No data"
                        quantidade = 0
                    
                    st.write(f"**#{orcamento['numero']:04d}** - {orcamento['data']}")
                    st.write(f"**Client:** {orcamento['cliente']}")
                    st.write(f"**Product:** {produto_info} | **Qty:** {quantidade:.0f}")
                    st.write(f"**Total:** {formatar_moeda(orcamento['valor_total'])}")
                
                with col_acoes:
                    if st.button("Open", key=f"open_{orcamento['numero']}"):
                        st.session_state.view_budget = orcamento
                        st.session_state.current_page = "view_budget"
                        st.rerun()
                    
                    if st.button("PDF", key=f"pdf_{orcamento['numero']}"):
                        # Gerar PDF
                        pdf_path = gerar_pdf(orcamento)
                        if pdf_path:
                            with open(pdf_path, "rb") as f:
                                pdf_bytes = f.read()
                            
                            st.download_button(
                                label="Download PDF",
                                data=pdf_bytes,
                                file_name=f"Orcamento_{orcamento['numero']:04d}.pdf",
                                mime="application/pdf"
                            )
                    
                    if st.button("Delete", key=f"del_{orcamento['numero']}", type="secondary"):
                        data['orcamentos'] = [o for o in data['orcamentos'] if o['numero'] != orcamento['numero']]
                        salvar_dados(data)
                        st.session_state.data = data
                        st.success(f"Budget #{orcamento['numero']:04d} deleted!")
                        st.rerun()
                
                st.divider()
    else:
        st.info("No budgets created yet. Create your first budget!")

# --- TELA: CREATE BUDGET ---
def mostrar_create_budget():
    st.title("📝 Create New Budget")
    
    data = st.session_state.data
    
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
        
        # Seção para adicionar itens manualmente (dentro do formulário)
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
            
            # Usar form_submit_button para adicionar item
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
                    
                    # Botão para remover item (usando índice único)
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
        
        # Botões de ação do formulário principal
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        
        with col_btn1:
            save_clicked = st.form_submit_button("Save Budget", type="primary", use_container_width=True, key="save_budget")
        
        with col_btn2:
            save_pdf_clicked = st.form_submit_button("Save and Generate PDF", use_container_width=True, key="save_pdf")
        
        with col_btn3:
            cancel_clicked = st.form_submit_button("Cancel", type="secondary", use_container_width=True, key="cancel_budget")
    
    # Processar ações APÓS o formulário (fora do with st.form())
    
    if cancel_clicked:
        # Limpar dados temporários
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
                # Criar novo orçamento
                novo_numero = data['ultimo_numero_orcamento'] + 1
                
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
                
                novo_orcamento = {
                    "numero": novo_numero,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "cliente": cliente.strip(),
                    "tipo_entrega": tipo_entrega,
                    "tipo_venda": tipo_venda,
                    "endereco": endereco.strip(),
                    "prazo_producao": prazo_producao,
                    "valor_total": total,
                    "observacoes": observacoes.strip(),
                    "itens": itens_para_salvar
                }
                
                # Salvar no banco de dados
                data['orcamentos'].append(novo_orcamento)
                data['ultimo_numero_orcamento'] = novo_numero
                salvar_dados(data)
                st.session_state.data = data
                
                st.success(f"✅ Budget #{novo_numero:04d} saved successfully!")
                
                # Limpar dados temporários
                if 'selected_products' in st.session_state:
                    st.session_state.selected_products = []
                if 'manual_items' in st.session_state:
                    st.session_state.manual_items = []
                
                # Gerar PDF se solicitado
                if save_pdf_clicked:
                    pdf_path = gerar_pdf(novo_orcamento)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="📄 Download PDF",
                            data=pdf_bytes,
                            file_name=f"Orcamento_{novo_numero:04d}.pdf",
                            mime="application/pdf",
                            type="primary"
                        )
                
                # Opção para ir para a lista de orçamentos
                if st.button("View Budgets List"):
                    st.session_state.current_page = "orcamentos"
                    st.rerun()

# --- TELA: VIEW BUDGET ---
def mostrar_view_budget():
    if 'view_budget' not in st.session_state:
        st.session_state.current_page = "orcamentos"
        st.rerun()
    
    orcamento = st.session_state.view_budget
    
    st.title(f"Budget #{orcamento['numero']:04d}")
    
    # Informações principais
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write(f"**Client:** {orcamento['cliente']}")
        st.write(f"**Date:** {orcamento['data']}")
        st.write(f"**Delivery Type:** {orcamento['tipo_entrega']}")
    
    with col_info2:
        st.write(f"**Sale Type:** {orcamento['tipo_venda']}")
        st.write(f"**Address:** {orcamento['endereco']}")
        st.write(f"**Deadline:** {orcamento['prazo_producao']}")
    
    # Itens
    st.subheader("Items")
    if 'itens' in orcamento and orcamento['itens']:
        itens_data = []
        for item in orcamento['itens']:
            itens_data.append({
                "Product": item.get('nome', 'Unnamed'),
                "Quantity": item.get('quantidade', 0),
                "Unit Value": formatar_moeda(item.get('valor_unitario', 0)),
                "Total": formatar_moeda(item.get('valor_unitario', 0) * item.get('quantidade', 1))
            })
        
        df = pd.DataFrame(itens_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    elif 'produto' in orcamento:
        st.write(f"**Product:** {orcamento['produto']}")
        st.write(f"**Quantity:** {orcamento.get('quantidade', 0)}")
        st.write(f"**Unit Value:** {formatar_moeda(orcamento.get('valor_unitario', 0))}")
    
    # Total
    st.metric("Total Value", formatar_moeda(orcamento['valor_total']))
    
    # Observações
    if orcamento.get('observacoes'):
        st.subheader("Observations")
        st.write(orcamento['observacoes'])
    
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
                    file_name=f"Orcamento_{orcamento['numero']:04d}.pdf",
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
def mostrar_clientes():
    st.title("👥 Clients")
    
    data = st.session_state.data
    
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
                    st.write(f"**{cliente['nome']}**")
                    if cliente.get('documento'):
                        st.write(f"**Document:** {cliente['documento']}")
                    if cliente.get('endereco'):
                        st.write(f"**Address:** {cliente['endereco']}")
                    if cliente.get('cep'):
                        st.write(f"**ZIP Code:** {cliente['cep']}")
                    
                    # Contar pedidos
                    num_pedidos = len(cliente.get('pedidos', []))
                    pedidos_pagos = sum(1 for pedido_id in cliente.get('pedidos', []) 
                                      for p in data['pedidos'] if p['id'] == pedido_id and p.get('pago', False))
                    
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
def mostrar_novo_cliente():
    st.title("👤 New Client")
    
    data = st.session_state.data
    
    with st.form("cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", placeholder="Full name")
            email = st.text_input("Email", placeholder="email@example.com")
            telefone = st.text_input("Phone", placeholder="(00) 00000-0000")
            
            tipo_documento = st.selectbox("Document Type", ["CPF", "CNPJ"])
            
            if tipo_documento == "CPF":
                documento = st.text_input("CPF *", placeholder="000.000.000-00")
                if documento:
                    documento = formatar_cpf(documento)
            else:
                documento = st.text_input("CNPJ *", placeholder="00.000.000/0000-00")
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
        elif tipo_documento == "CPF" and documento and not validar_cpf(documento):
            st.error("❌ Invalid CPF!")
        elif tipo_documento == "CNPJ" and documento and not validar_cnpj(documento):
            st.error("❌ Invalid CNPJ!")
        else:
            # Criar novo cliente
            data['ultimo_id_cliente'] += 1
            novo_cliente = {
                "id": data['ultimo_id_cliente'],
                "nome": nome.strip(),
                "email": email.strip(),
                "telefone": telefone.strip(),
                "tipo_documento": tipo_documento,
                "documento": documento.strip() if documento else "",
                "endereco": endereco.strip(),
                "cep": cep.strip(),
                "cidade": cidade.strip(),
                "estado": estado.strip(),
                "observacoes": observacoes.strip(),
                "pedidos": [],
                "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            data['clientes'].append(novo_cliente)
            salvar_dados(data)
            st.session_state.data = data
            
            st.success(f"✅ Client '{nome}' saved successfully!")
            
            if save_and_order:
                st.session_state.novo_pedido_cliente = novo_cliente
                st.session_state.current_page = "novo_pedido"
                st.rerun()
            else:
                if st.button("Back to Clients List"):
                    st.session_state.current_page = "clientes"
                    st.rerun()

# --- TELA: VIEW CLIENTE ---
def mostrar_view_cliente():
    if 'view_cliente' not in st.session_state:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    cliente = st.session_state.view_cliente
    data = st.session_state.data
    
    st.title(f"👤 {cliente['nome']}")
    
    # Abas para informações do cliente
    tab1, tab2, tab3 = st.tabs(["📋 Client Info", "🛒 Orders", "📊 Statistics"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Name:** {cliente['nome']}")
            if cliente.get('email'):
                st.write(f"**Email:** {cliente['email']}")
            if cliente.get('telefone'):
                st.write(f"**Phone:** {cliente['telefone']}")
            if cliente.get('documento'):
                st.write(f"**Document ({cliente.get('tipo_documento', '')}):** {cliente['documento']}")
        
        with col2:
            if cliente.get('endereco'):
                st.write(f"**Address:** {cliente['endereco']}")
            if cliente.get('cep'):
                st.write(f"**ZIP Code:** {cliente['cep']}")
            if cliente.get('cidade'):
                st.write(f"**City:** {cliente['cidade']}")
            if cliente.get('estado'):
                st.write(f"**State:** {cliente['estado']}")
            if cliente.get('observacoes'):
                st.write(f"**Notes:** {cliente['observacoes']}")
        
        st.write(f"**Registration Date:** {cliente.get('data_cadastro', 'N/A')}")
        
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
        pedidos_cliente = [p for p in data['pedidos'] if p['cliente_id'] == cliente['id']]
        
        if pedidos_cliente:
            # Ordenar por data (mais recente primeiro)
            pedidos_cliente.sort(key=lambda x: x['data_criacao'], reverse=True)
            
            for pedido in pedidos_cliente:
                cor = get_cor_status_pedido(pedido)
                
                with st.container():
                    st.markdown(f"""
                    <div style="border-left: 5px solid {cor}; padding-left: 10px; margin-bottom: 10px;">
                    """, unsafe_allow_html=True)
                    
                    col_info, col_status, col_acoes = st.columns([3, 2, 1])
                    
                    with col_info:
                        st.write(f"**Order #{pedido['id']}** - {pedido['data_criacao']}")
                        st.write(f"**Total:** {formatar_moeda(pedido['valor_total'])}")
                        
                        # Mostrar produtos
                        if pedido.get('itens'):
                            produtos = ", ".join([item['nome'] for item in pedido['itens'][:3]])
                            if len(pedido['itens']) > 3:
                                produtos += f" (+{len(pedido['itens']) - 3} more)"
                            st.write(f"**Products:** {produtos}")
                    
                    with col_status:
                        # Status de pagamento
                        if pedido.get('pago', False):
                            st.write("🟢 **Paid**")
                            if pedido.get('forma_pagamento'):
                                st.write(f"({pedido['forma_pagamento']})")
                        else:
                            st.write("🔴 **Pending Payment**")
                        
                        # Status de entrega
                        if pedido.get('entregue', False):
                            st.write("✓ **Delivered**")
                        else:
                            st.write("⏳ **In Production**")
                    
                    with col_acoes:
                        if st.button("View", key=f"view_pedido_{pedido['id']}"):
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
        pedidos_cliente = [p for p in data['pedidos'] if p['cliente_id'] == cliente['id']]
        
        if pedidos_cliente:
            col_stat1, col_stat2, col_stat3 = st.columns(3)
            
            with col_stat1:
                total_pedidos = len(pedidos_cliente)
                st.metric("Total Orders", total_pedidos)
            
            with col_stat2:
                pedidos_pagos = sum(1 for p in pedidos_cliente if p.get('pago', False))
                st.metric("Paid Orders", pedidos_pagos)
            
            with col_stat3:
                pedidos_entregues = sum(1 for p in pedidos_cliente if p.get('entregue', False))
                st.metric("Delivered Orders", pedidos_entregues)
            
            # Valor total gasto
            valor_total = sum(p['valor_total'] for p in pedidos_cliente)
            st.metric("Total Spent", formatar_moeda(valor_total))
            
            # Último pedido
            ultimo_pedido = max(pedidos_cliente, key=lambda x: x['data_criacao'])
            st.write(f"**Last Order:** #{ultimo_pedido['id']} - {ultimo_pedido['data_criacao']}")
            st.write(f"**Status:** {'Paid' if ultimo_pedido.get('pago', False) else 'Pending'} | {'Delivered' if ultimo_pedido.get('entregue', False) else 'In Production'}")
        else:
            st.info("No statistics available - client has no orders yet.")

# --- TELA: EDIT CLIENTE ---
def mostrar_edit_cliente():
    if 'edit_cliente' not in st.session_state:
        st.session_state.current_page = "clientes"
        st.rerun()
    
    cliente = st.session_state.edit_cliente
    data = st.session_state.data
    
    st.title(f"✏️ Edit Client: {cliente['nome']}")
    
    with st.form("edit_cliente_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", value=cliente.get('nome', ''), placeholder="Full name")
            email = st.text_input("Email", value=cliente.get('email', ''), placeholder="email@example.com")
            telefone = st.text_input("Phone", value=cliente.get('telefone', ''), placeholder="(00) 00000-0000")
            
            tipo_documento = st.selectbox("Document Type", ["CPF", "CNPJ"], 
                                         index=0 if cliente.get('tipo_documento') == 'CPF' else 1)
            
            if tipo_documento == "CPF":
                documento = st.text_input("CPF", value=cliente.get('documento', ''), placeholder="000.000.000-00")
                if documento:
                    documento = formatar_cpf(documento)
            else:
                documento = st.text_input("CNPJ", value=cliente.get('documento', ''), placeholder="00.000.000/0000-00")
                if documento:
                    documento = formatar_cnpj(documento)
        
        with col2:
            endereco = st.text_area("Address", value=cliente.get('endereco', ''), 
                                   placeholder="Street, Number, Neighborhood")
            cep = st.text_input("ZIP Code", value=cliente.get('cep', ''), placeholder="00000-000")
            cidade = st.text_input("City", value=cliente.get('cidade', ''), placeholder="City")
            estado = st.text_input("State", value=cliente.get('estado', ''), placeholder="State", max_chars=2)
            observacoes = st.text_area("Notes", value=cliente.get('observacoes', ''), 
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
            # Atualizar cliente
            for i, c in enumerate(data['clientes']):
                if c['id'] == cliente['id']:
                    data['clientes'][i].update({
                        "nome": nome.strip(),
                        "email": email.strip(),
                        "telefone": telefone.strip(),
                        "tipo_documento": tipo_documento,
                        "documento": documento.strip() if documento else "",
                        "endereco": endereco.strip(),
                        "cep": cep.strip(),
                        "cidade": cidade.strip(),
                        "estado": estado.strip(),
                        "observacoes": observacoes.strip()
                    })
                    break
            
            salvar_dados(data)
            st.session_state.data = data
            st.success(f"✅ Client '{nome}' updated successfully!")
            
            if st.button("Back to Client"):
                del st.session_state.edit_cliente
                st.session_state.view_cliente = next((c for c in data['clientes'] if c['id'] == cliente['id']), None)
                st.session_state.current_page = "view_cliente"
                st.rerun()

# --- TELA: FORNECEDORES ---
def mostrar_fornecedores():
    st.title("🏭 Suppliers")
    
    data = st.session_state.data
    
    # Estatísticas
    col_stats1, col_stats2 = st.columns(2)
    with col_stats1:
        st.metric("Total Suppliers", len(data['fornecedores']))
    with col_stats2:
        tipos = set(f.get('tipo', '') for f in data['fornecedores'])
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
            tipo = fornecedor.get('tipo', 'Outros')
            if tipo not in fornecedores_por_tipo:
                fornecedores_por_tipo[tipo] = []
            fornecedores_por_tipo[tipo].append(fornecedor)
        
        for tipo, fornecedores in fornecedores_por_tipo.items():
            with st.expander(f"{tipo} ({len(fornecedores)})", expanded=True):
                for fornecedor in fornecedores:
                    with st.container():
                        col_info, col_acoes = st.columns([3, 1])
                        
                        with col_info:
                            st.write(f"**{fornecedor['nome']}**")
                            if fornecedor.get('nome_fantasia'):
                                st.write(f"**Trade Name:** {fornecedor['nome_fantasia']}")
                            if fornecedor.get('documento'):
                                st.write(f"**Document:** {fornecedor['documento']}")
                            if fornecedor.get('endereco'):
                                st.write(f"**Address:** {fornecedor['endereco']}")
                            if fornecedor.get('observacoes'):
                                st.write(f"**Notes:** {fornecedor['observacoes']}")
                        
                        with col_acoes:
                            if st.button("Edit", key=f"edit_fornecedor_{fornecedor['id']}"):
                                st.session_state.edit_fornecedor = fornecedor
                                st.session_state.current_page = "edit_fornecedor"
                                st.rerun()
                        
                        st.divider()
    else:
        st.info("No suppliers registered. Create your first supplier!")

# --- TELA: NOVO FORNECEDOR ---
def mostrar_novo_fornecedor():
    st.title("🏭 New Supplier")
    
    data = st.session_state.data
    
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
            # Criar novo fornecedor
            data['ultimo_id_fornecedor'] += 1
            novo_fornecedor = {
                "id": data['ultimo_id_fornecedor'],
                "nome": nome.strip(),
                "nome_fantasia": nome_fantasia.strip(),
                "tipo": tipo,
                "tipo_documento": tipo_documento if tipo_documento != "None" else "",
                "documento": documento.strip(),
                "endereco": endereco.strip(),
                "telefone": telefone.strip(),
                "email": email.strip(),
                "observacoes": observacoes.strip(),
                "data_cadastro": datetime.now().strftime("%d/%m/%Y %H:%M")
            }
            
            data['fornecedores'].append(novo_fornecedor)
            salvar_dados(data)
            st.session_state.data = data
            
            st.success(f"✅ Supplier '{nome}' saved successfully!")
            
            if st.button("Back to Suppliers List"):
                st.session_state.current_page = "fornecedores"
                st.rerun()

# --- TELA: EDIT FORNECEDOR ---
def mostrar_edit_fornecedor():
    if 'edit_fornecedor' not in st.session_state:
        st.session_state.current_page = "fornecedores"
        st.rerun()
    
    fornecedor = st.session_state.edit_fornecedor
    data = st.session_state.data
    
    st.title(f"✏️ Edit Supplier: {fornecedor['nome']}")
    
    with st.form("edit_fornecedor_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome = st.text_input("Name *", value=fornecedor.get('nome', ''), placeholder="Company name")
            nome_fantasia = st.text_input("Trade Name", value=fornecedor.get('nome_fantasia', ''), 
                                         placeholder="Trade name (optional)")
            
            tipo = st.selectbox("Type", ["Camisaria", "Serviços", "Canecas e Brindes", 
                                        "DTF e Estamparia", "Acessórios", "Outros"],
                               index=["Camisaria", "Serviços", "Canecas e Brindes", 
                                     "DTF e Estamparia", "Acessórios", "Outros"].index(
                                         fornecedor.get('tipo', 'Outros')))
            
            tipo_documento_atual = fornecedor.get('tipo_documento', 'None')
            tipo_documento = st.selectbox("Document Type", ["None", "CPF", "CNPJ"],
                                         index=["None", "CPF", "CNPJ"].index(
                                             tipo_documento_atual if tipo_documento_atual in ["None", "CPF", "CNPJ"] else "None"))
            
            if tipo_documento != "None":
                if tipo_documento == "CPF":
                    documento = st.text_input("CPF", value=fornecedor.get('documento', ''), 
                                             placeholder="000.000.000-00")
                    if documento:
                        documento = formatar_cpf(documento)
                else:
                    documento = st.text_input("CNPJ", value=fornecedor.get('documento', ''), 
                                             placeholder="00.000.000/0000-00")
                    if documento:
                        documento = formatar_cnpj(documento)
            else:
                documento = ""
        
        with col2:
            endereco = st.text_area("Address", value=fornecedor.get('endereco', ''), 
                                   placeholder="Full address")
            telefone = st.text_input("Phone", value=fornecedor.get('telefone', ''), 
                                    placeholder="(00) 00000-0000")
            email = st.text_input("Email", value=fornecedor.get('email', ''), 
                                 placeholder="email@example.com")
            observacoes = st.text_area("Notes", value=fornecedor.get('observacoes', ''), 
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
            # Atualizar fornecedor
            for i, f in enumerate(data['fornecedores']):
                if f['id'] == fornecedor['id']:
                    data['fornecedores'][i].update({
                        "nome": nome.strip(),
                        "nome_fantasia": nome_fantasia.strip(),
                        "tipo": tipo,
                        "tipo_documento": tipo_documento if tipo_documento != "None" else "",
                        "documento": documento.strip(),
                        "endereco": endereco.strip(),
                        "telefone": telefone.strip(),
                        "email": email.strip(),
                        "observacoes": observacoes.strip()
                    })
                    break
            
            salvar_dados(data)
            st.session_state.data = data
            st.success(f"✅ Supplier '{nome}' updated successfully!")
            
            if st.button("Back to Suppliers"):
                del st.session_state.edit_fornecedor
                st.session_state.current_page = "fornecedores"
                st.rerun()

# --- TELA: PEDIDOS ---
def mostrar_pedidos():
    st.title("🛒 Orders")
    
    data = st.session_state.data
    
    # Estatísticas
    pedidos_pendentes = sum(1 for p in data['pedidos'] if not p.get('pago', False))
    pedidos_pagos = sum(1 for p in data['pedidos'] if p.get('pago', False))
    pedidos_entregues = sum(1 for p in data['pedidos'] if p.get('entregue', False))
    
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
        clientes_nomes = ["All"] + [c['nome'] for c in data['clientes']]
        filtro_cliente = st.selectbox("Client", clientes_nomes)
    
    # Lista de pedidos
    st.subheader("Order List")
    
    if data['pedidos']:
        # Ordenar por data (mais recente primeiro)
        pedidos_ordenados = sorted(data['pedidos'], key=lambda x: x['data_criacao'], reverse=True)
        
        # Aplicar filtros
        pedidos_filtrados = []
        for pedido in pedidos_ordenados:
            # Filtro de status de pagamento
            if "All" not in filtro_status:
                status_pagamento = "Paid" if pedido.get('pago', False) else "Pending"
                if status_pagamento not in filtro_status:
                    continue
            
            # Filtro de status de entrega
            if "All" not in filtro_entrega:
                status_entrega = "Delivered" if pedido.get('entregue', False) else "Pending"
                if status_entrega not in filtro_entrega:
                    continue
            
            # Filtro por cliente
            if filtro_cliente != "All":
                cliente = next((c for c in data['clientes'] if c['id'] == pedido['cliente_id']), None)
                if not cliente or cliente['nome'] != filtro_cliente:
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
                            if cliente['id'] == pedido['cliente_id']:
                                cliente_nome = cliente['nome']
                                break
                        
                        st.write(f"**Order #{pedido['id']}** - {pedido['data_criacao']}")
                        st.write(f"**Client:** {cliente_nome}")
                        st.write(f"**Total:** {formatar_moeda(pedido['valor_total'])}")
                        
                        # Mostrar produtos
                        if pedido.get('itens'):
                            produtos = ", ".join([item['nome'] for item in pedido['itens'][:2]])
                            if len(pedido['itens']) > 2:
                                produtos += f" (+{len(pedido['itens']) - 2} more)"
                            st.write(f"**Products:** {produtos}")
                    
                    with col_status:
                        # Status de pagamento
                        if pedido.get('pago', False):
                            st.write("🟢 **Paid**")
                            if pedido.get('forma_pagamento'):
                                st.write(f"({pedido['forma_pagamento']})")
                        else:
                            # Verificar se está atrasado
                            data_criacao = datetime.strptime(pedido['data_criacao'], "%d/%m/%Y %H:%M")
                            if (datetime.now() - data_criacao) > timedelta(hours=24):
                                st.write("🔴 **Overdue Payment**")
                            else:
                                st.write("🟡 **Pending Payment**")
                        
                        # Status de entrega
                        if pedido.get('entregue', False):
                            st.write("✓ **Delivered**")
                        else:
                            st.write("⏳ **In Production**")
                    
                    with col_acoes:
                        if st.button("View", key=f"view_pedido_main_{pedido['id']}"):
                            st.session_state.view_pedido = pedido
                            st.session_state.current_page = "view_pedido"
                            st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.divider()
    else:
        st.info("No orders created yet. Create your first order!")

# --- TELA: NOVO PEDIDO ---
def mostrar_novo_pedido():
    st.title("🛒 New Order")
    
    data = st.session_state.data
    
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
            clientes_options = [c['nome'] for c in data['clientes']]
            
            if st.session_state.get('novo_pedido_cliente'):
                cliente_pre_selecionado = st.session_state.novo_pedido_cliente['nome']
                cliente_selecionado = st.selectbox("Client *", clientes_options, 
                                                  index=clientes_options.index(cliente_pre_selecionado) 
                                                  if cliente_pre_selecionado in clientes_options else 0)
            else:
                cliente_selecionado = st.selectbox("Client *", clientes_options)
            
            # Obter cliente selecionado
            cliente_atual = None
            for c in data['clientes']:
                if c['nome'] == cliente_selecionado:
                    cliente_atual = c
                    break
            
            if cliente_atual:
                st.write(f"**Document:** {cliente_atual.get('documento', 'N/A')}")
                st.write(f"**Address:** {cliente_atual.get('endereco', 'N/A')}")
                if cliente_atual.get('telefone'):
                    st.write(f"**Phone:** {cliente_atual['telefone']}")
            
            prazo_entrega = st.text_input("Delivery Deadline", value="5 dias úteis")
        
        with col2:
            tipo_entrega = st.radio("Delivery Type", ["Pronta Entrega", "Sob Encomenda"])
            forma_pagamento = st.selectbox("Payment Method", 
                                          ["Not Defined", "Cash", "Credit Card", 
                                           "Debit Card", "PIX", "Bank Transfer"])
            observacoes = st.text_area("Observations", placeholder="Additional information")
        
        # Seção para adicionar produtos (similar à calculadora)
        st.subheader("Add Products")
        
        col_prod1, col_prod2, col_prod3 = st.columns(3)
        with col_prod1:
            produto_selecionado = st.selectbox("Product", 
                                              ["Apenas DTF"] + [p['nome'] for p in data['produtos']])
        
        with col_prod2:
            quantidade = st.number_input("Quantity", min_value=1, value=1)
        
        with col_prod3:
            # Se for um produto da lista, mostrar custo estimado
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
            
            # Criar novo pedido
            data['ultimo_id_pedido'] += 1
            
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
            
            novo_pedido = {
                "id": data['ultimo_id_pedido'],
                "cliente_id": cliente_atual['id'],
                "data_criacao": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "tipo_entrega": tipo_entrega,
                "prazo_entrega": prazo_entrega,
                "forma_pagamento": forma_pagamento if forma_pagamento != "Not Defined" else "",
                "valor_total": total,
                "observacoes": observacoes.strip(),
                "itens": itens_para_salvar,
                "pago": False,
                "entregue": False,
                "data_pagamento": None,
                "data_entrega": None
            }
            
            # Adicionar pedido ao cliente
            for cliente in data['clientes']:
                if cliente['id'] == cliente_atual['id']:
                    if 'pedidos' not in cliente:
                        cliente['pedidos'] = []
                    cliente['pedidos'].append(data['ultimo_id_pedido'])
                    break
            
            # Salvar pedido
            data['pedidos'].append(novo_pedido)
            salvar_dados(data)
            st.session_state.data = data
            
            st.success(f"✅ Order #{data['ultimo_id_pedido']} saved successfully!")
            
            # Limpar dados temporários
            if 'selected_products' in st.session_state:
                st.session_state.selected_products = []
            if 'manual_items' in st.session_state:
                st.session_state.manual_items = []
            if 'novo_pedido_cliente' in st.session_state:
                del st.session_state.novo_pedido_cliente
            
            # Gerar nota fiscal se solicitado
            if save_pdf_clicked:
                pdf_path = gerar_nota_fiscal(novo_pedido, cliente_atual)
                if pdf_path:
                    with open(pdf_path, "rb") as f:
                        pdf_bytes = f.read()
                    
                    st.download_button(
                        label="📄 Download Invoice",
                        data=pdf_bytes,
                        file_name=f"Nota_Ordem_{novo_pedido['id']}.pdf",
                        mime="application/pdf",
                        type="primary"
                    )
            
            # Opção para ir para a lista de pedidos
            if st.button("View Orders List"):
                st.session_state.current_page = "pedidos"
                st.rerun()

# --- TELA: VIEW PEDIDO ---
def mostrar_view_pedido():
    if 'view_pedido' not in st.session_state:
        st.session_state.current_page = "pedidos"
        st.rerun()
    
    pedido = st.session_state.view_pedido
    data = st.session_state.data
    
    # Obter cliente
    cliente = next((c for c in data['clientes'] if c['id'] == pedido['cliente_id']), None)
    
    st.title(f"🛒 Order #{pedido['id']}")
    
    # Informações principais
    col_info1, col_info2 = st.columns(2)
    
    with col_info1:
        st.write(f"**Client:** {cliente['nome'] if cliente else 'Unknown'}")
        st.write(f"**Creation Date:** {pedido['data_criacao']}")
        st.write(f"**Delivery Type:** {pedido['tipo_entrega']}")
        st.write(f"**Delivery Deadline:** {pedido['prazo_entrega']}")
    
    with col_info2:
        st.write(f"**Payment Method:** {pedido.get('forma_pagamento', 'Not defined')}")
        if pedido.get('data_pagamento'):
            st.write(f"**Payment Date:** {pedido['data_pagamento']}")
        if pedido.get('data_entrega'):
            st.write(f"**Delivery Date:** {pedido['data_entrega']}")
    
    # Status
    col_status1, col_status2 = st.columns(2)
    
    with col_status1:
        if pedido.get('pago', False):
            st.success("✅ **PAID**")
        else:
            st.error("❌ **PENDING PAYMENT**")
    
    with col_status2:
        if pedido.get('entregue', False):
            st.success("✅ **DELIVERED**")
        else:
            st.warning("⏳ **IN PRODUCTION**")
    
    # Itens
    st.subheader("Items")
    if pedido.get('itens'):
        itens_data = []
        for item in pedido['itens']:
            itens_data.append({
                "Product": item.get('nome', 'Unnamed'),
                "Quantity": item.get('quantidade', 0),
                "Unit Value": formatar_moeda(item.get('valor_unitario', 0)),
                "Total": formatar_moeda(item.get('valor_unitario', 0) * item.get('quantidade', 1))
            })
        
        df = pd.DataFrame(itens_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    # Total
    st.metric("Total Value", formatar_moeda(pedido['valor_total']))
    
    # Observações
    if pedido.get('observacoes'):
        st.subheader("Observations")
        st.write(pedido['observacoes'])
    
    # Controles de status
    st.subheader("Update Status")
    
    col_status_btn1, col_status_btn2, col_status_btn3 = st.columns(3)
    
    with col_status_btn1:
        if not pedido.get('pago', False):
            if st.button("Mark as Paid", type="primary", use_container_width=True):
                # Mostrar opções de pagamento
                st.session_state.pagar_pedido = pedido
                st.rerun()
        else:
            st.info("Order already paid")
    
    with col_status_btn2:
        if not pedido.get('entregue', False):
            if st.button("Mark as Delivered", use_container_width=True):
                for i, p in enumerate(data['pedidos']):
                    if p['id'] == pedido['id']:
                        data['pedidos'][i]['entregue'] = True
                        data['pedidos'][i]['data_entrega'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        break
                salvar_dados(data)
                st.session_state.data = data
                st.success("✅ Order marked as delivered!")
                st.rerun()
        else:
            st.info("Order already delivered")
    
    with col_status_btn3:
        if st.button("Generate Invoice", type="secondary", use_container_width=True):
            pdf_path = gerar_nota_fiscal(pedido, cliente)
            if pdf_path:
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                
                st.download_button(
                    label="Download Invoice",
                    data=pdf_bytes,
                    file_name=f"Nota_Ordem_{pedido['id']}.pdf",
                    mime="application/pdf"
                )
    
    # Seção para marcar como pago
    if st.session_state.get('pagar_pedido') == pedido:
        st.subheader("Confirm Payment")
        
        forma_pagamento = st.selectbox("Payment Method", 
                                      ["Cash", "Credit Card", "Debit Card", "PIX", "Bank Transfer"])
        
        col_confirm1, col_confirm2 = st.columns(2)
        
        with col_confirm1:
            if st.button("Confirm Payment", type="primary", use_container_width=True):
                for i, p in enumerate(data['pedidos']):
                    if p['id'] == pedido['id']:
                        data['pedidos'][i]['pago'] = True
                        data['pedidos'][i]['forma_pagamento'] = forma_pagamento
                        data['pedidos'][i]['data_pagamento'] = datetime.now().strftime("%d/%m/%Y %H:%M")
                        break
                salvar_dados(data)
                st.session_state.data = data
                del st.session_state.pagar_pedido
                st.success("✅ Payment confirmed!")
                st.rerun()
        
        with col_confirm2:
            if st.button("Cancel", type="secondary", use_container_width=True):
                del st.session_state.pagar_pedido
                st.rerun()
    
    # Botão para voltar
    if st.button("Back to Orders List", type="secondary", use_container_width=True):
        del st.session_state.view_pedido
        if 'pagar_pedido' in st.session_state:
            del st.session_state.pagar_pedido
        st.session_state.current_page = "pedidos"
        st.rerun()

# --- TELA: SETTINGS ---
def mostrar_settings():
    st.title("⚙️ Settings")
    
    data = st.session_state.data
    config = data['config']
    
    # DTF Costs
    st.subheader("DTF Costs")
    col_dtf1, col_dtf2 = st.columns(2)
    
    with col_dtf1:
        preco_metro = st.number_input("Price per Meter (R$)", 
                                    value=config['preco_metro'], 
                                    min_value=0.0, step=0.1)
    
    with col_dtf2:
        largura_rolo = st.number_input("Roll Width (cm)", 
                                     value=config['largura_rolo'], 
                                     min_value=0.0, step=0.1)
    
    # Custom Labels and Fixed Costs
    st.subheader("Custom Labels and Fixed Costs")
    
    col_label1, col_label2, col_label3 = st.columns(3)
    
    with col_label1:
        st.write("**Energy**")
        label_energia = st.text_input("Label", value=config['labels']['energia'], key="label_energia")
        valor_energia = st.number_input("Value (R$)", value=config['fixed_costs']['energia'], 
                                       min_value=0.0, step=0.1, key="val_energia")
    
    with col_label2:
        st.write("**Transport**")
        label_transporte = st.text_input("Label", value=config['labels']['transporte'], key="label_transporte")
        valor_transporte = st.number_input("Value (R$)", value=config['fixed_costs']['transporte'], 
                                          min_value=0.0, step=0.1, key="val_transporte")
    
    with col_label3:
        st.write("**Packaging**")
        label_embalagem = st.text_input("Label", value=config['labels']['embalagem'], key="label_embalagem")
        valor_embalagem = st.number_input("Value (R$)", value=config['fixed_costs']['embalagem'], 
                                         min_value=0.0, step=0.1, key="val_embalagem")
    
    # Botão salvar
    if st.button("Save All Settings", type="primary", use_container_width=True):
        # Atualizar configurações
        config['preco_metro'] = preco_metro
        config['largura_rolo'] = largura_rolo
        config['labels']['energia'] = label_energia
        config['labels']['transporte'] = label_transporte
        config['labels']['embalagem'] = label_embalagem
        config['fixed_costs']['energia'] = valor_energia
        config['fixed_costs']['transporte'] = valor_transporte
        config['fixed_costs']['embalagem'] = valor_embalagem
        
        # Salvar
        salvar_dados(data)
        st.session_state.data = data
        st.success("Settings saved successfully!")

# --- FUNÇÃO PARA GERAR NOTA FISCAL ---
def gerar_nota_fiscal(pedido, cliente):
    """Gera nota fiscal para um pedido"""
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
        title = Paragraph(f"NOTA FISCAL - ORDEM #{pedido['id']}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Informações da empresa
        empresa_info = [
            ["SEJA CAPRICHO", ""],
            ["Criatividade, Personalidade e muito Capricho!", ""],
            ["(75) 9155-5968 | @sejacapricho | sejacapricho.com.br", ""],
            [f"Data: {pedido['data_criacao']}", f"Ordem: #{pedido['id']}"]
        ]
        
        empresa_table = Table(empresa_info, colWidths=[doc.width/2.0]*2)
        empresa_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        elements.append(empresa_table)
        elements.append(Spacer(1, 20))
        
        # Dados do Cliente
        cliente_data = [
            ["DADOS DO CLIENTE", ""],
            ["Cliente:", cliente['nome']],
            ["Documento:", cliente.get('documento', '')],
            ["Endereço:", cliente.get('endereco', '')],
            ["CEP:", cliente.get('cep', '')],
            ["Cidade/Estado:", f"{cliente.get('cidade', '')}/{cliente.get('estado', '')}"],
            ["Telefone:", cliente.get('telefone', '')],
            ["Email:", cliente.get('email', '')]
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
        
        if 'itens' in pedido:
            for item in pedido['itens']:
                item_total = float(item.get('valor_unitario', 0)) * float(item.get('quantidade', 0))
                items_data.append([
                    item.get('nome', ''),
                    f"{item.get('quantidade', 0):.0f}",
                    f"R$ {item.get('valor_unitario', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    f"R$ {item_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
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
            ["RESUMO DO PEDIDO", ""],
            ["Tipo de Entrega:", pedido['tipo_entrega']],
            ["Prazo de Entrega:", pedido['prazo_entrega']],
            ["Forma de Pagamento:", pedido.get('forma_pagamento', 'A combinar')],
            ["Status Pagamento:", "PAGO" if pedido.get('pago', False) else "PENDENTE"],
            ["Status Entrega:", "ENTREGUE" if pedido.get('entregue', False) else "EM PRODUÇÃO"],
            ["", ""],
            ["VALOR TOTAL:", f"R$ {pedido['valor_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")]
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
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('PADDING', (0, 1), (-1, -2), 6),
            ('BACKGROUND', (1, 7), (1, 7), colors.HexColor('#f0f8ff')),
            ('FONTSIZE', (0, 7), (1, 7), 12),
            ('FONTNAME', (0, 7), (0, 7), 'Helvetica-Bold'),
            ('ALIGN', (1, 7), (1, 7), 'RIGHT'),
        ]))
        
        elements.append(resumo_table)
        
        # Observações (se existirem)
        if pedido.get('observacoes'):
            elements.append(Spacer(1, 20))
            obs_data = [
                ["OBSERVAÇÕES"],
                [pedido['observacoes']]
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
            "1. Este documento não é uma nota fiscal oficial, mas sim um comprovante de ordem de serviço.<br/>"
            "2. O prazo de produção começa a contar após a confirmação do pedido e pagamento.<br/>"
            "3. Para dúvidas ou alterações, entre em contato com nossa equipe.<br/>"
            "4. Agradecemos pela preferência!",
            ParagraphStyle(
                'Rodape',
                parent=styles['Normal'],
                fontSize=9,
                alignment=TA_CENTER,
                textColor=colors.gray
            )
        )
        elements.append(rodape)
        
        # Assinaturas
        elements.append(Spacer(1, 40))
        assinaturas_data = [
            ["", "", ""],
            ["________________________________", "________________________________", "________________________________"],
            ["Cliente", "Responsável", "Data de Entrega"]
        ]
        
        assinaturas_table = Table(assinaturas_data, colWidths=[doc.width/3.0]*3)
        assinaturas_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(assinaturas_table)
        
        # Construir PDF
        doc.build(elements)
        return pdf_path
        
    except Exception as e:
        st.error(f"Error generating invoice: {str(e)}")
        return None

# --- FUNÇÃO PARA GERAR PDF (ORÇAMENTO) ---
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
        title = Paragraph(f"ORÇAMENTO #{orcamento['numero']:04d}", title_style)
        elements.append(title)
        elements.append(Spacer(1, 12))
        
        # Informações da empresa
        empresa_info = [
            ["Criatividade, Personalidade e muito Capricho!", ""],
            ["DTF Pricing Calculator", ""],
            [f"Data: {orcamento['data']}", ""]
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
            ["Cliente:", orcamento['cliente']],
            ["Endereço:", orcamento['endereco']],
            ["Tipo de Entrega:", orcamento['tipo_entrega']],
            ["Tipo de Venda:", orcamento['tipo_venda']],
            ["Prazo de Produção:", orcamento['prazo_producao']]
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
        
        if 'itens' in orcamento:
            for item in orcamento['itens']:
                item_total = float(item.get('valor_unitario', 0)) * float(item.get('quantidade', 0))
                items_data.append([
                    item.get('nome', ''),
                    f"{item.get('quantidade', 0):.0f}",
                    f"R$ {item.get('valor_unitario', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                    f"R$ {item_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                ])
        elif 'produto' in orcamento:
            items_data.append([
                orcamento['produto'],
                f"{orcamento.get('quantidade', 0):.0f}",
                f"R$ {orcamento.get('valor_unitario', 0):,.2f}".replace(",", "X").replace(".", ",").replace("X", "."),
                f"R$ {orcamento['valor_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
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
            ["Valor Total:", f"R$ {orcamento['valor_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")]
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
        if orcamento.get('observacoes'):
            elements.append(Spacer(1, 20))
            obs_data = [
                ["OBSERVAÇÕES"],
                [orcamento['observacoes']]
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

# --- MAIN APP ---
def main():
    # Inicializar session state
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "calculator"
    
    if 'data' not in st.session_state:
        st.session_state.data = carregar_dados()
    
    # Barra lateral - Menu de Navegação
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align: center; margin-bottom: 30px;'>
            <h1 style='color: {COLOR_PURPLE};'>🖨️ DTF PRICING</h1>
            <p style='color: {COLOR_GRAY}; font-size: 0.8em;'>Complete Management System</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu de navegação
        menu_options = {
            "📱 Calculator": "calculator",
            "📦 Products": "products",
            "👥 Clients": "clientes",
            "🏭 Suppliers": "fornecedores",
            "🛒 Orders": "pedidos",
            "📋 Budgets": "orcamentos",
            "⚙️ Settings": "settings"
        }
        
        for label, page in menu_options.items():
            if st.button(label, 
                        use_container_width=True,
                        type="primary" if st.session_state.current_page == page else "secondary"):
                st.session_state.current_page = page
                st.rerun()
        
        st.divider()
        
        # Dashboard rápido (pendências)
        if st.session_state.data:
            # Contar pedidos pendentes
            pedidos_pendentes = sum(1 for p in st.session_state.data['pedidos'] 
                                  if not p.get('pago', False) and 
                                  (datetime.now() - datetime.strptime(p['data_criacao'], "%d/%m/%Y %H:%M")) > timedelta(hours=24))
            
            pedidos_recentes = sum(1 for p in st.session_state.data['pedidos'] 
                                 if not p.get('pago', False) and 
                                 (datetime.now() - datetime.strptime(p['data_criacao'], "%d/%m/%Y %H:%M")) <= timedelta(hours=24))
            
            if pedidos_pendentes > 0 or pedidos_recentes > 0:
                st.subheader("📊 Quick Dashboard")
                
                if pedidos_pendentes > 0:
                    st.error(f"⚠️ {pedidos_pendentes} overdue orders!")
                
                if pedidos_recentes > 0:
                    st.warning(f"⏳ {pedidos_recentes} recent orders")
        
        # Informações da sessão
        if st.session_state.data:
            st.divider()
            st.caption(f"Products: {len(st.session_state.data['produtos'])}")
            st.caption(f"Clients: {len(st.session_state.data['clientes'])}")
            st.caption(f"Suppliers: {len(st.session_state.data['fornecedores'])}")
            st.caption(f"Orders: {len(st.session_state.data['pedidos'])}")
            st.caption(f"Budgets: {len(st.session_state.data['orcamentos'])}")
    
    # Conteúdo principal baseado na página atual
    if st.session_state.current_page == "calculator":
        mostrar_calculator()
    elif st.session_state.current_page == "products":
        mostrar_products()
    elif st.session_state.current_page == "clientes":
        mostrar_clientes()
    elif st.session_state.current_page == "novo_cliente":
        mostrar_novo_cliente()
    elif st.session_state.current_page == "view_cliente":
        mostrar_view_cliente()
    elif st.session_state.current_page == "edit_cliente":
        mostrar_edit_cliente()
    elif st.session_state.current_page == "fornecedores":
        mostrar_fornecedores()
    elif st.session_state.current_page == "novo_fornecedor":
        mostrar_novo_fornecedor()
    elif st.session_state.current_page == "edit_fornecedor":
        mostrar_edit_fornecedor()
    elif st.session_state.current_page == "pedidos":
        mostrar_pedidos()
    elif st.session_state.current_page == "novo_pedido":
        mostrar_novo_pedido()
    elif st.session_state.current_page == "view_pedido":
        mostrar_view_pedido()
    elif st.session_state.current_page == "orcamentos":
        mostrar_orcamentos()
    elif st.session_state.current_page == "create_budget":
        mostrar_create_budget()
    elif st.session_state.current_page == "view_budget":
        mostrar_view_budget()
    elif st.session_state.current_page == "settings":
        mostrar_settings()

if __name__ == "__main__":
    main()
