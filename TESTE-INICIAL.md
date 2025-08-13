# 🧪 Guia para Primeiros Testes do CryptVault

## ❌ O que Falta para Funcionar Completamente

### 1. **Problemas Críticos Identificados**

#### 🔴 **Incompatibilidade Pydantic v1 vs v2**
```python
# ❌ PROBLEMA: app/core/config.py linha 5
from pydantic import BaseSettings, validator

# ✅ SOLUÇÃO: Pydantic v2 syntax
from pydantic_settings import BaseSettings
from pydantic import field_validator
```

#### 🔴 **Dependências dos Serviços Externos**
- **MS-AuthManager**: Não existe (precisa ser mockado)
- **Crypto Service**: Não existe (precisa ser mockado)
- **Mocks atuais**: São apenas arquivos estáticos

#### 🔴 **Problemas de Importação**
```python
# ❌ PROBLEMA: Várias importações circulares potenciais
# ❌ PROBLEMA: Modelos não importados no __init__.py
```

### 2. **Componentes que Precisam de Mock Funcional**

#### **MS-AuthManager Mock**
```python
# Precisa responder a:
POST /v1/validate-token
GET /v1/users/{id}
GET /v1/users/{id}/permissions
POST /v1/users/{id}/check-permission
```

#### **Crypto Service Mock**
```python
# Precisa responder a:
POST /v1/encrypt
GET /v1/decrypt/{id}
DELETE /v1/encrypted/{id}
GET /v1/verify/{id}
```

## 🔧 Correções Necessárias (Ordem de Prioridade)

### **PASSO 1: Corrigir Configurações (CRÍTICO)**
```python
# app/core/config.py - Linha 5
from pydantic_settings import BaseSettings
from pydantic import field_validator

# Substituir @validator por @field_validator
@field_validator("BACKEND_CORS_ORIGINS", mode="before")
@classmethod
def assemble_cors_origins(cls, v):
    # ... resto do código
```

### **PASSO 2: Atualizar requirements.txt**
```txt
# Adicionar:
pydantic-settings==2.1.0

# Verificar compatibilidade:
pydantic==2.5.0  # ✅ Já correto
```

### **PASSO 3: Criar Mocks Funcionais**

#### Mock do AuthManager:
```python
# mock_auth_manager.py
from fastapi import FastAPI
import uuid

app = FastAPI()

@app.post("/v1/validate-token")
async def validate_token():
    return {
        "user_id": str(uuid.uuid4()),
        "company_id": str(uuid.uuid4()),
        "email": "test@example.com",
        "name": "Test User",
        "roles": ["user"],
        "permissions": ["secret:read", "secret:create", "secret:update", "secret:delete"],
        "is_active": True
    }
```

#### Mock do Crypto Service:
```python
# mock_crypto_service.py
from fastapi import FastAPI
import uuid
import hashlib

app = FastAPI()

@app.post("/v1/encrypt")
async def encrypt_data(data: dict):
    return {
        "encrypted_id": str(uuid.uuid4()),
        "checksum": hashlib.sha256(data["data"].encode()).hexdigest(),
        "size": len(data["data"]),
        "encrypted_at": "2024-01-01T00:00:00Z"
    }

@app.get("/v1/decrypt/{encrypted_id}")
async def decrypt_data(encrypted_id: str):
    return {
        "data": "decrypted-content-mock",
        "checksum": "mock-checksum"
    }
```

### **PASSO 4: Corrigir Imports**
```python
# app/models/__init__.py
from .base import Base, BaseModel
from .secret import Secret, SecretVersion, SecretPermission, SharedLink
from .audit import AuditLog, SecurityEvent, AccessLog

__all__ = [
    "Base", "BaseModel",
    "Secret", "SecretVersion", "SecretPermission", "SharedLink",
    "AuditLog", "SecurityEvent", "AccessLog"
]
```

## 🚀 Setup para Teste Imediato

### **Opção 1: Docker com Mocks (RECOMENDADO)**

```bash
# 1. Criar mocks funcionais
mkdir -p mocks/services
```

