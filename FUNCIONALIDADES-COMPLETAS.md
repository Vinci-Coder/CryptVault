# 📋 CryptVault - Funcionalidades Completas

## 🎯 **Visão Geral do Sistema**

O CryptVault é um sistema **enterprise multi-tenant** para gerenciamento seguro de secrets com as seguintes características principais:

- 🏢 **Multi-tenant completo** (usuários em múltiplas empresas)
- 🔐 **Criptografia AES-256** via microserviço dedicado
- 🔄 **Versionamento completo** com histórico
- 👥 **Controle de acesso granular** por roles e permissões
- 📝 **Auditoria completa** de todas as operações
- 🔗 **Compartilhamento seguro** via links temporários
- 🚀 **API REST completa** + Documentação automática

---

## 🏗️ **1. SISTEMA ORGANIZACIONAL**

### **1.1 Gerenciamento de Empresas**

#### **Funcionalidades:**
- ✅ Criar empresas com tipos (startup, SME, enterprise, agency, freelancer, non-profit)
- ✅ Status de empresa (active, trial, premium, suspended)
- ✅ Limites configuráveis (usuários, projetos, secrets, storage)
- ✅ Trial management com expiração
- ✅ Configurações personalizadas por empresa
- ✅ Billing e endereçamento

#### **Como Usar:**

```bash
# Criar empresa
POST /api/v1/companies/
{
  "name": "Minha Startup",
  "slug": "minha-startup",
  "type": "startup",
  "description": "Uma startup inovadora",
  "email": "contato@startup.com",
  "max_users": 50,
  "max_projects": 10,
  "max_secrets": 1000
}

# Listar empresas do usuário
GET /api/v1/companies/

# Obter empresa específica
GET /api/v1/companies/{company_id}

# Atualizar empresa (apenas admins)
PUT /api/v1/companies/{company_id}
{
  "description": "Descrição atualizada",
  "max_users": 100
}

# Estatísticas da empresa
GET /api/v1/companies/{company_id}/stats

# Usuários da empresa
GET /api/v1/companies/{company_id}/users
```

#### **Como Testar:**

```bash
# 1. Teste com admin-token (pode criar)
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Company","slug":"test-company","type":"startup"}' \
  http://localhost:8000/api/v1/companies/

# 2. Teste listagem
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/companies/

# 3. Teste com dev-token (deve mostrar múltiplas empresas)
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/companies/

# 4. Teste sem token (deve falhar)
curl http://localhost:8000/api/v1/companies/
```

### **1.2 Gerenciamento de Usuários**

#### **Funcionalidades:**
- ✅ Usuários com múltiplas empresas
- ✅ Roles diferentes por empresa (admin, project_manager, developer, viewer, auditor)
- ✅ Empresa primária configurável
- ✅ Troca de contexto entre empresas
- ✅ Perfil completo (nome, email, título, timezone, idioma)
- ✅ Status de usuário (active, inactive, suspended, pending)
- ✅ Controle de sessões e segurança

#### **Como Usar:**

```bash
# Contexto do usuário atual
GET /api/v1/users/me

# Contexto com empresa específica
GET /api/v1/users/me?company_id={company_id}

# Trocar empresa ativa
POST /api/v1/users/me/switch-company
{
  "company_id": "uuid-da-empresa"
}

# Listar usuários (filtrado por empresa se especificada)
GET /api/v1/users/?company_id={id}&page=1&size=20

# Obter usuário específico
GET /api/v1/users/{user_id}

# Atualizar perfil
PUT /api/v1/users/me
{
  "full_name": "Nome Atualizado",
  "title": "Senior Developer",
  "timezone": "America/Sao_Paulo"
}
```

#### **Como Testar:**

```bash
# 1. Contexto de usuário admin (uma empresa)
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/users/me

# 2. Contexto de usuário multi-empresa
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/users/me

# 3. Trocar empresa
curl -X POST \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"company_id":"550e8400-e29b-41d4-a716-446655440003"}' \
  http://localhost:8000/api/v1/users/me/switch-company

# 4. Verificar mudança de contexto
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/users/me
```

### **1.3 Gerenciamento de Projetos**

#### **Funcionalidades:**
- ✅ Projetos por empresa com slugs únicos
- ✅ Status de projeto (planning, development, production, archived)
- ✅ Ambientes configuráveis (dev, staging, prod, custom)
- ✅ Equipe do projeto com permissões específicas
- ✅ Controle de acesso por ambiente
- ✅ Metadados (repositório, documentação, tags)
- ✅ Estatísticas e atividade

