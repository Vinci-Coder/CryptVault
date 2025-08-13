# 🚀 Como Usar o CryptVault - Guia Prático

## ⚡ Setup Rápido (5 minutos)

### 1. **Pré-requisitos**
```bash
# Verificar se tem Docker
docker --version
docker-compose --version

# Verificar se tem Python 3.11+ (opcional para desenvolvimento local)
python --version
```

### 2. **Configuração Instantânea**
```bash
# 1. Clone o projeto
git clone <repository-url>
cd Back-End-CryptVault

# 2. Copie configurações
cp env.example .env

# 3. Execute ambiente completo com mocks
docker-compose -f docker-compose.dev.yml up -d

# 4. Aguarde todos os serviços ficarem prontos (1-2 minutos)
docker-compose -f docker-compose.dev.yml ps
```

### 3. **Teste Imediato**
```bash
# Executar script de teste
chmod +x scripts/quick-test.sh  # Linux/Mac
./scripts/quick-test.sh

# OU teste manual:
curl http://localhost:8000/health
```

## 📊 Serviços Disponíveis

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **CryptVault API** | http://localhost:8000 | API principal |
| **Documentação** | http://localhost:8000/api/v1/docs | Swagger UI |
| **AuthManager Mock** | http://localhost:8001 | Autenticação mock |
| **Crypto Service Mock** | http://localhost:8002 | Criptografia mock |
| **Adminer (DB)** | http://localhost:8080 | Administração PostgreSQL |
| **PostgreSQL** | localhost:5432 | Banco de dados |
| **Redis** | localhost:6379 | Cache |

## 🔑 Tokens de Teste

### **Token Admin** (Todas as permissões)
```
admin-token
```
**Permissões:**
- secret:read, secret:create, secret:update, secret:delete, secret:share
- audit:read, audit:admin, security:read, security:manage

### **Token User** (Permissões limitadas)
```
user-token
```
**Permissões:**
- secret:read, secret:create, secret:update

## 📝 Exemplos de Uso da API

### **1. Health Check**
```bash
curl http://localhost:8000/health
```

### **2. Listar Secrets**
```bash
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/
```

### **3. Criar Secret**
```bash
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Database Password",
    "description": "Senha do banco de produção",
    "content": "super-secret-password",
    "type": "text",
    "environment": "prod",
    "tags": ["database", "critical"]
  }' \
  http://localhost:8000/api/v1/secrets/
```

### **4. Obter Conteúdo de Secret**
```bash
# Primeiro, obtenha o ID do secret criado acima
SECRET_ID="<id-retornado>"

# Obter apenas metadata
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID

# Obter conteúdo descriptografado
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/content
```

### **5. Atualizar Secret**
```bash
curl -X PUT \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Senha atualizada do banco",
    "content": "new-super-secret-password",
    "change_description": "Rotação de senha mensal"
  }' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID
```

### **6. Versionamento**
```bash
# Listar versões
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions

# Obter versão específica
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions/1/content

# Restaurar versão anterior
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/versions/1/restore
```

### **7. Compartilhamento Seguro**
```bash
# Criar link de compartilhamento
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "max_downloads": 5,
    "expires_in_hours": 24,
    "requires_password": true,
    "password": "temp-password-123",
    "description": "Compartilhamento para cliente"
  }' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/share
```

### **8. Busca Avançada**
```bash
# Buscar por nome
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?q=database"

# Filtrar por tipo e ambiente
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?type=text&environment=prod"

# Paginação
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?page=1&size=10"
```

### **9. Auditoria**
```bash
# Logs de auditoria
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/logs"

# Filtrar por ação
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/logs?action=secret_create"

# Logs de acesso de um secret
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/access-logs/$SECRET_ID?hours=24"

# Resumo de auditoria
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/stats/summary?hours=168"
```

## 🖥️ Usando a Interface Web (Swagger)

1. **Abra:** http://localhost:8000/api/v1/docs
2. **Autentique:**
   - Clique em "Authorize" 
   - Digite: `admin-token`
   - Clique "Authorize"
3. **Teste endpoints** diretamente na interface

## 🧪 Cenários de Teste Comuns

### **Cenário 1: Gerenciamento Básico**
```bash
# 1. Criar secret
SECRET_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"API Key","content":"key-123","type":"api_key"}' \
  http://localhost:8000/api/v1/secrets/)

SECRET_ID=$(echo $SECRET_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 2. Ler secret
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/content

# 3. Atualizar secret
curl -X PUT \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"content":"key-456","change_description":"Rotação de chave"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID

# 4. Ver histórico
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions
```

### **Cenário 2: Permissões**
```bash
# Teste com admin-token (deve funcionar)
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/

# Teste com user-token (deve funcionar)
curl -H "Authorization: Bearer user-token" \
     http://localhost:8000/api/v1/secrets/

# Teste sem token (deve falhar - 401)
curl http://localhost:8000/api/v1/secrets/

# Teste com token inválido (deve falhar - 401) 
curl -H "Authorization: Bearer invalid-token" \
     http://localhost:8000/api/v1/secrets/
```

