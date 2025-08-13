"""
Configuração de logging estruturado
"""
import logging
import sys
from typing import Any, Dict
import structlog
from loguru import logger
from app.core.config import settings


def configure_logging() -> None:
    """Configura o sistema de logging estruturado"""
    
    # Remove handlers padrão do loguru
    logger.remove()
    
    # Configura formato baseado na configuração
    if settings.LOG_FORMAT == "json":
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            serialize=True,
        )
    else:
        logger.add(
            sys.stdout,
            level=settings.LOG_LEVEL,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | {message}",
        )
    
    # Configura structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if settings.LOG_FORMAT == "json"
            else structlog.dev.ConsoleRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> Any:
    """Retorna um logger estruturado"""
    return structlog.get_logger(name)


class AuditLogger:
    """Logger especializado para auditoria"""
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_secret_access(
        self,
        user_id: str,
        secret_id: str,
        action: str,
        ip_address: str,
        user_agent: str,
        **kwargs: Any
    ) -> None:
        """Log de acesso a secrets"""
        self.logger.info(
            "secret_access",
            user_id=user_id,
            secret_id=secret_id,
            action=action,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )
    
    def log_secret_modification(
        self,
        user_id: str,
        secret_id: str,
        action: str,
        changes: Dict[str, Any],
        ip_address: str,
        **kwargs: Any
    ) -> None:
        """Log de modificação de secrets"""
        self.logger.info(
            "secret_modification",
            user_id=user_id,
            secret_id=secret_id,
            action=action,
            changes=changes,
            ip_address=ip_address,
            **kwargs
        )
    
    def log_authentication(
        self,
        user_id: str,
        action: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        **kwargs: Any
    ) -> None:
        """Log de eventos de autenticação"""
        self.logger.info(
            "authentication",
            user_id=user_id,
            action=action,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            **kwargs
        )


# Instância global do logger de auditoria
audit_logger = AuditLogger()

