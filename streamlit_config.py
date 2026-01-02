import streamlit as st

# Configurações do sistema
SYSTEM_CONFIG = {
    "app_name": "DTF Pricing Calculator",
    "version": "2.0.0",
    "company_name": "Seja Capricho",
    "company_contact": "(75) 9155-5968",
    "company_email": "contato@sejacapricho.com.br",
    "company_website": "sejacapricho.com.br",
    "default_margin": 50.0,
    "default_production_days": 5,
    "default_currency": "BRL",
    "timezone": "America/Sao_Paulo"
}

# Funções de configuração
def setup_page_config():
    """Configura a página do Streamlit"""
    st.set_page_config(
        page_title=SYSTEM_CONFIG["app_name"],
        page_icon="🖨️",
        layout="wide",
        initial_sidebar_state="expanded",
        menu_items={
            'Get Help': f'https://{SYSTEM_CONFIG["company_website"]}',
            'Report a bug': f'mailto:{SYSTEM_CONFIG["company_email"]}',
            'About': f'''
            ## {SYSTEM_CONFIG["app_name"]} v{SYSTEM_CONFIG["version"]}
            
            Sistema completo de gerenciamento para DTF e estamparia.
            
            **Desenvolvido para:** {SYSTEM_CONFIG["company_name"]}
            **Contato:** {SYSTEM_CONFIG["company_contact"]}
            **Website:** {SYSTEM_CONFIG["company_website"]}
            '''
        }
    )

def apply_custom_css():
    """Aplica CSS personalizado"""
    custom_css = f"""
    <style>
    .main {{
        background-color: {SYSTEM_CONFIG.get('theme_bg', '#0D1117')};
    }}
    
    .stButton > button {{
        border-radius: 8px;
        font-weight: 500;
    }}
    
    .stAlert {{
        border-radius: 8px;
    }}
    
    .metric-card {{
        background-color: #161B22;
        padding: 15px;
        border-radius: 10px;
        border-left: 4px solid #9370DB;
    }}
    
    .status-green {{
        color: #238636;
        font-weight: bold;
    }}
    
    .status-red {{
        color: #DA3633;
        font-weight: bold;
    }}
    
    .status-yellow {{
        color: #FFD700;
        font-weight: bold;
    }}
    
    .status-blue {{
        color: #1F6FEB;
        font-weight: bold;
    }}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

def get_system_info():
    """Retorna informações do sistema"""
    return SYSTEM_CONFIG