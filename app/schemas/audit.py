"""
Schemas para auditoria
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4, Field
from datetime import datetime
from enum import Enum

from app.models.audit import AuditAction, AuditLevel


class AuditActionEnum(str, Enum):
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


class AuditLevelEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# Schemas de resposta
class AuditLogResponse(BaseModel):
    """Schema para resposta de log de auditoria"""
    id: UUID4
    action: AuditActionEnum
    level: AuditLevelEnum
    user_id: Optional[UUID4]
    company_id: UUID4
    session_id: Optional[str]
    resource_type: str
    resource_id: Optional[UUID4]
    secret_id: Optional[UUID4]
    description: str
    details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    success: str
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AuditLogListResponse(BaseModel):
    """Schema para listagem de logs de auditoria"""
    logs: List[AuditLogResponse]
    total: int
    page: int
    size: int
    total_pages: int


class SecurityEventResponse(BaseModel):
    """Schema para resposta de evento de segurança"""
    id: UUID4
    event_type: str
    severity: AuditLevelEnum
    user_id: Optional[UUID4]
    company_id: UUID4
    title: str
    description: str
    source_ip: Optional[str]
    user_agent: Optional[str]
    event_data: Optional[Dict[str, Any]]
    is_resolved: str
    resolved_at: Optional[datetime]
    resolved_by: Optional[UUID4]
    resolution_notes: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class SecurityEventListResponse(BaseModel):
    """Schema para listagem de eventos de segurança"""
    events: List[SecurityEventResponse]
    total: int
    page: int
    size: int
    total_pages: int


class AccessLogResponse(BaseModel):
    """Schema para resposta de log de acesso"""
    id: UUID4
    user_id: UUID4
    company_id: UUID4
    secret_id: UUID4
    action: str
    ip_address: Optional[str]
    timestamp: datetime
    
    class Config:
        from_attributes = True


# Schemas de busca
class AuditLogSearchRequest(BaseModel):
    """Schema para busca de logs de auditoria"""
    q: Optional[str] = Field(None, max_length=200)
    action: Optional[str] = None
    user_id: Optional[UUID4] = None
    resource_id: Optional[UUID4] = None
    level: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# Schemas para estatísticas
class AuditSummaryResponse(BaseModel):
    """Schema para resumo de auditoria"""
    total_events: int
    by_action: Dict[str, int]
    by_level: Dict[str, int]
    by_user: List[Dict[str, Any]]
    recent_critical: List[AuditLogResponse]
    security_events_count: int
    unresolved_security_events: int
    most_accessed_secrets: List[Dict[str, Any]]
    failed_authentications: int
    unique_users: int
    unique_ips: int

