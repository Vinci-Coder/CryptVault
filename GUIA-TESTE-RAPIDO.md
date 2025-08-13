# ⚡ CryptVault - Guia de Teste Rápido

## 🚀 **Setup em 5 Minutos**

```bash
# 1. Clone e configure
git clone <repository>
cd Back-End-CryptVault
cp env.example .env

# 2. Execute ambiente completo
docker-compose -f docker-compose.dev.yml up -d

# 3. Aguarde 2 minutos para todos os serviços subirem
docker-compose -f docker-compose.dev.yml ps

# 4. Teste automatizado
./scripts/quick-test.sh
```

## 🌐 **Acesso Imediato**

| Serviço | URL | Descrição |
|---------|-----|-----------|
| **API Principal** | http://localhost:8000 | CryptVault Core |
| **📖 Documentação** | http://localhost:8000/api/v1/docs | **← COMECE AQUI** |
| **🗄️ Banco (Adminer)** | http://localhost:8080 | Admin DB |
| **🔐 Auth Mock** | http://localhost:8001/health | AuthManager |
| **🔒 Crypto Mock** | http://localhost:8002/health | Crypto Service |

## 🎯 **Tokens para Teste**

| Token | Usuário | Empresa(s) | Permissões |
|-------|---------|------------|------------|
| `admin-token` | João Silva (CTO) | Vinci Code (admin) | **Todas** |
| `dev-token` | Maria Santos (Dev) | Vinci Code (dev) + Startup ABC (pm) | **Multi-empresa** |
| `viewer-token` | Pedro Viewer | Vinci Code (viewer) | **Só leitura** |

## 🧪 **Testes Básicos (Copy & Paste)**

### **1. Health Check**
```bash
curl http://localhost:8000/health
```

### **2. Documentação Interativa**
```bash
# Abra no navegador:
open http://localhost:8000/api/v1/docs
# Clique "Authorize" → Digite "admin-token" → Teste endpoints
```

### **3. Contexto Multi-Tenant**
```bash
# Admin (uma empresa)
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/users/me

# Dev multi-empresa
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/users/me
```

### **4. Criar Secret**
```bash
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Secret","content":"my-secret-value","type":"text","description":"Secret para teste"}' \
  http://localhost:8000/api/v1/secrets/
```

### **5. Listar Secrets**
```bash
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/
```

### **6. Obter Conteúdo (use ID do secret criado)**
```bash
SECRET_ID="cole-o-id-aqui"
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/content
```

### **7. Criar Empresa**
```bash
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Minha Startup","slug":"minha-startup","type":"startup"}' \
  http://localhost:8000/api/v1/companies/
```

### **8. Trocar Empresa (dev-token)**
```bash
curl -X POST \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"company_id":"550e8400-e29b-41d4-a716-446655440003"}' \
  http://localhost:8000/api/v1/users/me/switch-company
```

### **9. Versionamento**
```bash
# Atualize o secret (cria nova versão)
curl -X PUT \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"content":"updated-value","change_description":"Primeira atualização"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID

# Veja versões
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions
```

### **10. Compartilhamento**
```bash
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"max_downloads":3,"expires_in_hours":24,"description":"Teste share"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/share
```

### **11. Auditoria**
```bash
# Ver logs
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/audit/logs

# Estatísticas
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/stats/summary?hours=24"
```

### **12. Teste de Permissões**
```bash
# Viewer só lê
curl -H "Authorization: Bearer viewer-token" \
     http://localhost:8000/api/v1/secrets/

# Viewer não pode criar (deve falhar)
curl -X POST \
  -H "Authorization: Bearer viewer-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Fail","content":"test"}' \
  http://localhost:8000/api/v1/secrets/
```

## 🛠️ **Casos de Uso Avançados**

