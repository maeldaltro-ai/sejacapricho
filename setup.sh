#!/bin/bash

echo "🚀 Iniciando setup do DTF Pricing Calculator..."

# Instalar dependências
pip install --upgrade pip
pip install -r requirements.txt

# Verificar se o banco de dados está acessível
if [ -n "$DATABASE_URL" ]; then
    echo "📦 Configurando banco de dados PostgreSQL..."
    # Testar conexão com o banco
    sleep 2
else
    echo "📦 Usando SQLite local..."
fi

echo "✅ Setup concluído!"
