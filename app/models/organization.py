"""
Modelos para organização multi-tenant: Companies, Users, Projects
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, Integer, 
    ForeignKey, Enum as SQLEnum, Index, JSON, Table
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import enum
import uuid

from .base import BaseModel


class CompanyStatus(str, enum.Enum):
    """Status da empresa"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    TRIAL = "trial"
    PREMIUM = "premium"


class CompanyType(str, enum.Enum):
    """Tipo de empresa"""
    STARTUP = "startup"
    SME = "sme"  # Small and Medium Enterprise
    ENTERPRISE = "enterprise"
    AGENCY = "agency"
    FREELANCER = "freelancer"
    NON_PROFIT = "non_profit"


class UserRole(str, enum.Enum):
    """Roles de usuário no sistema"""
    SUPER_ADMIN = "super_admin"  # Admin global do sistema
    COMPANY_ADMIN = "company_admin"  # Admin da empresa
    PROJECT_MANAGER = "project_manager"  # Gerente de projetos
    DEVELOPER = "developer"  # Desenvolvedor
    VIEWER = "viewer"  # Apenas leitura
    AUDITOR = "auditor"  # Acesso a logs de auditoria


class UserStatus(str, enum.Enum):
    """Status do usuário"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"


class ProjectStatus(str, enum.Enum):
    """Status do projeto"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"


# Tabelas de associação many-to-many
user_company_association = Table(
    'user_companies',
    BaseModel.metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), nullable=False),
    Column('company_id', UUID(as_uuid=True), ForeignKey('companies.id'), nullable=False),
    Column('role', SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER),
    Column('is_primary', Boolean, default=False),  # Empresa principal do usuário
    Column('permissions', JSONB, default=list),  # Permissões específicas
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('last_access', DateTime),
    Column('is_active', Boolean, default=True),
    Index('idx_user_company_user', 'user_id'),
    Index('idx_user_company_company', 'company_id'),
    Index('idx_user_company_role', 'role'),
    Index('idx_user_company_primary', 'user_id', 'is_primary'),
)

user_project_association = Table(
    'user_projects',
    BaseModel.metadata,
    Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'), nullable=False),
    Column('project_id', UUID(as_uuid=True), ForeignKey('projects.id'), nullable=False),
    Column('role', SQLEnum(UserRole), nullable=False, default=UserRole.DEVELOPER),
    Column('permissions', JSONB, default=list),  # Permissões específicas no projeto
    Column('can_create_secrets', Boolean, default=True),
    Column('can_read_secrets', Boolean, default=True),
    Column('can_update_secrets', Boolean, default=False),
    Column('can_delete_secrets', Boolean, default=False),
    Column('can_share_secrets', Boolean, default=False),
    Column('environments_access', JSONB, default=list),  # ["dev", "staging", "prod"]
    Column('joined_at', DateTime, default=datetime.utcnow),
    Column('last_access', DateTime),
    Column('is_active', Boolean, default=True),
    Index('idx_user_project_user', 'user_id'),
    Index('idx_user_project_project', 'project_id'),
    Index('idx_user_project_role', 'role'),
)


