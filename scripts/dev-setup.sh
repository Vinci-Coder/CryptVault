#!/bin/bash

# Script de configuração para desenvolvimento do CryptVault

set -e

echo "🚀 Configurando ambiente de desenvolvimento do CryptVault..."

# Verifica se o Docker está instalado
if ! command -v docker &> /dev/null; then
    echo "❌ Docker não encontrado. Por favor, instale o Docker primeiro."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose não encontrado. Por favor, instale o Docker Compose primeiro."
    exit 1
fi

# Cria arquivo .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env..."
    cp env.example .env
    echo "✅ Arquivo .env criado. Configure as variáveis conforme necessário."
fi

# Cria diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p logs
mkdir -p mocks/auth-manager
mkdir -p mocks/crypto-service

# Inicia serviços de infraestrutura
echo "🔧 Iniciando serviços de infraestrutura..."
docker-compose up -d postgres redis

# Aguarda serviços ficarem prontos
echo "⏳ Aguardando serviços ficarem prontos..."
sleep 10

# Verifica se o Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 não encontrado. Por favor, instale o Python 3.11+."
    exit 1
fi

# Instala dependências Python (se aplicável)
if [ -f requirements.txt ]; then
    echo "📦 Instalando dependências Python..."
    
    # Verifica se existe venv
    if [ ! -d "venv" ]; then
        echo "🐍 Criando ambiente virtual..."
        python3 -m venv venv
    fi
    
    echo "🔌 Ativando ambiente virtual e instalando dependências..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    echo "✅ Dependências instaladas!"
else
    echo "⚠️ requirements.txt não encontrado."
fi

# Executa migrations se Alembic estiver configurado
if [ -f alembic.ini ]; then
    echo "🗄️ Executando migrations do banco de dados..."
    source venv/bin/activate 2>/dev/null || true
    
    # Espera um pouco mais para o PostgreSQL estar totalmente pronto
    sleep 5
    
    # Cria a migration inicial se não existir
    if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
        echo "📝 Criando migration inicial..."
        alembic revision --autogenerate -m "Initial migration"
    fi
    
    # Executa migrations
    alembic upgrade head
    echo "✅ Migrations executadas!"
fi

# Inicia todos os serviços
echo "🚀 Iniciando todos os serviços..."
docker-compose up -d

echo ""
echo "✅ Ambiente de desenvolvimento configurado com sucesso!"
echo ""
echo "🌐 Serviços disponíveis:"
echo "   • API: http://localhost:8000"
echo "   • Docs: http://localhost:8000/api/v1/docs"
echo "   • Adminer: http://localhost:8080"
echo "   • PostgreSQL: localhost:5432"
echo "   • Redis: localhost:6379"
echo ""
echo "📋 Próximos passos:"
echo "   1. Configure as variáveis no arquivo .env"
echo "   2. Acesse http://localhost:8000/api/v1/docs para ver a documentação"
echo "   3. Use docker-compose logs -f cryptvault-core para ver os logs"
echo ""
echo "🛠️ Comandos úteis:"
echo "   • docker-compose ps          # Ver status dos serviços"
echo "   • docker-compose logs -f     # Ver logs em tempo real"
echo "   • docker-compose down        # Parar todos os serviços"
echo "   • docker-compose restart     # Reiniciar serviços"

