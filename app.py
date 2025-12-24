import streamlit as st
import json
import pandas as pd
from PIL import Image

# Configuração da Página
st.set_page_config(page_title="Calculadora DTF", layout="wide")

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_data
def carregar_dados():
    try:
        with open('dados_sistema.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("Arquivo dados_sistema.json não encontrado.")
        return None

def salvar_dados(dados):
    with open('dados_sistema.json', 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4)

# --- CARREGAR DADOS ---
data = carregar_dados()

if data:
    # --- BARRA LATERAL (Configurações) ---
    with st.sidebar:
        st.header("⚙️ Configurações")
        preco_metro = st.number_input("Preço Metro (R$)", value=data['config']['preco_metro'])
        largura_rolo = st.number_input("Largura Rolo (cm)", value=data['config']['largura_rolo'])
        
        st.divider()
        st.write("Custos Fixos")
        custo_energia = st.number_input("Energia", value=data['config']['fixed_costs']['energia'])
        custo_transporte = st.number_input("Transporte", value=data['config']['fixed_costs']['transporte'])
        custo_emb = st.number_input("Embalagem", value=data['config']['fixed_costs']['embalagem'])

    # --- ÁREA PRINCIPAL ---
    st.title("🖨️ Calculadora de Orçamento DTF")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Adicionar Item")
        # Inputs do usuário
        produto_base = st.selectbox("Selecione o Produto Base", ["Apenas DTF"] + [p['nome'] for p in data['produtos']])
        
        c1, c2 = st.columns(2)
        largura = c1.number_input("Largura (cm)", min_value=0.0)
        altura = c2.number_input("Altura (cm)", min_value=0.0)
        quantidade = st.number_input("Quantidade", min_value=1, value=1)

        # Botão de Calcular Item
        if st.button("Calcular Item", type="primary"):
            # Lógica de cálculo (Adaptada do seu código original)
            area_cm = largura * altura
            comprimento_linear = area_cm / largura_rolo
            custo_dtf = comprimento_linear * preco_metro
            
            # Pega custo do produto base se não for só DTF
            custo_produto_base = 0
            if produto_base != "Apenas DTF":
                for p in data['produtos']:
                    if p['nome'] == produto_base:
                        custo_produto_base = p['custo']
                        break
            
            custo_total_item = (custo_dtf + custo_produto_base + custo_energia + custo_transporte + custo_emb) * quantidade
            
            # Adiciona à sessão (memória temporária do navegador)
            if 'orcamento' not in st.session_state:
                st.session_state.orcamento = []
            
            st.session_state.orcamento.append({
                "Item": produto_base,
                "Dimensões": f"{largura}x{altura}",
                "Qtd": quantidade,
                "Unitário": f"R$ {custo_total_item/quantidade:.2f}",
                "Total": custo_total_item
            })
            st.success("Item adicionado!")

    with col2:
        st.subheader("Resumo do Orçamento")
        if 'orcamento' in st.session_state and len(st.session_state.orcamento) > 0:
            # Mostra tabela bonita
            df = pd.DataFrame(st.session_state.orcamento)
            st.dataframe(df, use_container_width=True)
            
            total_geral = df['Total'].sum()
            st.metric(label="VALOR TOTAL DO PEDIDO", value=f"R$ {total_geral:.2f}")
            
            if st.button("Limpar Orçamento"):
                st.session_state.orcamento = []
                st.rerun()
        else:
            st.info("Nenhum item adicionado ainda.")

else:
    st.warning("Carregando sistema...")