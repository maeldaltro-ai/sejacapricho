"""
Módulo de utilidades para o sistema DTF Pricing Calculator
"""

import json
from datetime import datetime
import pandas as pd

def validate_email(email):
    """Valida formato de email"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Valida formato de telefone brasileiro"""
    import re
    # Aceita formatos: (11) 99999-9999, 11999999999, (11) 9999-9999
    pattern = r'^\(?\d{2}\)?[\s-]?\d{4,5}[\s-]?\d{4}$'
    return re.match(pattern, phone) is not None

def validate_cep(cep):
    """Valida formato de CEP brasileiro"""
    import re
    # Aceita formatos: 00000-000, 00000000
    pattern = r'^\d{5}-?\d{3}$'
    return re.match(pattern, cep) is not None

def calculate_age(date_str):
    """Calcula idade a partir de uma data string"""
    try:
        birth_date = datetime.strptime(date_str, "%d/%m/%Y")
        today = datetime.now()
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return age
    except:
        return None

def export_to_excel(data, filename="export.xlsx"):
    """Exporta dados para Excel"""
    df = pd.DataFrame(data)
    df.to_excel(filename, index=False)
    return filename

def import_from_excel(filename):
    """Importa dados de Excel"""
    try:
        df = pd.read_excel(filename)
        return df.to_dict('records')
    except Exception as e:
        print(f"Erro ao importar: {e}")
        return []