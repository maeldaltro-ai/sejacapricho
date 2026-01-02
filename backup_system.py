"""
Sistema de backup automático
"""

import shutil
from datetime import datetime
import json
import os

def create_backup(data_file="dados_sistema.json", backup_dir="backups"):
    """Cria backup do arquivo de dados"""
    
    if not os.path.exists(data_file):
        return False
    
    # Criar diretório de backups se não existir
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    # Nome do arquivo de backup com timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_file = f"{backup_dir}/backup_{timestamp}.json"
    
    try:
        # Copiar arquivo
        shutil.copy2(data_file, backup_file)
        
        # Manter apenas os últimos 30 backups
        backup_files = sorted([f for f in os.listdir(backup_dir) if f.startswith("backup_")])
        if len(backup_files) > 30:
            for old_file in backup_files[:-30]:
                os.remove(os.path.join(backup_dir, old_file))
        
        return True
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return False

def restore_backup(backup_file, data_file="dados_sistema.json"):
    """Restaura backup"""
    try:
        shutil.copy2(backup_file, data_file)
        return True
    except Exception as e:
        print(f"Erro ao restaurar backup: {e}")
        return False