"""
Schemas Pydantic para organização multi-tenant
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, UUID4, Field, EmailStr, validator
from datetime import datetime
from enum import Enum

from app.models.organization import (
    CompanyStatus, CompanyType, UserRole, UserStatus, ProjectStatus
)


class CompanyStatusEnum(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    TRIAL = "trial"
    PREMIUM = "premium"


class CompanyTypeEnum(str, Enum):
    STARTUP = "startup"
    SME = "sme"
    ENTERPRISE = "enterprise"
    AGENCY = "agency"
    FREELANCER = "freelancer"
    NON_PROFIT = "non_profit"


class UserRoleEnum(str, Enum):
    SUPER_ADMIN = "super_admin"
    COMPANY_ADMIN = "company_admin"
    PROJECT_MANAGER = "project_manager"
    DEVELOPER = "developer"
    VIEWER = "viewer"
    AUDITOR = "auditor"


class UserStatusEnum(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_ACTIVATION = "pending_activation"


class ProjectStatusEnum(str, Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"
    SUSPENDED = "suspended"
    PLANNING = "planning"
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    MAINTENANCE = "maintenance"


# Company Schemas
class CompanyBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, regex="^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)
    type: CompanyTypeEnum = CompanyTypeEnum.SME
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug deve conter apenas letras, números e hífens')
        return v.lower()


class CompanyCreate(CompanyBase):
    billing_email: Optional[EmailStr] = None
    max_users: Optional[int] = Field(10, ge=1, le=1000)
    max_projects: Optional[int] = Field(5, ge=1, le=100)
    max_secrets: Optional[int] = Field(100, ge=1, le=10000)


class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=255)
    billing_email: Optional[EmailStr] = None
    settings: Optional[Dict[str, Any]] = None


class CompanyResponse(CompanyBase):
    id: UUID4
    status: CompanyStatusEnum
    created_at: datetime
    updated_at: datetime
    trial_ends_at: Optional[datetime]
    subscription_expires_at: Optional[datetime]
    max_users: int
    max_projects: int
    max_secrets: int
    is_trial_expired: bool
    is_subscription_expired: bool
    
    class Config:
        from_attributes = True


class CompanyListResponse(BaseModel):
    companies: List[CompanyResponse]
    total: int
    page: int
    size: int
    total_pages: int


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field("UTC", max_length=50)
    language: Optional[str] = Field("pt-BR", max_length=10)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=100)
    company_id: Optional[UUID4] = None  # Empresa inicial
    role: Optional[UserRoleEnum] = UserRoleEnum.DEVELOPER


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    title: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=10)
    preferences: Optional[Dict[str, Any]] = None


class UserResponse(UserBase):
    id: UUID4
    status: UserStatusEnum
    is_verified: bool
    is_system_admin: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserWithCompaniesResponse(UserResponse):
    companies: List["UserCompanyRole"]
    primary_company_id: Optional[UUID4]


class UserCompanyRole(BaseModel):
    """Relacionamento usuário-empresa com role"""
    company_id: UUID4
    company_name: str
    company_slug: str
    role: UserRoleEnum
    permissions: List[str]
    is_primary: bool
    joined_at: datetime
    last_access: Optional[datetime]
    
    class Config:
        from_attributes = True


class UserProjectPermissions(BaseModel):
    """Permissões do usuário em projeto"""
    project_id: UUID4
    project_name: str
    project_slug: str
    company_id: UUID4
    role: UserRoleEnum
    permissions: List[str]
    environments_access: List[str]
    can_create_secrets: bool
    can_read_secrets: bool
    can_update_secrets: bool
    can_delete_secrets: bool
    can_share_secrets: bool
    joined_at: datetime
    
    class Config:
        from_attributes = True


# Project Schemas
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, regex="^[a-z0-9-]+$")
    description: Optional[str] = Field(None, max_length=1000)
    environments: Optional[List[str]] = Field(["dev", "staging", "prod"])
    repository_url: Optional[str] = Field(None, max_length=500)
    documentation_url: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = Field(default_factory=list)
    
    @validator('slug')
    def validate_slug(cls, v):
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Slug deve conter apenas letras, números e hífens')
        return v.lower()
    
    @validator('environments')
    def validate_environments(cls, v):
        if v and len(v) > 10:
            raise ValueError('Máximo 10 ambientes permitidos')
        valid_envs = {'dev', 'test', 'staging', 'prod', 'sandbox', 'qa', 'demo', 'local'}
        for env in v or []:
            if env not in valid_envs:
                raise ValueError(f'Ambiente inválido: {env}')
        return v


class ProjectCreate(ProjectBase):
    company_id: UUID4


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[ProjectStatusEnum] = None
    environments: Optional[List[str]] = None
    repository_url: Optional[str] = Field(None, max_length=500)
    documentation_url: Optional[str] = Field(None, max_length=500)
    tags: Optional[List[str]] = None
    settings: Optional[Dict[str, Any]] = None


class ProjectResponse(ProjectBase):
    id: UUID4
    company_id: UUID4
    status: ProjectStatusEnum
    created_by: UUID4
    secrets_count: int
    last_activity: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    full_name: str
    
    class Config:
        from_attributes = True


class ProjectWithDetailsResponse(ProjectResponse):
    company: CompanyResponse
    creator: UserResponse
    users_count: int
    recent_activity: List[Dict[str, Any]]


class ProjectListResponse(BaseModel):
    projects: List[ProjectResponse]
    total: int
    page: int
    size: int
    total_pages: int


# Team Management Schemas
class TeamInvitationCreate(BaseModel):
    email: EmailStr
    company_id: UUID4
    project_id: Optional[UUID4] = None
    role: UserRoleEnum = UserRoleEnum.DEVELOPER
    permissions: Optional[List[str]] = Field(default_factory=list)
    environments_access: Optional[List[str]] = Field(default_factory=list)
    expires_in_hours: int = Field(72, ge=1, le=720)  # Max 30 dias
    message: Optional[str] = Field(None, max_length=500)


class TeamInvitationResponse(BaseModel):
    id: UUID4
    email: EmailStr
    company_id: UUID4
    project_id: Optional[UUID4]
    role: UserRoleEnum
    permissions: List[str]
    environments_access: List[str]
    invited_by: UUID4
    expires_at: datetime
    accepted_at: Optional[datetime]
    is_used: bool
    is_expired: bool
    is_valid: bool
    message: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AcceptInvitationRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    username: Optional[str] = Field(None, min_length=3, max_length=100)


# Team Management
class AddUserToCompanyRequest(BaseModel):
    user_id: UUID4
    role: UserRoleEnum = UserRoleEnum.DEVELOPER
    permissions: Optional[List[str]] = Field(default_factory=list)
    is_primary: bool = False


class AddUserToProjectRequest(BaseModel):
    user_id: UUID4
    role: UserRoleEnum = UserRoleEnum.DEVELOPER
    permissions: Optional[List[str]] = Field(default_factory=list)
    environments_access: Optional[List[str]] = Field(default_factory=list)
    can_create_secrets: bool = True
    can_read_secrets: bool = True
    can_update_secrets: bool = False
    can_delete_secrets: bool = False
    can_share_secrets: bool = False


class UpdateUserRoleRequest(BaseModel):
    role: UserRoleEnum
    permissions: Optional[List[str]] = None
    environments_access: Optional[List[str]] = None


# Search and Filter Schemas
class CompanySearchRequest(BaseModel):
    q: Optional[str] = Field(None, max_length=200)
    type: Optional[CompanyTypeEnum] = None
    status: Optional[CompanyStatusEnum] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", regex="^(name|created_at|updated_at)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class UserSearchRequest(BaseModel):
    q: Optional[str] = Field(None, max_length=200)
    company_id: Optional[UUID4] = None
    status: Optional[UserStatusEnum] = None
    role: Optional[UserRoleEnum] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", regex="^(full_name|email|created_at|last_login)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")


class ProjectSearchRequest(BaseModel):
    q: Optional[str] = Field(None, max_length=200)
    company_id: Optional[UUID4] = None
    status: Optional[ProjectStatusEnum] = None
    created_by: Optional[UUID4] = None
    tags: Optional[List[str]] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    sort_by: str = Field("created_at", regex="^(name|created_at|updated_at|last_activity)$")
    sort_order: str = Field("desc", regex="^(asc|desc)$")


# Statistics Schemas
class CompanyStatsResponse(BaseModel):
    total_users: int
    active_users: int
    total_projects: int
    active_projects: int
    total_secrets: int
    secrets_by_environment: Dict[str, int]
    storage_used_mb: int
    storage_limit_mb: int
    recent_activity: List[Dict[str, Any]]


class UserActivityResponse(BaseModel):
    user_id: UUID4
    last_login: Optional[datetime]
    total_secrets_created: int
    total_secrets_accessed: int
    companies_count: int
    projects_count: int
    recent_actions: List[Dict[str, Any]]


# Context Schemas (for current user)
class CurrentUserContext(BaseModel):
    """Contexto do usuário atual com suas empresas e projetos"""
    user: UserResponse
    current_company_id: Optional[UUID4]
    companies: List[UserCompanyRole]
    projects: List[UserProjectPermissions]
    permissions: List[str]
    is_super_admin: bool


class SwitchCompanyRequest(BaseModel):
    company_id: UUID4


# Update forward references
UserWithCompaniesResponse.model_rebuild()
ProjectWithDetailsResponse.model_rebuild()