class Company(BaseModel):
    """Modelo para empresas/organizações"""
    
    __tablename__ = "companies"
    
    # Informações básicas
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)  # URL-friendly name
    description = Column(Text)
    
    # Tipo e status
    type = Column(SQLEnum(CompanyType), nullable=False, default=CompanyType.SME)
    status = Column(SQLEnum(CompanyStatus), nullable=False, default=CompanyStatus.TRIAL)
    
    # Informações de contato
    email = Column(String(255))
    phone = Column(String(50))
    website = Column(String(255))
    
    # Endereço
    address = Column(JSONB)  # Endereço completo estruturado
    
    # Configurações da empresa
    settings = Column(JSONB, default=dict)  # Configurações específicas
    
    # Limites e quotas
    max_users = Column(Integer, default=10)
    max_projects = Column(Integer, default=5)
    max_secrets = Column(Integer, default=100)
    max_storage_mb = Column(Integer, default=1024)  # 1GB padrão
    
    # Dados de billing
    billing_email = Column(String(255))
    billing_address = Column(JSONB)
    
    # Metadados
    metadata = Column(JSONB, default=dict)
    
    # Datas importantes
    trial_ends_at = Column(DateTime)
    subscription_expires_at = Column(DateTime)
    
    # Relacionamentos
    users = relationship(
        "User",
        secondary=user_company_association,
        back_populates="companies",
        lazy="dynamic"
    )
    projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")
    secrets = relationship("Secret", back_populates="company")
    audit_logs = relationship("AuditLog", back_populates="company")
    
    # Índices
    __table_args__ = (
        Index('idx_company_name', 'name'),
        Index('idx_company_slug', 'slug'),
        Index('idx_company_status', 'status'),
        Index('idx_company_type', 'type'),
        Index('idx_company_trial', 'trial_ends_at', 'status'),
    )
    
    @property
    def is_trial_expired(self) -> bool:
        """Verifica se o trial expirou"""
        if not self.trial_ends_at:
            return False
        return datetime.utcnow() > self.trial_ends_at
    
    @property
    def is_subscription_expired(self) -> bool:
        """Verifica se a assinatura expirou"""
        if not self.subscription_expires_at:
            return False
        return datetime.utcnow() > self.subscription_expires_at
    
    def get_user_role(self, user_id: uuid.UUID) -> Optional[UserRole]:
        """Obtém o role do usuário na empresa"""
        from sqlalchemy import select
        stmt = select(user_company_association.c.role).where(
            user_company_association.c.user_id == user_id,
            user_company_association.c.company_id == self.id,
            user_company_association.c.is_active == True
        )
        # Seria executado em uma sessão, retornando o role
        return None  # Placeholder
    
    def __repr__(self) -> str:
        return f"<Company(id={self.id}, name={self.name}, slug={self.slug})>"


class User(BaseModel):
    """Modelo para usuários do sistema"""
    
    __tablename__ = "users"
    
    # Informações básicas
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, index=True)
    full_name = Column(String(255), nullable=False)
    
    # Avatar e perfil
    avatar_url = Column(String(500))
    bio = Column(Text)
    title = Column(String(100))  # Cargo/posição
    
    # Status e controle
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING_ACTIVATION)
    is_verified = Column(Boolean, default=False)
    is_system_admin = Column(Boolean, default=False)  # Super admin
    
    # Configurações pessoais
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="pt-BR")
    preferences = Column(JSONB, default=dict)
    
    # Segurança
    last_login = Column(DateTime)
    last_password_change = Column(DateTime)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Tokens e sessões
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(DateTime)
    
    # Metadados
    metadata = Column(JSONB, default=dict)
    
    # Relacionamentos
    companies = relationship(
        "Company",
        secondary=user_company_association,
        back_populates="users",
        lazy="dynamic"
    )
    projects = relationship(
        "Project",
        secondary=user_project_association,
        back_populates="users",
        lazy="dynamic"
    )
    owned_secrets = relationship("Secret", foreign_keys="Secret.owner_id", back_populates="owner")
    created_projects = relationship("Project", foreign_keys="Project.created_by", back_populates="creator")
    
    # Índices
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_username', 'username'),
        Index('idx_user_status', 'status'),
        Index('idx_user_last_login', 'last_login'),
        Index('idx_user_full_name', 'full_name'),
    )
    
    @property
    def is_locked(self) -> bool:
        """Verifica se a conta está bloqueada"""
        if not self.locked_until:
            return False
        return datetime.utcnow() < self.locked_until
    
    @property
    def primary_company(self) -> Optional["Company"]:
        """Retorna a empresa principal do usuário"""
        # Seria implementado com query à tabela de associação
        return None  # Placeholder
    
    def get_companies_with_roles(self) -> List[dict]:
        """Retorna empresas do usuário com seus roles"""
        # Seria implementado com query complexa
        return []  # Placeholder
    
    def get_projects_with_permissions(self, company_id: Optional[uuid.UUID] = None) -> List[dict]:
        """Retorna projetos do usuário com permissões"""
        # Seria implementado com query complexa
        return []  # Placeholder
    
    def has_permission_in_company(self, company_id: uuid.UUID, permission: str) -> bool:
        """Verifica se usuário tem permissão específica na empresa"""
        # Seria implementado com query e lógica de roles
        return False  # Placeholder
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, full_name={self.full_name})>"


