"""
Modelos para auditoria e logs de acesso
"""
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, 
    Integer, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import enum

from .base import BaseModel


class AuditAction(str, enum.Enum):
    """Ações de auditoria"""
    # Secrets
    SECRET_CREATE = "secret_create"
    SECRET_READ = "secret_read"
    SECRET_UPDATE = "secret_update"
    SECRET_DELETE = "secret_delete"
    SECRET_RESTORE = "secret_restore"
    SECRET_SHARE = "secret_share"
    SECRET_UNSHARE = "secret_unshare"
    
    # Versões
    VERSION_CREATE = "version_create"
    VERSION_RESTORE = "version_restore"
    
    # Permissões
    PERMISSION_GRANT = "permission_grant"
    PERMISSION_REVOKE = "permission_revoke"
    PERMISSION_UPDATE = "permission_update"
    
    # Autenticação
    AUTH_LOGIN = "auth_login"
    AUTH_LOGOUT = "auth_logout"
    AUTH_FAILED = "auth_failed"
    AUTH_TOKEN_REFRESH = "auth_token_refresh"
    
    # Compartilhamento
    SHARED_LINK_CREATE = "shared_link_create"
    SHARED_LINK_ACCESS = "shared_link_access"
    SHARED_LINK_DELETE = "shared_link_delete"
    
    # Sistema
    SYSTEM_BACKUP = "system_backup"
    SYSTEM_RESTORE = "system_restore"


class AuditLevel(str, enum.Enum):
    """Nível de criticidade do evento"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AuditLog(BaseModel):
    """Modelo principal para logs de auditoria"""
    
    __tablename__ = "audit_logs"
    
    # Ação realizada
    action = Column(SQLEnum(AuditAction), nullable=False, index=True)
    level = Column(SQLEnum(AuditLevel), nullable=False, default=AuditLevel.MEDIUM)
    
    # Usuário e contexto
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), index=True)  # Pode ser None para ações do sistema
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    session_id = Column(String(255), index=True)
    
    # Recurso afetado
    resource_type = Column(String(50), nullable=False)  # secret, version, permission, etc.
    resource_id = Column(UUID(as_uuid=True), index=True)
    secret_id = Column(UUID(as_uuid=True), ForeignKey("secrets.id"), index=True)
    
    # Relacionamentos
    user = relationship("User")
    company = relationship("Company", back_populates="audit_logs")
    secret = relationship("Secret", back_populates="audit_logs")
    
    # Detalhes da ação
    description = Column(Text, nullable=False)
    details = Column(JSONB)  # Detalhes estruturados da ação
    
    # Informações de rede
    ip_address = Column(INET)
    user_agent = Column(Text)
    
    # Resultado
    success = Column(String(10), nullable=False)  # success, failure, partial
    error_message = Column(Text)
    
    # Metadados adicionais
    metadata = Column(JSONB)
    
    # Índices otimizados para consultas de auditoria
    __table_args__ = (
        Index('idx_audit_company_action', 'company_id', 'action'),
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_secret_action', 'secret_id', 'action'),
        Index('idx_audit_created_action', 'created_at', 'action'),
        Index('idx_audit_level_created', 'level', 'created_at'),
        Index('idx_audit_ip_created', 'ip_address', 'created_at'),
        Index('idx_audit_details', 'details', postgresql_using='gin'),
    )
    
    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, user_id={self.user_id}, created_at={self.created_at})>"


class SecurityEvent(BaseModel):
    """Modelo para eventos de segurança específicos"""
    
    __tablename__ = "security_events"
    
    # Tipo de evento
    event_type = Column(String(100), nullable=False, index=True)
    severity = Column(SQLEnum(AuditLevel), nullable=False, default=AuditLevel.MEDIUM)
    
    # Contexto
    user_id = Column(UUID(as_uuid=True), index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Detalhes do evento
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Dados técnicos
    source_ip = Column(INET)
    user_agent = Column(Text)
    
    # Dados estruturados
    event_data = Column(JSONB)
    
    # Status
    is_resolved = Column(String(20), default="pending")  # pending, investigating, resolved, false_positive
    resolved_at = Column(DateTime)
    resolved_by = Column(UUID(as_uuid=True))
    resolution_notes = Column(Text)
    
    # Índices
    __table_args__ = (
        Index('idx_security_company_type', 'company_id', 'event_type'),
        Index('idx_security_severity_created', 'severity', 'created_at'),
        Index('idx_security_user_created', 'user_id', 'created_at'),
        Index('idx_security_resolved', 'is_resolved', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<SecurityEvent(type={self.event_type}, severity={self.severity}, created_at={self.created_at})>"


class AccessLog(BaseModel):
    """Modelo simplificado para logs de acesso rápido"""
    
    __tablename__ = "access_logs"
    
    # Básico
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    company_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    secret_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Ação
    action = Column(String(50), nullable=False)  # read, download, view
    
    # Rede
    ip_address = Column(INET)
    
    # Performance - usando timestamp simples
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Índices otimizados para high-frequency logging
    __table_args__ = (
        Index('idx_access_secret_timestamp', 'secret_id', 'timestamp'),
        Index('idx_access_user_timestamp', 'user_id', 'timestamp'),
        Index('idx_access_company_timestamp', 'company_id', 'timestamp'),
        # Particionamento por data seria ideal aqui
    )
    
    def __repr__(self) -> str:
        return f"<AccessLog(user_id={self.user_id}, secret_id={self.secret_id}, action={self.action})>"
