import streamlit as st
import json
import pandas as pd
import os
from datetime import datetime
import math
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import tempfile
import base64

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
            if "ultimo_numero_orcamento" not in data:
                data["ultimo_numero_orcamento"] = 0
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
            "ultimo_numero_orcamento": 0
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
            if st.button("📋 Create Budget", type="primary", use_container_width=True):
                st.session_state.current_page = "create_budget"
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
    
    # Formulário do orçamento
    with st.form("budget_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            cliente = st.text_input("Client *", placeholder="Client name")
            endereco = st.text_area("Address", placeholder="Full address")
            tipo_entrega = st.radio("Delivery Type", ["Ready Delivery", "Custom Order"])
            prazo_producao = st.text_input("Production Deadline", value="5 business days")
        
        with col2:
            data_orcamento = st.date_input("Date", value=datetime.now())
            tipo_venda = st.radio("Sale Type", ["Resale", "Customized"])
            observacoes = st.text_area("Observations", placeholder="Additional information")
        
        # Itens do orçamento
        st.subheader("Items")
        
        # Usar produtos da calculadora ou adicionar novos
        if st.session_state.get('selected_products'):
            st.info(f"{len(st.session_state.selected_products)} products from calculator")
            for i, item in enumerate(st.session_state.selected_products):
                col_item1, col_item2, col_item3 = st.columns([3, 1, 1])
                with col_item1:
                    st.write(f"**{item['nome']}**")
                with col_item2:
                    st.write(f"Qty: {item['quantidade']}")
                with col_item3:
                    st.write(f"Unit: {formatar_moeda(item['preco_unitario'])}")
        
        # Adicionar item manualmente
        with st.expander("Add Item Manually"):
            prod_col1, prod_col2, prod_col3 = st.columns(3)
            with prod_col1:
                produto_manual = st.selectbox(
                    "Product",
                    ["Only DTF"] + [p['nome'] for p in data['produtos']]
                )
            with prod_col2:
                quantidade_manual = st.number_input("Quantity", min_value=1, value=1)
            with prod_col3:
                valor_unitario_manual = st.number_input("Unit Value (R$)", min_value=0.0, value=0.0)
            
            if st.button("Add Item to Budget"):
                st.success("Item added!")
        
        # Botões do formulário
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            submit = st.form_submit_button("Save Budget", type="primary", use_container_width=True)
        with col_btn2:
            if st.form_submit_button("Save and Generate PDF", use_container_width=True):
                submit = True
                gerar_pdf_flag = True
        with col_btn3:
            if st.form_submit_button("Cancel", type="secondary", use_container_width=True):
                st.session_state.current_page = "calculator"
                st.rerun()
        
        if submit:
            if not cliente.strip():
                st.error("Client name is required!")
            else:
                # Calcular total
                total = 0
                if st.session_state.get('selected_products'):
                    total = sum(item['preco_total'] for item in st.session_state.selected_products)
                
                # Criar orçamento
                novo_numero = data['ultimo_numero_orcamento'] + 1
                novo_orcamento = {
                    "numero": novo_numero,
                    "data": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "cliente": cliente.strip(),
                    "tipo_entrega": tipo_entrega,
                    "tipo_venda": tipo_venda,
                    "endereco": endereco.strip(),
                    "prazo_producao": prazo_producao,
                    "valor_total": total,
                    "observacoes": observacoes.strip()
                }
                
                # Adicionar itens
                if st.session_state.get('selected_products'):
                    novo_orcamento['itens'] = st.session_state.selected_products
                
                # Salvar
                data['orcamentos'].append(novo_orcamento)
                data['ultimo_numero_orcamento'] = novo_numero
                salvar_dados(data)
                st.session_state.data = data
                
                st.success(f"Budget #{novo_numero:04d} saved successfully!")
                
                # Limpar seleção
                st.session_state.selected_products = []
                
                # Gerar PDF se solicitado
                if gerar_pdf_flag:
                    pdf_path = gerar_pdf(novo_orcamento)
                    if pdf_path:
                        with open(pdf_path, "rb") as f:
                            pdf_bytes = f.read()
                        
                        st.download_button(
                            label="Download PDF",
                            data=pdf_bytes,
                            file_name=f"Orcamento_{novo_numero:04d}.pdf",
                            mime="application/pdf"
                        )

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

# --- FUNÇÃO PARA GERAR PDF ---
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
        </div>
        """, unsafe_allow_html=True)
        
        # Menu de navegação
        menu_options = {
            "📱 Calculator": "calculator",
            "📦 Products": "products",
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
        
        # Informações da sessão
        if st.session_state.data:
            st.caption(f"Products: {len(st.session_state.data['produtos'])}")
            st.caption(f"Budgets: {len(st.session_state.data['orcamentos'])}")
    
    # Conteúdo principal baseado na página atual
    if st.session_state.current_page == "calculator":
        mostrar_calculator()
    elif st.session_state.current_page == "products":
        mostrar_products()
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