#### **Como Usar:**

```bash
# Criar projeto
POST /api/v1/projects/
{
  "name": "Website Corporativo",
  "slug": "website-corp",
  "company_id": "uuid-empresa",
  "description": "Site institucional da empresa",
  "environments": ["dev", "staging", "prod"],
  "repository_url": "https://github.com/empresa/website",
  "tags": ["frontend", "wordpress"]
}

# Listar projetos
GET /api/v1/projects/?company_id={id}&status=active

# Obter projeto específico
GET /api/v1/projects/{project_id}

# Atualizar projeto
PUT /api/v1/projects/{project_id}
{
  "status": "production",
  "environments": ["dev", "staging", "prod", "demo"]
}

# Remover projeto
DELETE /api/v1/projects/{project_id}

# Usuários do projeto
GET /api/v1/projects/{project_id}/users

# Adicionar usuário ao projeto
POST /api/v1/projects/{project_id}/users
{
  "user_id": "uuid-usuario",
  "role": "developer",
  "environments_access": ["dev", "staging"],
  "can_create_secrets": true,
  "can_read_secrets": true
}
```

#### **Como Testar:**

```bash
# 1. Criar projeto (precisa ser admin da empresa)
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Project","slug":"test-project","company_id":"550e8400-e29b-41d4-a716-446655440001","environments":["dev","prod"]}' \
  http://localhost:8000/api/v1/projects/

# 2. Listar projetos
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/projects/

# 3. Testar filtros
curl -H "Authorization: Bearer dev-token" \
     "http://localhost:8000/api/v1/projects/?company_id=550e8400-e29b-41d4-a716-446655440001"
```

---

## 🔐 **2. GERENCIAMENTO DE SECRETS**

### **2.1 CRUD de Secrets**

#### **Funcionalidades:**
- ✅ Tipos de secret (text, file, env_file, json, yaml, certificate, ssh_key, api_key)
- ✅ Criptografia AES-256 via microserviço
- ✅ Organização por empresa, projeto e ambiente
- ✅ Tags para categorização
- ✅ Validação de formato (regex, JSON, YAML)
- ✅ Expiração automática
- ✅ Status (active, archived, expired, revoked)
- ✅ Metadados customizados

#### **Como Usar:**

```bash
# Criar secret
POST /api/v1/secrets/
{
  "name": "Database Password",
  "description": "Senha do banco de produção",
  "content": "super-secret-password123",
  "type": "text",
  "project_id": "uuid-projeto",
  "environment": "prod",
  "tags": ["database", "critical"],
  "expires_at": "2024-12-31T23:59:59Z",
  "format_validation": "^[A-Za-z0-9!@#$%]+$"
}

# Listar secrets com filtros
GET /api/v1/secrets/?page=1&size=20&type=text&environment=prod&project_id={id}

# Buscar secrets
GET /api/v1/secrets/?q=database&tags=critical

# Obter metadata do secret (sem conteúdo)
GET /api/v1/secrets/{secret_id}

# Obter conteúdo descriptografado
GET /api/v1/secrets/{secret_id}/content

# Atualizar secret (cria nova versão)
PUT /api/v1/secrets/{secret_id}
{
  "content": "new-password-456",
  "change_description": "Rotação mensal de senha",
  "expires_at": "2025-01-31T23:59:59Z"
}

# Remover secret
DELETE /api/v1/secrets/{secret_id}
```

#### **Como Testar:**

```bash
# 1. Criar secret simples
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Secret","content":"my-secret-value","type":"text","description":"Secret para teste"}' \
  http://localhost:8000/api/v1/secrets/

# 2. Listar secrets
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/

# 3. Obter conteúdo (guarde o ID do secret criado)
SECRET_ID="id-retornado-acima"
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/content

# 4. Testar permissões (dev-token pode ter acesso limitado)
curl -H "Authorization: Bearer viewer-token" \
     http://localhost:8000/api/v1/secrets/

# 5. Buscar com filtros
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?q=test&type=text"

# 6. Atualizar secret
curl -X PUT \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"content":"updated-secret-value","change_description":"Teste de atualização"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID
```

### **2.2 Versionamento de Secrets**

#### **Funcionalidades:**
- ✅ Histórico completo de alterações
- ✅ Metadados por versão (checksum, tamanho, autor, data)
- ✅ Restauração de versões anteriores
- ✅ Comparação entre versões
- ✅ Descrição de mudanças
- ✅ Limpeza automática de versões antigas
- ✅ Controle de versão atual