### **Cenário 3: Workflow de Desenvolvimento**
```bash
# 1. Criar secret de desenvolvimento
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "DB Connection",
    "content": "postgresql://user:pass@localhost:5432/myapp",
    "type": "text",
    "environment": "dev",
    "tags": ["database", "connection-string"]
  }' \
  http://localhost:8000/api/v1/secrets/

# 2. Buscar secrets por tag
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?tags=database"

# 3. Buscar por ambiente
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?environment=dev"
```

## 🔧 Desenvolvimento Local

### **Executar sem Docker**
```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar .env
cp env.example .env
# Editar URLs para localhost:

# 3. Subir dependências
docker-compose up -d postgres redis auth-mock crypto-mock

# 4. Executar migrations
alembic upgrade head

# 5. Executar aplicação
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### **Executar Testes**
```bash
# Testes unitários
pytest

# Testes com cobertura
pytest --cov=app

# Teste específico
pytest tests/test_api/test_secrets.py -v
```

### **Logs e Debug**
```bash
# Ver logs da aplicação
docker-compose -f docker-compose.dev.yml logs -f cryptvault-core

# Ver logs de todos os serviços
docker-compose -f docker-compose.dev.yml logs -f

# Debug no container
docker exec -it <container-name> bash
```

## 🗄️ Banco de Dados

### **Acessar via Adminer**
1. **URL:** http://localhost:8080
2. **Sistema:** PostgreSQL
3. **Servidor:** postgres
4. **Usuário:** cryptvault
5. **Senha:** password
6. **Base:** cryptvault_db

### **Acessar via CLI**
```bash
# Conectar ao PostgreSQL
docker exec -it <postgres-container> psql -U cryptvault -d cryptvault_db

# Comandos úteis:
\dt              # Listar tabelas
\d secrets       # Descrever tabela secrets
SELECT * FROM secrets LIMIT 5;
SELECT * FROM audit_logs ORDER BY created_at DESC LIMIT 10;
```

## 📊 Monitoramento

### **Status dos Serviços**
```bash
# Status completo
curl http://localhost:8000/status | python3 -m json.tool

# Status dos containers
docker-compose -f docker-compose.dev.yml ps

# Uso de recursos
docker stats
```

### **Métricas de Uso**
```bash
# Estatísticas do crypto service
curl http://localhost:8002/v1/stats

# Resumo de auditoria (últimas 24h)
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/stats/summary?hours=24"
```

## 🐛 Troubleshooting

### **Problemas Comuns**

#### **1. Erro de Conexão com Banco**
```bash
# Verificar se PostgreSQL está rodando
docker-compose -f docker-compose.dev.yml ps postgres

# Ver logs do PostgreSQL
docker-compose -f docker-compose.dev.yml logs postgres

# Conectar manualmente
docker exec -it <postgres-container> pg_isready -U cryptvault
```

#### **2. Serviços Mock não Respondem**
```bash
# Verificar status dos mocks
curl http://localhost:8001/health
curl http://localhost:8002/health

# Reiniciar mocks
docker-compose -f docker-compose.dev.yml restart auth-mock crypto-mock
```

#### **3. Erro 401 - Unauthorized**
- Verificar se está usando `admin-token` ou `user-token`
- Verificar formato: `Authorization: Bearer admin-token`
- Testar token no mock: `curl -X POST -H "Authorization: Bearer admin-token" http://localhost:8001/v1/validate-token`

#### **4. Erro 500 - Internal Server Error**
```bash
# Ver logs detalhados
docker-compose -f docker-compose.dev.yml logs cryptvault-core

# Verificar health dos serviços externos
curl http://localhost:8000/status
```

### **Reset Completo**
```bash
# Parar tudo
docker-compose -f docker-compose.dev.yml down -v

# Limpar volumes
docker volume prune

# Recriar tudo
docker-compose -f docker-compose.dev.yml up -d --build
```

## 🎯 Próximos Passos

### **Para Desenvolvimento**
1. **Implementar Crypto Service real** em Go
2. **Configurar MS-AuthManager** real  
3. **Adicionar mais testes** de integração
4. **Implementar CLI** para desenvolvedores

### **Para Produção**
1. **Deploy em staging** 
2. **Configurar monitoramento** (Grafana/Prometheus)
3. **Implementar backup** automatizado
4. **Configurar CI/CD** completo

---

## 💡 Dicas Importantes

- **Use sempre HTTPS** em produção
- **Rotacione tokens** regularmente
- **Monitore logs** de auditoria
- **Faça backup** do banco regularmente
- **Teste permissões** com diferentes tokens
- **Documente** mudanças de API

**🎉 O CryptVault está pronto para uso em desenvolvimento! Para dúvidas, consulte a documentação em `/api/v1/docs`**