class Project(BaseModel):
    """Modelo para projetos dentro de empresas"""
    
    __tablename__ = "projects"
    
    # Informações básicas
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), nullable=False, index=True)  # Único dentro da empresa
    description = Column(Text)
    
    # Relacionamento com empresa
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False, index=True)
    company = relationship("Company", back_populates="projects")
    
    # Status e tipo
    status = Column(SQLEnum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    
    # Configurações do projeto
    environments = Column(JSONB, default=["dev", "staging", "prod"])  # Ambientes disponíveis
    settings = Column(JSONB, default=dict)
    
    # Informações de controle
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    creator = relationship("User", foreign_keys=[created_by], back_populates="created_projects")
    
    # Metadados do projeto
    repository_url = Column(String(500))
    documentation_url = Column(String(500))
    tags = Column(JSONB, default=list)
    metadata = Column(JSONB, default=dict)
    
    # Estatísticas
    secrets_count = Column(Integer, default=0)
    last_activity = Column(DateTime)
    
    # Relacionamentos
    users = relationship(
        "User",
        secondary=user_project_association,
        back_populates="projects",
        lazy="dynamic"
    )
    secrets = relationship("Secret", back_populates="project", cascade="all, delete-orphan")
    
    # Índices
    __table_args__ = (
        Index('idx_project_company_slug', 'company_id', 'slug', unique=True),
        Index('idx_project_name', 'name'),
        Index('idx_project_status', 'status'),
        Index('idx_project_created_by', 'created_by'),
        Index('idx_project_last_activity', 'last_activity'),
        Index('idx_project_tags', 'tags', postgresql_using='gin'),
    )
    
    def get_user_permissions(self, user_id: uuid.UUID) -> dict:
        """Obtém permissões do usuário no projeto"""
        # Seria implementado com query à tabela de associação
        return {}  # Placeholder
    
    def get_environments_for_user(self, user_id: uuid.UUID) -> List[str]:
        """Retorna ambientes que o usuário pode acessar"""
        # Seria implementado com query e lógica de permissões
        return []  # Placeholder
    
    @property
    def full_name(self) -> str:
        """Nome completo do projeto (empresa/projeto)"""
        return f"{self.company.name}/{self.name}" if self.company else self.name
    
    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name={self.name}, company_id={self.company_id})>"


class TeamInvitation(BaseModel):
    """Convites para usuários se juntarem a empresas/projetos"""
    
    __tablename__ = "team_invitations"
    
    # Informações do convite
    email = Column(String(255), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    
    # Relacionamentos
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"), nullable=False)
    company = relationship("Company")
    
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id"))  # Opcional
    project = relationship("Project")
    
    # Permissões do convite
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.DEVELOPER)
    permissions = Column(JSONB, default=list)
    environments_access = Column(JSONB, default=list)
    
    # Controle do convite
    invited_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    inviter = relationship("User")
    
    expires_at = Column(DateTime, nullable=False)
    accepted_at = Column(DateTime)
    accepted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    
    # Status
    is_used = Column(Boolean, default=False)
    
    # Mensagem personalizada
    message = Column(Text)
    
    # Índices
    __table_args__ = (
        Index('idx_invitation_email', 'email'),
        Index('idx_invitation_token', 'token'),
        Index('idx_invitation_company', 'company_id'),
        Index('idx_invitation_expires', 'expires_at'),
        Index('idx_invitation_used', 'is_used'),
    )
    
    @property
    def is_expired(self) -> bool:
        """Verifica se o convite expirou"""
        return datetime.utcnow() > self.expires_at
    
    @property
    def is_valid(self) -> bool:
        """Verifica se o convite é válido"""
        return not (self.is_expired or self.is_used)
    
    def __repr__(self) -> str:
        return f"<TeamInvitation(email={self.email}, company_id={self.company_id})>"