#### **Como Usar:**

```bash
# Listar versões de um secret
GET /api/v1/secrets/{secret_id}/versions

# Obter versão específica (metadata)
GET /api/v1/secrets/{secret_id}/versions/{version_number}

# Obter conteúdo de versão específica
GET /api/v1/secrets/{secret_id}/versions/{version_number}/content

# Restaurar versão anterior (cria nova versão)
POST /api/v1/secrets/{secret_id}/versions/{version_number}/restore

# Remover versão específica (não pode ser a atual)
DELETE /api/v1/secrets/{secret_id}/versions/{version_number}
```

#### **Como Testar:**

```bash
# 1. Crie um secret e atualize várias vezes
SECRET_ID="seu-secret-id"

curl -X PUT \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"content":"versao-2","change_description":"Segunda versão"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID

curl -X PUT \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"content":"versao-3","change_description":"Terceira versão"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID

# 2. Liste versões
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions

# 3. Obtenha conteúdo da versão 1
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions/1/content

# 4. Restaure versão 1
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/versions/1/restore

# 5. Verifique que nova versão foi criada
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/versions
```

### **2.3 Compartilhamento Seguro**

#### **Funcionalidades:**
- ✅ Links temporários com expiração
- ✅ Controle de downloads máximos
- ✅ Proteção por senha opcional
- ✅ Whitelist de IPs
- ✅ Auditoria de acessos
- ✅ Links únicos e seguros
- ✅ Descrição personalizada

#### **Como Usar:**

```bash
# Criar link de compartilhamento
POST /api/v1/secrets/{secret_id}/share
{
  "max_downloads": 5,
  "expires_in_hours": 24,
  "requires_password": true,
  "password": "temp-password-123",
  "description": "Compartilhamento para cliente",
  "allowed_ips": ["192.168.1.100", "10.0.0.50"]
}

# Acessar link compartilhado (público)
GET /api/v1/shared/{token}
# ou com senha:
POST /api/v1/shared/{token}
{
  "password": "temp-password-123"
}

# Listar links compartilhados de um secret
GET /api/v1/secrets/{secret_id}/shared-links

# Remover/cancelar link compartilhado
DELETE /api/v1/shared/{token}
```

#### **Como Testar:**

```bash
# 1. Criar compartilhamento
SECRET_ID="seu-secret-id"
SHARE_RESPONSE=$(curl -s -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"max_downloads":3,"expires_in_hours":24,"description":"Teste de compartilhamento"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/share)

echo $SHARE_RESPONSE

# 2. Extrair token do response
TOKEN=$(echo $SHARE_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['token'])")

# 3. Acessar link compartilhado (sem autenticação)
curl http://localhost:8000/api/v1/shared/$TOKEN

# 4. Testar com senha
curl -s -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"max_downloads":1,"expires_in_hours":1,"requires_password":true,"password":"test123"}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/share

# Acessar com senha
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"password":"test123"}' \
  http://localhost:8000/api/v1/shared/$NEW_TOKEN
```

---

## 👥 **3. CONTROLE DE ACESSO E PERMISSÕES**

### **3.1 Sistema de Roles**

#### **Funcionalidades:**
- ✅ **Super Admin**: Acesso global ao sistema
- ✅ **Company Admin**: Controle total da empresa
- ✅ **Project Manager**: Gerenciamento de projetos específicos
- ✅ **Developer**: Acesso a desenvolvimento
- ✅ **Viewer**: Apenas leitura
- ✅ **Auditor**: Acesso completo a logs
- ✅ Roles diferentes por empresa/projeto
- ✅ Permissões granulares customizáveis

#### **Permissões Disponíveis:**

```text
# Empresa
company:admin, company:read, company:billing

# Projetos  
project:admin, project:read, project:create

# Secrets
secret:admin, secret:read, secret:create, secret:update, secret:delete, secret:share

# Usuários
user:admin, user:read, user:invite

# Auditoria
audit:read, audit:admin, security:read, security:manage
```

### **3.2 Controle por Ambiente**

#### **Funcionalidades:**
- ✅ Ambientes configuráveis por projeto
- ✅ Permissões específicas por ambiente
- ✅ Controle granular (dev: full, staging: read/write, prod: read-only)
- ✅ Secrets isolados por ambiente
- ✅ Auditoria por ambiente

#### **Como Testar Permissões:**

