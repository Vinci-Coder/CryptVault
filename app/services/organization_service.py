"""
Service layer para gerenciamento de organizações multi-tenant
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc, update, delete
from sqlalchemy.orm import selectinload, joinedload
from uuid import UUID
import secrets
import hashlib

from app.models.organization import (
    Company, User, Project, TeamInvitation,
    user_company_association, user_project_association,
    CompanyStatus, UserRole, UserStatus, ProjectStatus
)
from app.schemas.organization import (
    CompanyCreate, CompanyUpdate, CompanySearchRequest,
    UserCreate, UserUpdate, UserSearchRequest,
    ProjectCreate, ProjectUpdate, ProjectSearchRequest,
    TeamInvitationCreate, AddUserToCompanyRequest, AddUserToProjectRequest
)
from app.schemas.auth import CurrentUser
from app.core.logging import get_logger, audit_logger
from app.core.security import get_password_hash

logger = get_logger(__name__)


class OrganizationService:
    """Service para gerenciamento de organizações"""
    
    def __init__(self, db: AsyncSession):
        self.db = db


class CompanyService(OrganizationService):
    """Service para gerenciamento de empresas"""
    
    async def create_company(
        self,
        company_data: CompanyCreate,
        current_user: CurrentUser
    ) -> Company:
        """Cria uma nova empresa"""
        
        logger.info(
            "Creating new company",
            user_id=str(current_user.id),
            company_name=company_data.name
        )
        
        # Verifica se slug já existe
        existing = await self.db.execute(
            select(Company).where(Company.slug == company_data.slug)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Slug '{company_data.slug}' já está em uso")
        
        # Cria empresa
        company = Company(
            name=company_data.name,
            slug=company_data.slug,
            description=company_data.description,
            type=company_data.type,
            email=company_data.email,
            phone=company_data.phone,
            website=company_data.website,
            billing_email=company_data.billing_email,
            max_users=company_data.max_users,
            max_projects=company_data.max_projects,
            max_secrets=company_data.max_secrets,
            status=CompanyStatus.TRIAL,
            trial_ends_at=datetime.utcnow() + timedelta(days=30)
        )
        
        self.db.add(company)
        await self.db.flush()
        
        # Adiciona usuário criador como admin da empresa
        user_company_stmt = user_company_association.insert().values(
            user_id=current_user.id,
            company_id=company.id,
            role=UserRole.COMPANY_ADMIN,
            is_primary=True,
            permissions=[
                "company:admin", "project:admin", "secret:admin",
                "user:admin", "audit:admin"
            ]
        )
        await self.db.execute(user_company_stmt)
        
        await self.db.commit()
        
        audit_logger.log_secret_modification(
            user_id=str(current_user.id),
            secret_id=None,
            action="company_create",
            changes={
                "company_id": str(company.id),
                "name": company.name,
                "slug": company.slug
            },
            ip_address="unknown"
        )
        
        logger.info(
            "Company created successfully",
            company_id=str(company.id),
            user_id=str(current_user.id)
        )
        
        return company
    
    async def get_company(
        self,
        company_id: UUID,
        current_user: CurrentUser
    ) -> Optional[Company]:
        """Obtém empresa por ID"""
        
        # Verifica se usuário tem acesso à empresa
        if not await self._user_has_company_access(current_user.id, company_id):
            return None
        
        query = select(Company).where(Company.id == company_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def update_company(
        self,
        company_id: UUID,
        company_data: CompanyUpdate,
        current_user: CurrentUser
    ) -> Optional[Company]:
        """Atualiza empresa"""
        
        company = await self.get_company(company_id, current_user)
        if not company:
            return None
        
        # Verifica permissão de admin
        if not await self._user_has_company_permission(
            current_user.id, company_id, "company:admin"
        ):
            return None
        
        # Atualiza campos
        update_data = company_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(company, field, value)
        
        await self.db.commit()
        
        logger.info(
            "Company updated",
            company_id=str(company_id),
            user_id=str(current_user.id),
            updated_fields=list(update_data.keys())
        )
        
        return company
    
    async def search_companies(
        self,
        search_params: CompanySearchRequest,
        current_user: CurrentUser
    ) -> Tuple[List[Company], int]:
        """Busca empresas do usuário"""
        
        # Query base - apenas empresas do usuário
        query = (
            select(Company)
            .join(user_company_association)
            .where(user_company_association.c.user_id == current_user.id)
            .where(user_company_association.c.is_active == True)
        )
        
        count_query = (
            select(func.count(Company.id))
            .join(user_company_association)
            .where(user_company_association.c.user_id == current_user.id)
            .where(user_company_association.c.is_active == True)
        )
        
        # Filtros
        if search_params.q:
            filter_condition = or_(
                Company.name.ilike(f"%{search_params.q}%"),
                Company.description.ilike(f"%{search_params.q}%")
            )
            query = query.where(filter_condition)
            count_query = count_query.where(filter_condition)
        
        if search_params.type:
            query = query.where(Company.type == search_params.type.value)
            count_query = count_query.where(Company.type == search_params.type.value)
        
        if search_params.status:
            query = query.where(Company.status == search_params.status.value)
            count_query = count_query.where(Company.status == search_params.status.value)
        
        # Ordenação
        order_column = getattr(Company, search_params.sort_by, Company.created_at)
        if search_params.sort_order == "asc":
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        # Paginação
        offset = (search_params.page - 1) * search_params.size
        query = query.offset(offset).limit(search_params.size)
        
        # Executa queries
        companies_result = await self.db.execute(query)
        companies = companies_result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(companies), total
    
    async def get_company_users(
        self,
        company_id: UUID,
        current_user: CurrentUser
    ) -> List[Dict[str, Any]]:
        """Lista usuários da empresa com roles"""
        
        if not await self._user_has_company_access(current_user.id, company_id):
            return []
        
        query = (
            select(
                User,
                user_company_association.c.role,
                user_company_association.c.permissions,
                user_company_association.c.is_primary,
                user_company_association.c.joined_at,
                user_company_association.c.last_access
            )
            .join(user_company_association)
            .where(user_company_association.c.company_id == company_id)
            .where(user_company_association.c.is_active == True)
            .order_by(User.full_name)
        )
        
        result = await self.db.execute(query)
        users_data = result.all()
        
        users = []
        for user, role, permissions, is_primary, joined_at, last_access in users_data:
            users.append({
                "user": user,
                "role": role,
                "permissions": permissions or [],
                "is_primary": is_primary,
                "joined_at": joined_at,
                "last_access": last_access
            })
        
        return users
    
    async def _user_has_company_access(self, user_id: UUID, company_id: UUID) -> bool:
        """Verifica se usuário tem acesso à empresa"""
        query = select(user_company_association).where(
            and_(
                user_company_association.c.user_id == user_id,
                user_company_association.c.company_id == company_id,
                user_company_association.c.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.first() is not None
    
    async def _user_has_company_permission(
        self, 
        user_id: UUID, 
        company_id: UUID, 
        permission: str
    ) -> bool:
        """Verifica se usuário tem permissão específica na empresa"""
        query = select(
            user_company_association.c.role,
            user_company_association.c.permissions
        ).where(
            and_(
                user_company_association.c.user_id == user_id,
                user_company_association.c.company_id == company_id,
                user_company_association.c.is_active == True
            )
        )
        result = await self.db.execute(query)
        data = result.first()
        
        if not data:
            return False
        
        role, permissions = data
        
        # Admins sempre têm todas as permissões
        if role == UserRole.COMPANY_ADMIN:
            return True
        
        # Verifica permissão específica
        return permission in (permissions or [])


class UserService(OrganizationService):
    """Service para gerenciamento de usuários"""
    
    async def create_user(
        self,
        user_data: UserCreate,
        current_user: Optional[CurrentUser] = None
    ) -> User:
        """Cria novo usuário"""
        
        # Verifica se email já existe
        existing = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Email '{user_data.email}' já está em uso")
        
        # Verifica username se fornecido
        if user_data.username:
            existing_username = await self.db.execute(
                select(User).where(User.username == user_data.username)
            )
            if existing_username.scalar_one_or_none():
                raise ValueError(f"Username '{user_data.username}' já está em uso")
        
        # Cria usuário
        user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            title=user_data.title,
            bio=user_data.bio,
            timezone=user_data.timezone,
            language=user_data.language,
            status=UserStatus.PENDING_ACTIVATION,
            # password_hash seria definido aqui em implementação real
        )
        
        self.db.add(user)
        await self.db.flush()
        
        # Se empresa inicial especificada, adiciona usuário
        if user_data.company_id and current_user:
            if await self._user_has_company_permission(
                current_user.id, user_data.company_id, "user:admin"
            ):
                user_company_stmt = user_company_association.insert().values(
                    user_id=user.id,
                    company_id=user_data.company_id,
                    role=user_data.role or UserRole.DEVELOPER,
                    permissions=[]
                )
                await self.db.execute(user_company_stmt)
        
        await self.db.commit()
        
        logger.info("User created", user_id=str(user.id), email=user.email)
        
        return user
    
    async def get_user_context(
        self,
        user_id: UUID,
        company_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """Obtém contexto completo do usuário"""
        
        # Usuário básico
        user_query = select(User).where(User.id == user_id)
        user_result = await self.db.execute(user_query)
        user = user_result.scalar_one_or_none()
        
        if not user:
            return {}
        
        # Empresas do usuário
        companies_query = (
            select(
                Company,
                user_company_association.c.role,
                user_company_association.c.permissions,
                user_company_association.c.is_primary
            )
            .join(user_company_association)
            .where(user_company_association.c.user_id == user_id)
            .where(user_company_association.c.is_active == True)
        )
        companies_result = await self.db.execute(companies_query)
        companies_data = companies_result.all()
        
        companies = []
        primary_company_id = None
        
        for company, role, permissions, is_primary in companies_data:
            companies.append({
                "company": company,
                "role": role,
                "permissions": permissions or []
            })
            if is_primary:
                primary_company_id = company.id
        
        # Se empresa específica não informada, usa a primária
        current_company_id = company_id or primary_company_id
        
        # Projetos do usuário na empresa atual
        projects = []
        if current_company_id:
            projects_query = (
                select(
                    Project,
                    user_project_association.c.role,
                    user_project_association.c.permissions,
                    user_project_association.c.environments_access
                )
                .join(user_project_association)
                .where(user_project_association.c.user_id == user_id)
                .where(Project.company_id == current_company_id)
                .where(user_project_association.c.is_active == True)
            )
            projects_result = await self.db.execute(projects_query)
            projects_data = projects_result.all()
            
            for project, role, permissions, env_access in projects_data:
                projects.append({
                    "project": project,
                    "role": role,
                    "permissions": permissions or [],
                    "environments_access": env_access or []
                })
        
        return {
            "user": user,
            "current_company_id": current_company_id,
            "companies": companies,
            "projects": projects,
            "is_super_admin": user.is_system_admin
        }


class ProjectService(OrganizationService):
    """Service para gerenciamento de projetos"""
    
    async def create_project(
        self,
        project_data: ProjectCreate,
        current_user: CurrentUser
    ) -> Project:
        """Cria novo projeto"""
        
        # Verifica acesso à empresa
        if not await self._user_has_company_access(current_user.id, project_data.company_id):
            raise ValueError("Acesso negado à empresa")
        
        # Verifica se slug já existe na empresa
        existing = await self.db.execute(
            select(Project).where(
                and_(
                    Project.company_id == project_data.company_id,
                    Project.slug == project_data.slug
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError(f"Projeto '{project_data.slug}' já existe nesta empresa")
        
        # Cria projeto
        project = Project(
            name=project_data.name,
            slug=project_data.slug,
            description=project_data.description,
            company_id=project_data.company_id,
            environments=project_data.environments,
            repository_url=project_data.repository_url,
            documentation_url=project_data.documentation_url,
            tags=project_data.tags,
            created_by=current_user.id,
            status=ProjectStatus.PLANNING
        )
        
        self.db.add(project)
        await self.db.flush()
        
        # Adiciona criador como project manager
        user_project_stmt = user_project_association.insert().values(
            user_id=current_user.id,
            project_id=project.id,
            role=UserRole.PROJECT_MANAGER,
            permissions=["project:admin"],
            environments_access=project_data.environments,
            can_create_secrets=True,
            can_read_secrets=True,
            can_update_secrets=True,
            can_delete_secrets=True,
            can_share_secrets=True
        )
        await self.db.execute(user_project_stmt)
        
        await self.db.commit()
        
        logger.info(
            "Project created",
            project_id=str(project.id),
            company_id=str(project_data.company_id),
            user_id=str(current_user.id)
        )
        
        return project
    
    async def _user_has_company_access(self, user_id: UUID, company_id: UUID) -> bool:
        """Verifica se usuário tem acesso à empresa"""
        query = select(user_company_association).where(
            and_(
                user_company_association.c.user_id == user_id,
                user_company_association.c.company_id == company_id,
                user_company_association.c.is_active == True
            )
        )
        result = await self.db.execute(query)
        return result.first() is not None


class TeamService(OrganizationService):
    """Service para gerenciamento de equipes"""
    
    async def invite_user(
        self,
        invitation_data: TeamInvitationCreate,
        current_user: CurrentUser
    ) -> TeamInvitation:
        """Convida usuário para empresa/projeto"""
        
        # Verifica permissão para convidar
        if not await self._user_has_company_permission(
            current_user.id, invitation_data.company_id, "user:admin"
        ):
            raise ValueError("Permissão insuficiente para convidar usuários")
        
        # Gera token único
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=invitation_data.expires_in_hours)
        
        # Cria convite
        invitation = TeamInvitation(
            email=invitation_data.email,
            token=token,
            company_id=invitation_data.company_id,
            project_id=invitation_data.project_id,
            role=invitation_data.role,
            permissions=invitation_data.permissions,
            environments_access=invitation_data.environments_access,
            invited_by=current_user.id,
            expires_at=expires_at,
            message=invitation_data.message
        )
        
        self.db.add(invitation)
        await self.db.commit()
        
        logger.info(
            "Team invitation created",
            email=invitation_data.email,
            company_id=str(invitation_data.company_id),
            invited_by=str(current_user.id)
        )
        
        return invitation
    
    async def _user_has_company_permission(
        self, 
        user_id: UUID, 
        company_id: UUID, 
        permission: str
    ) -> bool:
        """Verifica permissão na empresa"""
        query = select(
            user_company_association.c.role,
            user_company_association.c.permissions
        ).where(
            and_(
                user_company_association.c.user_id == user_id,
                user_company_association.c.company_id == company_id,
                user_company_association.c.is_active == True
            )
        )
        result = await self.db.execute(query)
        data = result.first()
        
        if not data:
            return False
        
        role, permissions = data
        
        if role == UserRole.COMPANY_ADMIN:
            return True
        
        return permission in (permissions or [])

