#!/bin/bash
# start.sh

echo "🔧 Inicializando DTF Pricing Calculator..."
echo "📊 Ambiente: $APP_ENV"

# Verificar se DATABASE_URL está configurada
if [ -z "$DATABASE_URL" ]; then
    echo "❌ ERRO: DATABASE_URL não está configurada!"
    exit 1
fi

echo "✅ Banco de dados configurado"

# Executar migrações do banco de dados
echo "🔄 Executando migrações do banco de dados..."
python -c "
from models import init_db
init_db()
print('✅ Banco de dados inicializado')
"

# Iniciar aplicação Streamlit
echo "🚀 Iniciando aplicação Streamlit..."
exec streamlit run app.py \
    --server.port=$PORT \
    --server.address=0.0.0.0 \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false \
    --theme.base="dark" \
    --browser.gatherUsageStats=false