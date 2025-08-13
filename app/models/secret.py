"""
Modelos para gerenciamento de secrets
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, 
    ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
import uuid

from .base import BaseModel


class SecretType(str, enum.Enum):
    """Tipos de secret suportados"""
    TEXT = "text"
    FILE = "file"
    ENV_FILE = "env_file"
    JSON = "json"
    YAML = "yaml"
    CERTIFICATE = "certificate"
    SSH_KEY = "ssh_key"
    API_KEY = "api_key"


class SecretStatus(str, enum.Enum):
    """Status do secret"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Secret(BaseModel):
    """Modelo principal para secrets"""
    
    __tablename__ = "secrets"
    
    # Informações básicas
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    type = Column(SQLEnum(SecretType), nullable=False, default=SecretType.TEXT)
    status = Column(SQLEnum(SecretStatus), nullable=False, default=SecretStatus.ACTIVE)
    
    # Dados criptografados (referência para o serviço de criptografia)
    encrypted_data_id = Column(String(255), nullable=False)  # ID no serviço de criptografia
    encrypted_metadata = Column(JSONB)  # Metadados criptografados
    
    # Organização e controle
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"), index=True)  # Projeto (opcional)
    environment = Column(String(50))  # dev, staging, prod, etc.
    
    # Tags para organização
    tags = Column(JSONB, default=list)  # Lista de tags
    
    # Controle de acesso
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    is_shared = Column(Boolean, default=False)
    
    # Versionamento
    current_version = Column(Integer, default=1)
    
    # Expiração
    expires_at = Column(DateTime)
    
    # Validação de formato
    format_validation = Column(String(100))  # regex, json, yaml, etc.
    
    # Relacionamentos
    company = relationship("Company", back_populates="secrets")
    project = relationship("Project", back_populates="secrets")
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_secrets")
    versions = relationship("SecretVersion", back_populates="secret", cascade="all, delete-orphan")
    permissions = relationship("SecretPermission", back_populates="secret", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="secret")
    shared_links = relationship("SharedLink", back_populates="secret", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_secret_company_name', 'company_id', 'name'),
        Index('idx_secret_owner_status', 'owner_id', 'status'),
        Index('idx_secret_project_env', 'project_id', 'environment'),
        Index('idx_secret_tags', 'tags', postgresql_using='gin'),
        Index('idx_secret_expires_status', 'expires_at', 'status'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Verifica se o secret está expirado"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self) -> str:
        return f"<Secret(id={self.id}, name={self.name}, type={self.type})>"


class SecretVersion(BaseModel):
    """Modelo para versionamento de secrets"""
    
    __tablename__ = "secret_versions"
    
    # Relacionamento com secret
    secret_id = Column(UUID(as_uuid=True), ForeignKey("secrets.id"), nullable=False, index=True)
    secret = relationship("Secret", back_populates="versions")
    
    # Informações da versão
    version_number = Column(Integer, nullable=False)
    encrypted_data_id = Column(String(255), nullable=False)  # ID no serviço de criptografia
    encrypted_metadata = Column(JSONB)
    
    # Metadados da versão
    size_bytes = Column(Integer)
    checksum = Column(String(64))  # SHA-256
    mime_type = Column(String(100))
    
    # Controle
    created_by = Column(UUID(as_uuid=True), nullable=False, index=True)
    change_description = Column(Text)
    
    # Status da versão
    is_current = Column(Boolean, default=False)
    
    # Índices
    __table_args__ = (
        Index('idx_version_secret_number', 'secret_id', 'version_number', unique=True),
        Index('idx_version_secret_current', 'secret_id', 'is_current'),
    )
    
    def __repr__(self) -> str:
        return f"<SecretVersion(secret_id={self.secret_id}, version={self.version_number})>"


class SecretPermission(BaseModel):
    """Modelo para permissões de acesso aos secrets"""
    
    __tablename__ = "secret_permissions"
    
    # Relacionamento com secret
    secret_id = Column(UUID(as_uuid=True), ForeignKey("secrets.id"), nullable=False, index=True)
    secret = relationship("Secret", back_populates="permissions")
    
    # Tipo de permissão
    grantee_type = Column(String(20), nullable=False)  # user, group, role
    grantee_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Permissões específicas
    can_read = Column(Boolean, default=True)
    can_write = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_share = Column(Boolean, default=False)
    can_manage_permissions = Column(Boolean, default=False)
    
    # Controle temporal
    granted_by = Column(UUID(as_uuid=True), nullable=False)
    granted_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    
    # Índices
    __table_args__ = (
        Index('idx_permission_secret_grantee', 'secret_id', 'grantee_id', 'grantee_type', unique=True),
        Index('idx_permission_grantee', 'grantee_id', 'grantee_type'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Verifica se a permissão está expirada"""
        if not self.expires_at:
            return False
        return datetime.utcnow() > self.expires_at
    
    def __repr__(self) -> str:
        return f"<SecretPermission(secret_id={self.secret_id}, grantee={self.grantee_id})>"


class SharedLink(BaseModel):
    """Modelo para links de compartilhamento temporário"""
    
    __tablename__ = "shared_links"
    
    # Relacionamento com secret
    secret_id = Column(UUID(as_uuid=True), ForeignKey("secrets.id"), nullable=False, index=True)
    secret = relationship("Secret", back_populates="shared_links")
    
    # Link único
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Controle de acesso
    max_downloads = Column(Integer, default=1)
    current_downloads = Column(Integer, default=0)
    requires_password = Column(Boolean, default=False)
    password_hash = Column(String(255))
    
    # Expiração
    expires_at = Column(DateTime, nullable=False)
    
    # Metadados
    created_by = Column(UUID(as_uuid=True), nullable=False)
    description = Column(Text)
    
    # Controle de IP (opcional)
    allowed_ips = Column(JSONB)  # Lista de IPs permitidos
    
    @property
    def is_expired(self) -> bool:
        """Verifica se o link está expirado"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_exhausted(self) -> bool:
        """Verifica se o link atingiu o limite de downloads"""
        return self.current_downloads >= self.max_downloads
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o link é válido"""
        return not (self.is_expired or self.is_exhausted)
    
    def __repr__(self) -> str:
        return f"<SharedLink(secret_id={self.secret_id}, token={self.token[:8]}...)>"
