# Multi-stage build para otimização
FROM python:3.11-slim as builder

# Instala dependências do sistema necessárias para build
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Configura diretório de trabalho
WORKDIR /app

# Copia arquivos de dependências
COPY requirements.txt pyproject.toml ./

# Instala dependências Python
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Stage de produção
FROM python:3.11-slim

# Instala dependências de runtime
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r cryptvault \
    && useradd -r -g cryptvault cryptvault

# Copia dependências do stage builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Configura diretório de trabalho
WORKDIR /app

# Copia código da aplicação
COPY . .

# Configura permissões
RUN chown -R cryptvault:cryptvault /app

# Muda para usuário não-root
USER cryptvault

# Healthcheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expõe porta
EXPOSE 8000

# Comando padrão
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

