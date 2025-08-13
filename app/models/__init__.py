"""
Modelos SQLAlchemy do CryptVault
"""
from .base import Base, BaseModel, BaseModelWithIntId
from .organization import (
    Company,
    User, 
    Project,
    TeamInvitation,
    CompanyStatus,
    CompanyType,
    UserRole,
    UserStatus,
    ProjectStatus,
    user_company_association,
    user_project_association
)
from .secret import (
    Secret, 
    SecretVersion, 
    SecretPermission, 
    SharedLink,
    SecretType,
    SecretStatus
)
from .audit import (
    AuditLog, 
    SecurityEvent, 
    AccessLog,
    AuditAction,
    AuditLevel
)

__all__ = [
    # Base
    "Base", 
    "BaseModel", 
    "BaseModelWithIntId",
    
    # Organization models
    "Company",
    "User",
    "Project", 
    "TeamInvitation",
    "CompanyStatus",
    "CompanyType",
    "UserRole",
    "UserStatus", 
    "ProjectStatus",
    "user_company_association",
    "user_project_association",
    
    # Secret models
    "Secret", 
    "SecretVersion", 
    "SecretPermission", 
    "SharedLink",
    "SecretType",
    "SecretStatus",
    
    # Audit models
    "AuditLog", 
    "SecurityEvent", 
    "AccessLog",
    "AuditAction",
    "AuditLevel",
]