### **Workflow Empresarial**
```bash
# 1. Criar empresa → projeto → secrets por ambiente
COMPANY_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"TestCorp","slug":"testcorp","type":"enterprise"}' \
  http://localhost:8000/api/v1/companies/)

COMPANY_ID=$(echo $COMPANY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 2. Criar projeto
PROJECT_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Main App","slug":"main-app","company_id":"'$COMPANY_ID'","environments":["dev","prod"]}' \
  http://localhost:8000/api/v1/projects/)

PROJECT_ID=$(echo $PROJECT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# 3. Secrets por ambiente
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"DB_PASSWORD","content":"dev-pass-123","project_id":"'$PROJECT_ID'","environment":"dev"}' \
  http://localhost:8000/api/v1/secrets/

curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"DB_PASSWORD","content":"prod-pass-456","project_id":"'$PROJECT_ID'","environment":"prod"}' \
  http://localhost:8000/api/v1/secrets/
```

### **Teste Criptografia Direta**
```bash
# 1. Criptografar
ENCRYPT_RESPONSE=$(curl -s -X POST \
  -H "Content-Type: application/json" \
  -d '{"data":"sensitive-data-123","data_type":"text"}' \
  http://localhost:8002/v1/encrypt)

ENCRYPTED_ID=$(echo $ENCRYPT_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['encrypted_id'])")

# 2. Descriptografar
curl http://localhost:8002/v1/decrypt/$ENCRYPTED_ID

# 3. Verificar integridade
curl http://localhost:8002/v1/verify/$ENCRYPTED_ID
```

## 🐛 **Troubleshooting Rápido**

### **Serviços não sobem**
```bash
# Ver logs
docker-compose -f docker-compose.dev.yml logs

# Recriar tudo
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d --build
```

### **401 Unauthorized**
```bash
# Verificar token no auth service
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  http://localhost:8001/v1/validate-token
```

### **500 Internal Error**
```bash
# Ver logs da aplicação
docker-compose -f docker-compose.dev.yml logs cryptvault-core

# Verificar status dos serviços
curl http://localhost:8000/status
```

### **Banco não conecta**
```bash
# Verificar PostgreSQL
docker-compose -f docker-compose.dev.yml ps postgres

# Conectar manualmente
docker exec -it <postgres-container> psql -U cryptvault -d cryptvault_db
```

## 📊 **Verificação do Sistema**

### **Status dos Serviços**
```bash
curl http://localhost:8000/status | python3 -m json.tool
```

### **Dados no Banco**
```bash
# Via Adminer: http://localhost:8080
# Sistema: PostgreSQL
# Servidor: postgres
# Usuário: cryptvault  
# Senha: password
# Base: cryptvault_db

# Via CLI:
docker exec -it <postgres-container> psql -U cryptvault -d cryptvault_db -c "SELECT COUNT(*) FROM secrets;"
```

### **Logs em Tempo Real**
```bash
# Todos os serviços
docker-compose -f docker-compose.dev.yml logs -f

# Apenas a aplicação
docker-compose -f docker-compose.dev.yml logs -f cryptvault-core
```

## 🎯 **Cenários de Demo**

### **Demo 1: Multi-Tenant Básico**
1. Mostrar contexto admin-token (uma empresa)
2. Mostrar contexto dev-token (duas empresas)
3. Trocar empresa e mostrar mudança de permissões

### **Demo 2: Secrets Management**
1. Criar secret
2. Atualizar (versionar)
3. Ver histórico de versões
4. Restaurar versão anterior
5. Compartilhar com link temporário

### **Demo 3: Controle de Acesso**
1. Admin cria secret
2. Dev consegue ler
3. Viewer só consegue ler
4. Viewer falha ao tentar criar
5. Mostrar logs de auditoria

### **Demo 4: Workflow Empresarial**
1. Criar empresa nova
2. Criar projeto com ambientes
3. Criar secrets por ambiente
4. Mostrar isolamento entre empresas

## 💡 **Dicas Importantes**

- ✅ **Use admin-token** para testes de criação
- ✅ **Use dev-token** para multi-empresa
- ✅ **Use viewer-token** para testar permissões
- ✅ **Documentação Swagger** é interativa e completa
- ✅ **Health checks** mostram status dos serviços
- ✅ **Logs** estão em formato JSON estruturado
- ✅ **IDs** são UUIDs - copie exatamente
- ✅ **Permissões** são granulares e contextuais

**🎉 Em 5 minutos você tem um sistema enterprise multi-tenant funcionando!**