```bash
# 1. Teste admin-token (deve ter acesso total)
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/companies/

# 2. Teste dev-token (acesso limitado a suas empresas)
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/companies/

# 3. Teste viewer-token (apenas leitura)
curl -H "Authorization: Bearer viewer-token" \
     http://localhost:8000/api/v1/secrets/

# 4. Teste criação com viewer (deve falhar)
curl -X POST \
  -H "Authorization: Bearer viewer-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","content":"test"}' \
  http://localhost:8000/api/v1/secrets/

# 5. Teste sem token (deve falhar)
curl http://localhost:8000/api/v1/secrets/
```

---

## 📊 **4. AUDITORIA E LOGS**

### **4.1 Sistema de Auditoria**

#### **Funcionalidades:**
- ✅ Log completo de todas as operações
- ✅ Níveis de auditoria (low, medium, high, critical)
- ✅ Metadados detalhados (IP, user-agent, timestamp)
- ✅ Correlação de eventos
- ✅ Busca e filtros avançados
- ✅ Retenção configurável
- ✅ Export de relatórios

#### **Como Usar:**

```bash
# Listar logs de auditoria
GET /api/v1/audit/logs?page=1&size=20

# Filtrar por ação
GET /api/v1/audit/logs?action=secret_create&start_date=2024-01-01

# Filtrar por usuário
GET /api/v1/audit/logs?user_id={user_id}&level=critical

# Obter log específico
GET /api/v1/audit/logs/{log_id}

# Logs de acesso de um secret
GET /api/v1/audit/access-logs/{secret_id}?hours=24

# Estatísticas de auditoria
GET /api/v1/audit/stats/summary?hours=168
```

### **4.2 Eventos de Segurança**

#### **Funcionalidades:**
- ✅ Detecção de anomalias
- ✅ Tentativas de acesso não autorizado
- ✅ Falhas de autenticação
- ✅ Acessos suspeitos
- ✅ Alertas automáticos
- ✅ Resolução de incidentes

#### **Como Usar:**

```bash
# Listar eventos de segurança
GET /api/v1/audit/security-events

# Filtrar por severidade
GET /api/v1/audit/security-events?severity=critical&is_resolved=pending

# Resolver evento
POST /api/v1/audit/security-events/{event_id}/resolve
{
  "resolution_notes": "Falso positivo - acesso autorizado"
}
```

#### **Como Testar:**

```bash
# 1. Realizar algumas ações para gerar logs
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/

curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Audit Test","content":"test"}' \
  http://localhost:8000/api/v1/secrets/

# 2. Ver logs gerados
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/audit/logs

# 3. Filtrar por ação específica
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/logs?action=secret_create"

# 4. Ver estatísticas
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/stats/summary?hours=24"

# 5. Testar acesso negado (gera evento de segurança)
curl -H "Authorization: Bearer invalid-token" \
     http://localhost:8000/api/v1/secrets/

# 6. Ver eventos de segurança
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/audit/security-events
```

---

## 🛡️ **5. SEGURANÇA E CRIPTOGRAFIA**

### **5.1 Criptografia**

#### **Funcionalidades:**
- ✅ AES-256-GCM via microserviço dedicado
- ✅ Chaves gerenciadas externamente
- ✅ Verificação de integridade (checksums)
- ✅ Re-criptografia automática
- ✅ Rotação de chaves
- ✅ HSM support (futuro)

#### **Como Testar Criptografia:**

```bash
# 1. Teste direto do crypto service
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"data":"test-data-to-encrypt","data_type":"text"}' \
  http://localhost:8002/v1/encrypt

# 2. Obter ID criptografado do response
ENCRYPTED_ID="id-retornado"

# 3. Descriptografar
curl http://localhost:8002/v1/decrypt/$ENCRYPTED_ID

# 4. Verificar integridade
curl http://localhost:8002/v1/verify/$ENCRYPTED_ID

# 5. Ver estatísticas do crypto service
curl http://localhost:8002/v1/stats
```

### **5.2 Autenticação e Autorização**

#### **Funcionalidades:**
- ✅ JWT tokens via MS-AuthManager
- ✅ Validação em tempo real
- ✅ Expiração automática
- ✅ Refresh tokens
- ✅ Session management
- ✅ Multi-factor authentication (futuro)

#### **Como Testar Auth:**

```bash
# 1. Validar token diretamente no auth service
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  http://localhost:8001/v1/validate-token

# 2. Obter informações do usuário
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8001/v1/users/550e8400-e29b-41d4-a716-446655440000

# 3. Verificar permissões
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"permission":"secret:admin"}' \
  http://localhost:8001/v1/users/550e8400-e29b-41d4-a716-446655440000/check-permission

# 4. Testar health do auth service
curl http://localhost:8001/health
```

