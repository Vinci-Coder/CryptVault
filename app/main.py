"""
Aplicação principal FastAPI do CryptVault
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1 import secrets, versions, audit
from app.api.deps import get_db
from app.db.database import create_tables


# Configura logging
configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação"""
    
    # Startup
    logger.info("Starting CryptVault application", version=settings.VERSION)
    
    try:
        # Cria tabelas se necessário (em produção usar Alembic)
        if settings.DEBUG:
            await create_tables()
            logger.info("Database tables created/verified")
    
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down CryptVault application")


# Cria a aplicação FastAPI
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema seguro de armazenamento e gerenciamento de secrets",
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DEBUG else None,
    docs_url=f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
    redoc_url=f"{settings.API_V1_STR}/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Middleware de CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Middleware de Trusted Host (segurança)
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["localhost", "127.0.0.1", "*.vincicode.com"]
    )


# Middleware para logging de requisições
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log de todas as requisições"""
    start_time = time.time()
    
    # Log da requisição
    logger.info(
        "Request received",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else "unknown",
        user_agent=request.headers.get("user-agent", "unknown")
    )
    
    response = await call_next(request)
    
    # Log da resposta
    process_time = time.time() - start_time
    logger.info(
        "Request completed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=round(process_time, 3)
    )
    
    # Adiciona headers de resposta
    response.headers["X-Process-Time"] = str(process_time)
    response.headers["X-API-Version"] = settings.VERSION
    
    return response


# Handler de exceções globais
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handler global para exceções não tratadas"""
    
    logger.error(
        "Unhandled exception",
        method=request.method,
        url=str(request.url),
        error=str(exc),
        exc_info=True
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_id": str(int(time.time())),
            "message": "An unexpected error occurred"
        }
    )


# Rotas de saúde e status
@app.get("/health")
async def health_check():
    """Endpoint de health check"""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": time.time()
    }


@app.get("/status")
async def status_check():
    """Endpoint de status detalhado"""
    from app.services.crypto_service import crypto_service
    from app.services.auth_service import auth_service
    
    # Verifica serviços externos
    crypto_status = await crypto_service.client.health_check()
    auth_status = await auth_service.client.health_check()
    
    return {
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database": "connected",  # TODO: Implementar check real
        "external_services": {
            "crypto_service": crypto_status,
            "auth_manager": auth_status
        },
        "timestamp": time.time()
    }


# Inclui routers da API
from app.api.v1 import companies, projects, users

app.include_router(
    companies.router,
    prefix=f"{settings.API_V1_STR}/companies",
    tags=["companies"]
)

app.include_router(
    projects.router,
    prefix=f"{settings.API_V1_STR}/projects",
    tags=["projects"]
)

app.include_router(
    users.router,
    prefix=f"{settings.API_V1_STR}/users",
    tags=["users"]
)

app.include_router(
    secrets.router,
    prefix=f"{settings.API_V1_STR}/secrets",
    tags=["secrets"]
)

app.include_router(
    versions.router,
    prefix=f"{settings.API_V1_STR}/secrets",
    tags=["versions"]
)

app.include_router(
    audit.router,
    prefix=f"{settings.API_V1_STR}/audit",
    tags=["audit"]
)


# Rota raiz
@app.get("/")
async def root():
    """Endpoint raiz da API"""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs" if settings.DEBUG else None,
        "status": f"/status",
        "health": f"/health"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