```python
# mocks/services/auth_mock.py
from fastapi import FastAPI, HTTPException
import uuid

app = FastAPI(title="AuthManager Mock")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "auth-manager-mock"}

@app.post("/v1/validate-token")
async def validate_token():
    return {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "company_id": "550e8400-e29b-41d4-a716-446655440001", 
        "email": "admin@test.com",
        "name": "Admin Test",
        "roles": ["admin"],
        "permissions": [
            "secret:read", "secret:create", "secret:update", "secret:delete", "secret:share",
            "audit:read", "audit:admin", "security:read", "security:manage"
        ],
        "is_active": True
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
```

```python
# mocks/services/crypto_mock.py
from fastapi import FastAPI
import uuid
import hashlib
import base64

app = FastAPI(title="Crypto Service Mock")

# Simulação de storage em memória
encrypted_storage = {}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "crypto-service-mock"}

@app.post("/v1/encrypt")
async def encrypt_data(request: dict):
    encrypted_id = str(uuid.uuid4())
    content = request.get("data", "")
    
    # "Criptografia" mock (apenas base64)
    encrypted_content = base64.b64encode(content.encode()).decode()
    
    encrypted_storage[encrypted_id] = {
        "content": encrypted_content,
        "original_size": len(content),
        "metadata": request.get("metadata", {})
    }
    
    return {
        "encrypted_id": encrypted_id,
        "checksum": hashlib.sha256(content.encode()).hexdigest(),
        "size": len(content),
        "encrypted_at": "2024-01-01T12:00:00Z"
    }

@app.get("/v1/decrypt/{encrypted_id}")
async def decrypt_data(encrypted_id: str):
    if encrypted_id not in encrypted_storage:
        raise HTTPException(404, "Encrypted data not found")
    
    stored = encrypted_storage[encrypted_id]
    # "Descriptografia" mock
    decrypted = base64.b64decode(stored["content"]).decode()
    
    return {
        "data": decrypted,
        "data_type": "text",
        "metadata": stored["metadata"],
        "checksum": hashlib.sha256(decrypted.encode()).hexdigest()
    }

@app.delete("/v1/encrypted/{encrypted_id}")
async def delete_encrypted(encrypted_id: str):
    if encrypted_id in encrypted_storage:
        del encrypted_storage[encrypted_id]
    return {"success": True}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
```

### **Docker Compose Atualizado:**

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: cryptvault_db
      POSTGRES_USER: cryptvault
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  # Mock do AuthManager
  auth-mock:
    build:
      context: .
      dockerfile: Dockerfile.mock
    command: python mocks/services/auth_mock.py
    ports:
      - "8001:8001"

  # Mock do Crypto Service  
  crypto-mock:
    build:
      context: .
      dockerfile: Dockerfile.mock
    command: python mocks/services/crypto_mock.py
    ports:
      - "8002:8002"

  # CryptVault Core
  cryptvault-core:
    build: .
    environment:
      - DATABASE_URL=postgresql+asyncpg://cryptvault:password@postgres:5432/cryptvault_db
      - REDIS_URL=redis://redis:6379/0
      - AUTH_MANAGER_URL=http://auth-mock:8001
      - CRYPTO_SERVICE_URL=http://crypto-mock:8002
      - AUTH_MANAGER_API_KEY=mock-auth-key
      - CRYPTO_SERVICE_API_KEY=mock-crypto-key
      - JWT_SECRET_KEY=test-jwt-secret-key
      - SECRET_KEY=test-app-secret-key
      - DEBUG=true
      - ENVIRONMENT=development
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
      - auth-mock
      - crypto-mock

volumes:
  postgres_data:
```

## 📋 Teste Passo a Passo

### **PASSO 1: Verificar Dependências**
```bash
# Instalar dependências corretas
pip install --upgrade pydantic pydantic-settings

# Verificar versões
python -c "import pydantic; print(pydantic.VERSION)"
# Deve ser >= 2.5.0
```

### **PASSO 2: Teste Local Mínimo**
```bash
# 1. Configurar ambiente
cp env.example .env