---

## 🚀 **6. API E INTEGRAÇÃO**

### **6.1 API REST Completa**

#### **Funcionalidades:**
- ✅ RESTful design com OpenAPI 3.0
- ✅ Documentação automática (Swagger UI)
- ✅ Versionamento de API (/api/v1/)
- ✅ Rate limiting (preparado)
- ✅ CORS configurado
- ✅ Error handling padronizado
- ✅ Paginação em todas as listas
- ✅ Filtros e busca avançada

#### **Endpoints Principais:**

```text
# Organizacional
/api/v1/companies/            # Empresas
/api/v1/projects/             # Projetos  
/api/v1/users/                # Usuários
/api/v1/teams/                # Equipes (futuro)

# Secrets
/api/v1/secrets/              # CRUD de secrets
/api/v1/secrets/{id}/versions # Versionamento
/api/v1/secrets/{id}/share    # Compartilhamento
/api/v1/shared/{token}        # Acesso público

# Auditoria
/api/v1/audit/logs            # Logs de auditoria
/api/v1/audit/security-events # Eventos de segurança
/api/v1/audit/stats           # Estatísticas

# Sistema
/health                       # Health check
/status                       # Status detalhado
/api/v1/docs                  # Documentação
```

### **6.2 Documentação Automática**

#### **Como Acessar:**
- **Swagger UI**: http://localhost:8000/api/v1/docs
- **ReDoc**: http://localhost:8000/api/v1/redoc
- **OpenAPI JSON**: http://localhost:8000/api/v1/openapi.json

#### **Como Usar Swagger:**

```text
1. Abra http://localhost:8000/api/v1/docs
2. Clique em "Authorize"
3. Digite: admin-token (ou dev-token, viewer-token)
4. Clique "Authorize"
5. Teste qualquer endpoint diretamente na interface
6. Veja exemplos de request/response
7. Baixe client SDKs automaticamente
```

---

## 🧪 **7. AMBIENTE DE TESTES**

### **7.1 Tokens de Teste Disponíveis**

```bash
# Admin completo (João Silva - CTO Vinci Code)
admin-token
- Empresa: Vinci Code (company_admin)
- Permissões: Todas (company:admin, project:admin, secret:admin, user:admin, audit:admin)

# Developer multi-empresa (Maria Santos)
dev-token  
- Empresas: 
  * Vinci Code (developer) - permissões limitadas
  * Startup ABC (project_manager) - permissões de projeto
- Permissões: Variáveis por empresa

# Viewer/Auditor (Pedro Viewer)
viewer-token
- Empresa: Vinci Code (viewer)
- Permissões: Apenas leitura (secret:read, audit:read)
```

### **7.2 Dados Mock Incluídos**

```json
{
  "companies": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440001",
      "name": "Vinci Code",
      "slug": "vinci-code",
      "type": "agency",
      "status": "active"
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440003", 
      "name": "Startup ABC",
      "slug": "startup-abc",
      "type": "startup",
      "status": "trial"
    }
  ],
  "users": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "admin@vincicode.com",
      "name": "João Silva",
      "title": "CTO",
      "companies": ["Vinci Code (admin)"]
    },
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "email": "dev@vincicode.com", 
      "name": "Maria Santos",
      "title": "Full Stack Developer",
      "companies": ["Vinci Code (dev)", "Startup ABC (pm)"]
    }
  ]
}
```

### **7.3 Scripts de Teste Automatizado**

```bash
# Teste completo do sistema
./scripts/quick-test.sh

# Testes específicos
python -m pytest tests/

# Teste com cobertura
python -m pytest --cov=app tests/

# Teste de carga (futuro)
./scripts/load-test.sh
```

---

## 📋 **8. WORKFLOWS COMPLETOS DE TESTE**

### **8.1 Workflow: Empresa Nova**

```bash
# 1. Criar empresa
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Acme Corp","slug":"acme-corp","type":"enterprise","max_users":100}' \
  http://localhost:8000/api/v1/companies/

# 2. Obter ID da empresa criada
COMPANY_ID="uuid-retornado"

# 3. Criar projeto
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Main App","slug":"main-app","company_id":"'$COMPANY_ID'","environments":["dev","staging","prod"]}' \
  http://localhost:8000/api/v1/projects/

# 4. Obter ID do projeto
PROJECT_ID="uuid-retornado"

# 5. Criar secrets por ambiente
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"DB_PASSWORD","content":"dev-password","type":"text","project_id":"'$PROJECT_ID'","environment":"dev"}' \
  http://localhost:8000/api/v1/secrets/

curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"DB_PASSWORD","content":"prod-password","type":"text","project_id":"'$PROJECT_ID'","environment":"prod"}' \
  http://localhost:8000/api/v1/secrets/

# 6. Ver todos os secrets da empresa
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/secrets/?project_id=$PROJECT_ID"
```

