"""
API endpoints para gerenciamento de usuários
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_db, get_current_active_user
from app.schemas.auth import CurrentUser
from app.schemas.organization import (
    UserResponse, UserWithCompaniesResponse, UserSearchRequest,
    CurrentUserContext, SwitchCompanyRequest
)
from app.services.organization_service import UserService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/me", response_model=CurrentUserContext)
async def get_current_user_context(
    company_id: UUID = Query(None, description="Company context"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Obtém contexto completo do usuário atual"""
    
    service = UserService(db)
    
    try:
        context = await service.get_user_context(current_user.id, company_id)
        
        if not context:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User context not found"
            )
        
        return CurrentUserContext(
            user=UserResponse.from_orm(context["user"]),
            current_company_id=context["current_company_id"],
            companies=context["companies"],
            projects=context["projects"],
            permissions=context.get("permissions", []),
            is_super_admin=context["is_super_admin"]
        )
        
    except Exception as e:
        logger.error(
            "Failed to get user context",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user context"
        )


@router.post("/me/switch-company")
async def switch_company(
    switch_data: SwitchCompanyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Troca empresa ativa do usuário"""
    
    service = UserService(db)
    
    try:
        # Verifica se usuário tem acesso à empresa
        context = await service.get_user_context(current_user.id, switch_data.company_id)
        
        if not context or not any(
            c["company"].id == switch_data.company_id for c in context["companies"]
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to company"
            )
        
        return {"message": "Company switched successfully", "company_id": str(switch_data.company_id)}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Failed to switch company",
            user_id=str(current_user.id),
            company_id=str(switch_data.company_id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to switch company"
        )


@router.get("/", response_model=List[UserResponse])
async def list_users(
    q: str = Query(None, description="Search query"),
    company_id: UUID = Query(None, description="Company filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Lista usuários (filtrado por empresa se especificada)"""
    
    # TODO: Implementar listagem de usuários
    return []


@router.get("/{user_id}", response_model=UserWithCompaniesResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Obtém usuário por ID"""
    
    # TODO: Implementar busca de usuário
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
    )

