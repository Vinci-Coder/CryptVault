"""
Schemas para secrets
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4, validator, Field
from datetime import datetime
from enum import Enum

from app.models.secret import SecretType, SecretStatus


class SecretTypeEnum(str, Enum):
    TEXT = "text"
    FILE = "file"
    ENV_FILE = "env_file"
    JSON = "json"
    YAML = "yaml"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"
    API_KEY = "api_key"


class SecretStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    REVOKED = "revoked"


# Schemas de criação
class SecretCreate(BaseModel):
    """Schema para criação de secret"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: str = Field(..., min_length=1)
    type: SecretTypeEnum = SecretTypeEnum.TEXT
    project_id: Optional[UUID4] = None
    environment: Optional[str] = Field(None, max_length=50)
    tags: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None
    format_validation: Optional[str] = Field(None, max_length=100)
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag length cannot exceed 50 characters')
        return v
    
    @validator('environment')
    def validate_environment(cls, v):
        if v and v not in ['dev', 'test', 'staging', 'prod', 'sandbox']:
            raise ValueError('Invalid environment')
        return v


class SecretUpdate(BaseModel):
    """Schema para atualização de secret"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    content: Optional[str] = Field(None, min_length=1)
    project_id: Optional[UUID4] = None
    environment: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    format_validation: Optional[str] = Field(None, max_length=100)
    status: Optional[SecretStatusEnum] = None
    change_description: Optional[str] = Field(None, max_length=500)
    
    @validator('tags')
    def validate_tags(cls, v):
        if v and len(v) > 20:
            raise ValueError('Maximum 20 tags allowed')
        if v:
            for tag in v:
                if len(tag) > 50:
                    raise ValueError('Tag length cannot exceed 50 characters')
        return v


# Schemas de resposta
class SecretVersionResponse(BaseModel):
    """Schema para versão do secret"""
    id: UUID4
    version_number: int
    size_bytes: Optional[int]
    checksum: Optional[str]
    mime_type: Optional[str]
    created_by: UUID4
    created_at: datetime
    change_description: Optional[str]
    is_current: bool
    
    class Config:
        from_attributes = True


class SecretResponse(BaseModel):
    """Schema para resposta de secret (sem conteúdo)"""
    id: UUID4
    name: str
    description: Optional[str]
    type: SecretTypeEnum
    status: SecretStatusEnum
    company_id: UUID4
    project_id: Optional[UUID4]
    environment: Optional[str]
    tags: List[str]
    owner_id: UUID4
    is_shared: bool
    current_version: int
    expires_at: Optional[datetime]
    format_validation: Optional[str]
    created_at: datetime
    updated_at: datetime
    is_expired: bool
    
    class Config:
        from_attributes = True


class SecretWithContentResponse(SecretResponse):
    """Schema para resposta de secret com conteúdo descriptografado"""
    content: str
    
    class Config:
        from_attributes = True


class SecretListResponse(BaseModel):
    """Schema para listagem de secrets"""
    secrets: List[SecretResponse]
    total: int
    page: int
    size: int
    total_pages: int


class SecretVersionListResponse(BaseModel):
    """Schema para listagem de versões"""
    versions: List[SecretVersionResponse]
    total: int


# Schemas para compartilhamento
class SharedLinkCreate(BaseModel):
    """Schema para criação de link compartilhado"""
    max_downloads: int = Field(default=1, ge=1, le=100)
    expires_in_hours: int = Field(default=24, ge=1, le=720)  # Max 30 dias
    requires_password: bool = False
    password: Optional[str] = Field(None, min_length=8)
    description: Optional[str] = Field(None, max_length=200)
    allowed_ips: Optional[List[str]] = None
    
    @validator('allowed_ips')
    def validate_ips(cls, v):
        if v and len(v) > 10:
            raise ValueError('Maximum 10 IP addresses allowed')
        return v


class SharedLinkResponse(BaseModel):
    """Schema para resposta de link compartilhado"""
    id: UUID4
    token: str
    secret_id: UUID4
    max_downloads: int
    current_downloads: int
    requires_password: bool
    expires_at: datetime
    created_by: UUID4
    created_at: datetime
    description: Optional[str]
    is_valid: bool
    
    class Config:
        from_attributes = True


class SharedLinkAccessRequest(BaseModel):
    """Schema para acesso a link compartilhado"""
    password: Optional[str] = None


# Schemas para permissões
class SecretPermissionCreate(BaseModel):
    """Schema para criação de permissão"""
    grantee_type: str = Field(..., regex="^(user|group|role)$")
    grantee_id: UUID4
    can_read: bool = True
    can_write: bool = False
    can_delete: bool = False
    can_share: bool = False
    can_manage_permissions: bool = False
    expires_at: Optional[datetime] = None


class SecretPermissionResponse(BaseModel):
    """Schema para resposta de permissão"""
    id: UUID4
    secret_id: UUID4
    grantee_type: str
    grantee_id: UUID4
    can_read: bool
    can_write: bool
    can_delete: bool
    can_share: bool
    can_manage_permissions: bool
    granted_by: UUID4
    granted_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool
    
    class Config:
        from_attributes = True


# Schemas para busca e filtros
class SecretSearchRequest(BaseModel):
    """Schema para busca de secrets"""
    q: Optional[str] = Field(None, max_length=200)  # Query de busca
    type: Optional[SecretTypeEnum] = None
    status: Optional[SecretStatusEnum] = None
    project_id: Optional[UUID4] = None
    environment: Optional[str] = None
    tags: Optional[List[str]] = None
    owner_id: Optional[UUID4] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    expires_after: Optional[datetime] = None
    expires_before: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = Field(default="created_at", regex="^(name|created_at|updated_at|expires_at)$")
    sort_order: Optional[str] = Field(default="desc", regex="^(asc|desc)$")


# Schemas para estatísticas
class SecretStatsResponse(BaseModel):
    """Schema para estatísticas de secrets"""
    total_secrets: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_environment: Dict[str, int]
    expiring_soon: int  # Próximos 7 dias
    recently_created: int  # Últimos 7 dias
    most_accessed: List[Dict[str, Any]]