# 2. Editar .env
DATABASE_URL=postgresql+asyncpg://cryptvault:password@localhost:5432/cryptvault_db
REDIS_URL=redis://localhost:6379/0
AUTH_MANAGER_URL=http://localhost:8001
CRYPTO_SERVICE_URL=http://localhost:8002
AUTH_MANAGER_API_KEY=mock-key
CRYPTO_SERVICE_API_KEY=mock-key
JWT_SECRET_KEY=test-secret-key
SECRET_KEY=test-app-secret

# 3. Subir apenas banco e redis
docker-compose up -d postgres redis

# 4. Executar migrations
python -m alembic upgrade head

# 5. Executar mocks em terminais separados
python mocks/services/auth_mock.py
python mocks/services/crypto_mock.py

# 6. Executar aplicação
python -m uvicorn app.main:app --reload
```

### **PASSO 3: Testes de API**

```bash
# 1. Health check
curl http://localhost:8000/health

# 2. Status (verificar serviços externos)
curl http://localhost:8000/status

# 3. Documentação
# Abrir http://localhost:8000/api/v1/docs
```

### **PASSO 4: Teste com Token Mock**

```bash
# 1. Obter token mock do auth service
curl -X POST http://localhost:8001/v1/validate-token

# 2. Usar token para criar secret
curl -X POST \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test Secret","content":"my-secret-value","type":"text"}' \
  http://localhost:8000/api/v1/secrets/

# 3. Listar secrets
curl -H "Authorization: Bearer mock-token" \
  http://localhost:8000/api/v1/secrets/
```

## 🔍 O que Esperar nos Primeiros Testes

### **✅ Deve Funcionar:**
- Health checks (/health, /status)
- Documentação automática (/api/v1/docs)
- Conexão com banco de dados
- Migrations automáticas
- Logs estruturados

### **⚠️ Pode Falhar (Esperado):**
- Criação de secrets (requer mocks funcionais)
- Autenticação real (requer token válido)
- Criptografia (requer crypto service)

### **🐛 Problemas Comuns Esperados:**

1. **Pydantic v1/v2 conflict**
   ```
   ImportError: cannot import name 'BaseSettings' from 'pydantic'
   ```
   **Solução**: Instalar `pydantic-settings`

2. **Conexão com serviços externos**
   ```
   httpx.ConnectError: [Errno 111] Connection refused
   ```
   **Solução**: Mocks não estão rodando

3. **Variáveis de ambiente faltando**
   ```
   pydantic.error_wrappers.ValidationError: field required
   ```
   **Solução**: Configurar .env corretamente

## 🎯 Próximas Melhorias (Ordem de Prioridade)

### **Imediato (1-2 dias)**
1. ✅ Corrigir configurações Pydantic v2
2. ✅ Criar mocks funcionais para auth e crypto
3. ✅ Adicionar fixtures de teste com dados mock
4. ✅ Documentar fluxo de teste completo

### **Curto Prazo (1 semana)**
1. 🔄 Implementar CLI básico para testes
2. 🔄 Adicionar seed data para desenvolvimento
3. 🔄 Melhorar error handling
4. 🔄 Adicionar rate limiting

### **Médio Prazo (2-4 semanas)**
1. 📋 Interface web básica
2. 📋 Crypto service real em Go
3. 📋 MS-AuthManager real
4. 📋 Testes de integração completos

## 💡 Dicas para Desenvolvimento

### **Debug Mode**
```python
# Para debug detalhado, adicionar no .env:
DEBUG=true
LOG_LEVEL=DEBUG

# Logs aparecerão em formato legível
```

### **Teste Incremental**
```bash
# 1. Teste apenas a aplicação
python -c "from app.main import app; print('Import OK')"

# 2. Teste conexão DB
python -c "from app.db.database import engine; print('DB Config OK')"

# 3. Teste models
python -c "from app.models.secret import Secret; print('Models OK')"

# 4. Teste services
python -c "from app.services.crypto_service import crypto_service; print('Services OK')"
```

### **Monitoramento**
```bash
# Logs em tempo real
docker-compose logs -f cryptvault-core

# Verificar recursos
docker stats

# Verificar banco
docker exec -it postgres psql -U cryptvault -d cryptvault_db -c "\dt"
```

Este guia deve permitir que você execute os primeiros testes do CryptVault em menos de 30 minutos, identificando e corrigindo os problemas principais antes de partir para funcionalidades mais avançadas.

