-- Script de inicialização do banco de dados PostgreSQL
-- Executado automaticamente quando o container é criado

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- Para índices compostos com JSONB
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- Para busca por similaridade

-- Configurações de timezone
SET timezone = 'UTC';

-- Criação de índices otimizados será feita via Alembic migrations

-- Configurações de performance para desenvolvimento
-- Em produção, essas configurações devem ser ajustadas conforme o hardware
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;

-- Configurações de logging para auditoria
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_duration = on;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Recarrega configurações
SELECT pg_reload_conf();
