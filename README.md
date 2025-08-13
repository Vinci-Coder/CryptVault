# CryptVault - Sistema Seguro de Gerenciamento de Secrets

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-red.svg)
![License](https://img.shields.io/badge/license-Proprietary-yellow.svg)

## Visão Geral

O CryptVault é um sistema seguro de armazenamento, gerenciamento e compartilhamento de secrets e arquivos sensíveis (.env, chaves de API, certificados, configurações críticas). Oferece versionamento, criptografia forte e controle granular de acesso.

### Características Principais

- 🔐 **Criptografia AES-256** via microserviço dedicado
- 🔄 **Versionamento completo** de secrets
- 👥 **Controle de acesso granular** por usuários, grupos e empresas
- 📝 **Auditoria completa** de todas as operações
- 🔗 **Compartilhamento seguro** via links temporários
- 🏢 **Multi-tenant** com isolamento por empresa
- 🚀 **API REST** para integração
- 📊 **Monitoramento e métricas**

## Arquitetura

### Core API (Este Repositório)
- **Backend**: Python 3.11+ com FastAPI
- **Banco de Dados**: PostgreSQL com SQLAlchemy 2.0
- **Cache**: Redis para sessões e dados temporários
- **Autenticação**: Integração com MS-AuthManager
- **Criptografia**: Integração com microserviço Go (futuro)

### Dependências Externas
- **MS-AuthManager**: Gerenciamento de usuários e permissões
- **Crypto Service**: Microserviço de criptografia (será implementado em Go)

## Instalação e Desenvolvimento

### Pré-requisitos

- Python 3.11+
- Docker e Docker Compose
- PostgreSQL 15+
- Redis 7+

### Configuração Rápida

1. **Clone o repositório**
```bash
git clone <repository-url>
cd Back-End-CryptVault
```

2. **Configure variáveis de ambiente**
```bash
cp env.example .env
# Edite o arquivo .env conforme necessário
```

3. **Execute com Docker Compose**
```bash
docker-compose up -d
```

A aplicação estará disponível em:
- API: http://localhost:8000
- Documentação: http://localhost:8000/api/v1/docs
- Adminer (DB): http://localhost:8080

### Desenvolvimento Local

1. **Instale dependências**
```bash
pip install -r requirements.txt
```

2. **Configure banco de dados**
```bash
# Inicie PostgreSQL e Redis
docker-compose up -d postgres redis

# Execute migrations
alembic upgrade head
```

3. **Execute a aplicação**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Testes

```bash
# Testes unitários
pytest

# Testes com cobertura
pytest --cov=app

# Testes específicos
pytest tests/test_api/test_secrets.py -v
```

## Uso da API

### Autenticação

Todas as requisições requerem autenticação via token Bearer:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/v1/secrets/
```

### Exemplos de Endpoints

#### Criar Secret
```bash
POST /api/v1/secrets/
{
  "name": "Database Password",
  "description": "Senha do banco de produção",
  "content": "super-secret-password",
  "type": "text",
  "environment": "prod",
  "tags": ["database", "critical"]
}
```

#### Listar Secrets
```bash
GET /api/v1/secrets/?page=1&size=20&type=text&environment=prod
```

#### Obter Conteúdo de Secret
```bash
GET /api/v1/secrets/{id}/content
```

#### Criar Link de Compartilhamento
```bash
POST /api/v1/secrets/{id}/share
{
  "max_downloads": 5,
  "expires_in_hours": 24,
  "requires_password": true,
  "password": "temp-password"
}
```

### Versionamento

```bash
# Listar versões
GET /api/v1/secrets/{id}/versions

# Obter versão específica
GET /api/v1/secrets/{id}/versions/{version_number}/content

# Restaurar versão
POST /api/v1/secrets/{id}/versions/{version_number}/restore
```

### Auditoria

```bash
# Logs de auditoria
GET /api/v1/audit/logs?action=secret_create&start_date=2024-01-01

# Eventos de segurança
GET /api/v1/audit/security-events?severity=critical

# Logs de acesso de um secret
GET /api/v1/audit/access-logs/{secret_id}?hours=24
```

## Estrutura do Projeto

```
app/
├── api/                 # Endpoints da API
│   ├── deps.py         # Dependências (autenticação, DB)
│   └── v1/             # Versão 1 da API
├── core/               # Configurações centrais
│   ├── config.py       # Configurações da aplicação
│   ├── security.py     # JWT e autenticação
│   └── logging.py      # Sistema de logs
├── db/                 # Banco de dados
│   └── database.py     # Configuração SQLAlchemy
├── models/             # Modelos SQLAlchemy
│   ├── base.py         # Classe base
│   ├── secret.py       # Modelos de secrets
│   └── audit.py        # Modelos de auditoria
├── schemas/            # Schemas Pydantic
├── services/           # Lógica de negócio
│   ├── crypto_service.py    # Interface crypto
│   ├── auth_service.py      # Interface auth
│   ├── secret_service.py    # Lógica de secrets
│   ├── version_service.py   # Versionamento
│   └── audit_service.py     # Auditoria
└── main.py             # Aplicação FastAPI
```

## Configuração

### Variáveis de Ambiente

| Variável | Descrição | Padrão |
|----------|-----------|---------|
| `DATABASE_URL` | URL do PostgreSQL | - |
| `REDIS_URL` | URL do Redis | `redis://localhost:6379/0` |
| `JWT_SECRET_KEY` | Chave para JWT | - |
| `AUTH_MANAGER_URL` | URL do MS-AuthManager | - |
| `CRYPTO_SERVICE_URL` | URL do serviço de criptografia | - |
| `DEBUG` | Modo debug | `false` |
| `LOG_LEVEL` | Nível de log | `INFO` |

### Permissões

O sistema utiliza permissões granulares:

- `secret:create` - Criar secrets
- `secret:read` - Ler secrets
- `secret:update` - Atualizar secrets
- `secret:delete` - Deletar secrets
- `secret:share` - Compartilhar secrets
- `audit:read` - Ler logs de auditoria
- `audit:admin` - Administrar auditoria
- `security:read` - Ler eventos de segurança
- `security:manage` - Gerenciar eventos de segurança

## Segurança

### Princípios

1. **Criptografia em Repouso**: Todos os secrets são criptografados via AES-256
2. **Criptografia em Trânsito**: HTTPS obrigatório em produção
3. **Autenticação**: JWT com MS-AuthManager
4. **Autorização**: Permissões granulares por recurso
5. **Auditoria**: Log completo de todas as operações
6. **Isolamento**: Multi-tenant com separação por empresa

### Boas Práticas

- Rotação regular de chaves de criptografia
- Monitoramento de eventos de segurança
- Backup seguro dos dados
- Rate limiting em endpoints críticos
- Validação rigorosa de entrada

## Monitoramento

### Health Checks

```bash
# Status básico
GET /health

# Status detalhado
GET /status
```

### Métricas

- Logs estruturados em JSON
- Integração com Prometheus (futuro)
- Dashboards Grafana (futuro)
- Alertas para eventos críticos

## Deployment

### Docker

```bash
# Build da imagem
docker build -t cryptvault-core .

# Execução
docker run -p 8000:8000 --env-file .env cryptvault-core
```

### CapRover

```bash
# Deploy via CapRover (configurar captain-definition)
tar -czf app.tar.gz *
# Upload via interface do CapRover
```

### Kubernetes

```yaml
# Exemplo de deployment (implementar Helm charts)
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cryptvault-core
spec:
  replicas: 3
  # ... resto da configuração
```

## Roadmap

### Fase 1 - MVP ✅
- [x] API REST para CRUD de secrets
- [x] Versionamento básico
- [x] Autenticação via MS-AuthManager
- [x] Logs de auditoria
- [x] Docker e docker-compose

### Fase 2 - Avançada
- [ ] Interface web básica
- [ ] CLI para desenvolvedores
- [ ] Webhooks para eventos
- [ ] Busca avançada com tags
- [ ] Links de compartilhamento com senha

### Fase 3 - Enterprise
- [ ] Dashboard de compliance
- [ ] Integração com CI/CD
- [ ] Alertas inteligentes
- [ ] Backup automatizado
- [ ] Multi-region

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/amazing-feature`)
3. Commit suas mudanças (`git commit -m 'Add amazing feature'`)
4. Push para a branch (`git push origin feature/amazing-feature`)
5. Abra um Pull Request

## Licença

Proprietary - Vinci Code © 2024

## Suporte

- **Documentação**: http://localhost:8000/api/v1/docs
- **Issues**: GitHub Issues
- **Email**: dev@vincicode.com

