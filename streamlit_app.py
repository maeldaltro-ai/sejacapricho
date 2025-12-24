import streamlit as st
import json
import io
from datetime import datetime

DATA_FILE = "dados_sistema.json"

st.set_page_config(page_title="Capricho - Orçamentos", layout="wide")

st.title("Capricho — Orçamentos")

@st.cache_data
def load_data(path=DATA_FILE):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"orcamentos": []}

data = load_data()
orcamentos = data.get("orcamentos", [])

col1, col2 = st.columns([2,1])
with col1:
    st.subheader(f"Total de Orçamentos: {len(orcamentos)}")
with col2:
    total_val = sum(o.get("valor_total", 0) for o in orcamentos)
    st.subheader(f"Valor Total: R$ {total_val:,.2f}")

st.markdown("---")

if not orcamentos:
    st.info("Nenhum orçamento encontrado. Suba um arquivo `dados_sistema.json` na raiz do repositório.")
else:
    for o in sorted(orcamentos, key=lambda x: x.get("numero", 0), reverse=True):
        st.container()
        with st.expander(f"#{o.get('numero',0):04d} — {o.get('cliente','--')}"):
            cols = st.columns([2,1,1,1])
            with cols[0]:
                st.write("**Cliente**")
                st.write(o.get("cliente",""))
                st.write("**Data**")
                st.write(o.get("data",""))
                if o.get("observacoes"):
                    st.write("**Observações**")
                    st.write(o.get("observacoes"))
            with cols[1]:
                st.write("**Itens/Produto**")
                if "produto" in o:
                    st.write(o.get("produto"))
                elif "itens" in o:
                    for it in o.get("itens",[]):
                        st.write(f"- {it.get('nome','')} x{it.get('quantidade','')} — R$ {it.get('valor_unitario','')}")
            with cols[2]:
                st.write("**Quantidade**")
                if "quantidade" in o:
                    st.write(o.get("quantidade"))
                elif "itens" in o:
                    total_q = sum(float(it.get('quantidade',0)) for it in o.get('itens',[]))
                    st.write(int(total_q))
            with cols[3]:
                st.write("**Valor Total**")
                st.write(f"R$ {o.get('valor_total',0):,.2f}")
                st.write("")
                # Download JSON for this orçamento
                btn_label = f"Baixar JSON #{o.get('numero',0):04d}"
                orc_json = json.dumps(o, ensure_ascii=False, indent=2).encode("utf-8")
                st.download_button(btn_label, orc_json, file_name=f"Orcamento_{o.get('numero',0):04d}.json", mime="application/json")

                # Placeholder: PDF generation requires porting your PDF code (reportlab) to be callable here
                st.info("Gerar PDF está disponível após portar a função de geração de PDF para módulo sem GUI.")

st.markdown("---")

st.sidebar.title("Admin")
st.sidebar.write("Suba um `dados_sistema.json` atualizado para ver orçamentos reais.")
st.sidebar.write("Deploy: Push repo to GitHub → Streamlit Cloud → New app → select repository and `streamlit_app.py`.")