### **8.2 Workflow: Colaboração Multi-Empresa**

```bash
# 1. Contexto inicial (Maria como dev na Vinci Code)
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/users/me

# 2. Ver empresas disponíveis
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/companies/

# 3. Trocar para Startup ABC (onde é project manager)
curl -X POST \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"company_id":"550e8400-e29b-41d4-a716-446655440003"}' \
  http://localhost:8000/api/v1/users/me/switch-company

# 4. Verificar mudança de contexto e permissões
curl -H "Authorization: Bearer dev-token" \
     http://localhost:8000/api/v1/users/me

# 5. Agora pode criar secrets na Startup ABC
curl -X POST \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"API_KEY","content":"startup-api-key","type":"api_key"}' \
  http://localhost:8000/api/v1/secrets/

# 6. Voltar para Vinci Code
curl -X POST \
  -H "Authorization: Bearer dev-token" \
  -H "Content-Type: application/json" \
  -d '{"company_id":"550e8400-e29b-41d4-a716-446655440001"}' \
  http://localhost:8000/api/v1/users/me/switch-company
```

### **8.3 Workflow: Auditoria e Compliance**

```bash
# 1. Gerar atividade auditável
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Critical Secret","content":"super-secret","type":"text","environment":"prod"}' \
  http://localhost:8000/api/v1/secrets/

SECRET_ID="uuid-retornado"

# 2. Acessar conteúdo
curl -H "Authorization: Bearer admin-token" \
     http://localhost:8000/api/v1/secrets/$SECRET_ID/content

# 3. Compartilhar secret
curl -X POST \
  -H "Authorization: Bearer admin-token" \
  -H "Content-Type: application/json" \
  -d '{"max_downloads":1,"expires_in_hours":24}' \
  http://localhost:8000/api/v1/secrets/$SECRET_ID/share

# 4. Ver logs de auditoria
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/logs?action=secret_create"

# 5. Ver acessos específicos do secret
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/access-logs/$SECRET_ID?hours=24"

# 6. Relatório de atividade das últimas 24h
curl -H "Authorization: Bearer admin-token" \
     "http://localhost:8000/api/v1/audit/stats/summary?hours=24"
```

---

## 🎯 **RESUMO DE FUNCIONALIDADES**

### **✅ Organizacional**
- [x] Empresas multi-tenant
- [x] Usuários multi-empresa  
- [x] Projetos por empresa
- [x] Roles e permissões hierárquicas
- [x] Sistema de convites (interfaces criadas)

### **✅ Secrets Management**
- [x] CRUD completo de secrets
- [x] 8 tipos de secret suportados
- [x] Versionamento com histórico
- [x] Compartilhamento seguro
- [x] Expiração automática
- [x] Tags e metadados

### **✅ Segurança**
- [x] Criptografia AES-256
- [x] Autenticação JWT
- [x] Controle granular de acesso
- [x] Isolamento multi-tenant
- [x] Auditoria completa
- [x] Verificação de integridade

### **✅ API e Integração**
- [x] API REST completa
- [x] Documentação automática
- [x] Filtros e paginação
- [x] Error handling padronizado
- [x] Health checks
- [x] Mocks funcionais

### **✅ DevOps e Deploy**
- [x] Docker containerizado
- [x] Docker Compose completo
- [x] Mocks para desenvolvimento
- [x] Scripts de teste
- [x] Configuração por ambiente
- [x] Logs estruturados

---

## 🚀 **PRÓXIMOS PASSOS**

### **Implementação Faltante (1-2 semanas)**
- [ ] Sistema de convites completo
- [ ] Interface web básica
- [ ] CLI para desenvolvedores
- [ ] Testes de integração completos

### **Features Enterprise (1-2 meses)**
- [ ] Dashboard analytics
- [ ] Billing e quotas
- [ ] Backup automatizado
- [ ] SSO integration
- [ ] Advanced monitoring

**🎉 O CryptVault está pronto para uso em desenvolvimento e demo, com arquitetura enterprise preparada para escalar para produção!**
