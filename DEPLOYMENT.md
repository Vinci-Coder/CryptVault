# Guia de Deploy - CryptVault

Este documento descreve como fazer o deploy do CryptVault em diferentes ambientes.

## Pré-requisitos

- Docker e Docker Compose
- PostgreSQL 15+
- Redis 7+
- MS-AuthManager configurado
- Microserviço de Criptografia (futuro)

## Desenvolvimento

### Setup Rápido

```bash
# Clone e configure
git clone <repo>
cd Back-End-CryptVault
cp env.example .env

# Execute o script de setup (Linux/Mac)
./scripts/dev-setup.sh

# Ou manualmente:
docker-compose up -d
```

### Configuração Manual

1. **Banco de Dados**
```bash
docker-compose up -d postgres redis
```

2. **Migrations**
```bash
# Instale dependências
pip install -r requirements.txt

# Execute migrations
alembic upgrade head
```

3. **Aplicação**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Staging

### Docker Compose

```yaml
# docker-compose.staging.yml
version: '3.8'
services:
  cryptvault-core:
    image: cryptvault-core:latest
    environment:
      - ENVIRONMENT=staging
      - DEBUG=false
      - DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/cryptvault_staging
      - AUTH_MANAGER_URL=https://auth-staging.vincicode.com
      - CRYPTO_SERVICE_URL=https://crypto-staging.vincicode.com
    ports:
      - "8000:8000"
    restart: unless-stopped
```

### Build e Deploy

```bash
# Build da imagem
docker build -t cryptvault-core:latest .

# Deploy
docker-compose -f docker-compose.staging.yml up -d
```

## Produção

### CapRover

1. **Preparação**
```bash
# Crie captain-definition
echo '{"schemaVersion":2,"dockerfilePath":"./Dockerfile"}' > captain-definition

# Crie arquivo tar
tar -czf app.tar.gz *
```

2. **Deploy via Interface**
- Acesse painel do CapRover
- Upload do arquivo app.tar.gz
- Configure variáveis de ambiente

3. **Configuração de Variáveis**
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@postgres:5432/cryptvault_prod
REDIS_URL=redis://redis:6379/0
JWT_SECRET_KEY=<strong-secret-key>
SECRET_KEY=<strong-app-secret>
AUTH_MANAGER_URL=https://auth.vincicode.com
CRYPTO_SERVICE_URL=https://crypto.vincicode.com
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=WARNING
```

### Kubernetes

1. **Namespace**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: cryptvault
```

2. **ConfigMap**
```yaml
# configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cryptvault-config
  namespace: cryptvault
data:
  ENVIRONMENT: "production"
  DEBUG: "false"
  LOG_LEVEL: "INFO"
  API_V1_STR: "/api/v1"
```

3. **Secret**
```yaml
# secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: cryptvault-secrets
  namespace: cryptvault
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://user:pass@postgres:5432/cryptvault_prod"
  JWT_SECRET_KEY: "your-jwt-secret"
  SECRET_KEY: "your-app-secret"
```

4. **Deployment**
```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: cryptvault-core
  namespace: cryptvault
spec:
  replicas: 3
  selector:
    matchLabels:
      app: cryptvault-core
  template:
    metadata:
      labels:
        app: cryptvault-core
    spec:
      containers:
      - name: cryptvault-core
        image: cryptvault-core:latest
        ports:
        - containerPort: 8000
        envFrom:
        - configMapRef:
            name: cryptvault-config
        - secretRef:
            name: cryptvault-secrets
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

5. **Service**
```yaml
# service.yaml
apiVersion: v1
kind: Service
metadata:
  name: cryptvault-service
  namespace: cryptvault
spec:
  selector:
    app: cryptvault-core
  ports:
  - port: 80
    targetPort: 8000
  type: ClusterIP
```

6. **Ingress**
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cryptvault-ingress
  namespace: cryptvault
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.cryptvault.vincicode.com
    secretName: cryptvault-tls
  rules:
  - host: api.cryptvault.vincicode.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: cryptvault-service
            port:
              number: 80
```

## Banco de Dados

### Migrations em Produção

```bash
# Backup antes de migration
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d_%H%M%S).sql

# Execute migration
alembic upgrade head

# Verifique status
alembic current
```

### Backup Automatizado

```bash
#!/bin/bash
# backup-db.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DATABASE_URL="postgresql://user:pass@host:5432/cryptvault_prod"

# Backup do banco
pg_dump $DATABASE_URL | gzip > $BACKUP_DIR/cryptvault_$DATE.sql.gz

# Remove backups antigos (mantém 30 dias)
find $BACKUP_DIR -name "cryptvault_*.sql.gz" -mtime +30 -delete

echo "Backup concluído: cryptvault_$DATE.sql.gz"
```

## Monitoramento

### Health Checks

```bash
# Health check básico
curl -f http://localhost:8000/health

# Status detalhado
curl http://localhost:8000/status
```

### Logs

```bash
# Logs da aplicação
docker-compose logs -f cryptvault-core

# Logs do banco
docker-compose logs -f postgres

# Logs estruturados
tail -f logs/app.log | jq '.'
```

### Métricas (Futuro)

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'cryptvault'
    static_configs:
      - targets: ['cryptvault-core:8000']
    metrics_path: '/metrics'
```

## Segurança

### SSL/TLS

```bash
# Certbot para Let's Encrypt
certbot --nginx -d api.cryptvault.vincicode.com
```

### Firewall

```bash
# UFW (Ubuntu)
ufw allow 22/tcp      # SSH
ufw allow 80/tcp      # HTTP
ufw allow 443/tcp     # HTTPS
ufw deny 8000/tcp     # Aplicação (via proxy)
ufw deny 5432/tcp     # PostgreSQL
ufw deny 6379/tcp     # Redis
```

### Backup de Secrets

```bash
# Backup dos dados criptografados
kubectl exec -n cryptvault deployment/cryptvault-core -- \
  pg_dump $DATABASE_URL --table=secrets --table=secret_versions > secrets_backup.sql
```

## Troubleshooting

### Problemas Comuns

1. **Erro de Conexão com Banco**
```bash
# Verifique conectividade
pg_isready -h postgres -p 5432 -U cryptvault

# Logs do PostgreSQL
docker-compose logs postgres
```

2. **Erro de Autenticação**
```bash
# Verifique MS-AuthManager
curl -H "X-API-Key: $AUTH_MANAGER_API_KEY" $AUTH_MANAGER_URL/health

# Logs de auth
grep "authentication" logs/app.log
```

3. **Erro de Criptografia**
```bash
# Verifique Crypto Service
curl -H "Authorization: Bearer $CRYPTO_SERVICE_API_KEY" $CRYPTO_SERVICE_URL/health

# Logs de crypto
grep "crypto" logs/app.log
```

### Comandos de Debug

```bash
# Conectar ao container
docker exec -it cryptvault-core_cryptvault-core_1 bash

# Verificar variáveis de ambiente
docker exec cryptvault-core env

# Logs em tempo real
docker-compose logs -f --tail=100

# Status dos serviços
docker-compose ps
```

## Rollback

### Docker Compose

```bash
# Rollback para versão anterior
docker-compose down
docker pull cryptvault-core:previous-version
docker-compose up -d
```

### Kubernetes

```bash
# Rollback do deployment
kubectl rollout undo deployment/cryptvault-core -n cryptvault

# Verificar status
kubectl rollout status deployment/cryptvault-core -n cryptvault
```

### Banco de Dados

```bash
# Rollback de migration
alembic downgrade -1

# Restaurar backup
psql $DATABASE_URL < backup_20240101_120000.sql
```

