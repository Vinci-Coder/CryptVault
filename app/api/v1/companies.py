"""
API endpoints para gerenciamento de empresas
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import math

from app.api.deps import get_db, get_current_active_user, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.organization import (
    CompanyCreate, CompanyUpdate, CompanyResponse, CompanyListResponse,
    CompanySearchRequest, CompanyStatsResponse
)
from app.services.organization_service import CompanyService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(
    company_data: CompanyCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Cria uma nova empresa"""
    
    service = CompanyService(db)
    
    try:
        company = await service.create_company(company_data, current_user)
        return CompanyResponse.from_orm(company)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to create company",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create company"
        )


@router.get("/", response_model=CompanyListResponse)
async def list_companies(
    q: str = Query(None, description="Search query"),
    type: str = Query(None, description="Company type filter"),
    status: str = Query(None, description="Company status filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Lista empresas do usuário"""
    
    search_params = CompanySearchRequest(
        q=q,
        type=type,
        status=status,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = CompanyService(db)
    
    try:
        companies, total = await service.search_companies(search_params, current_user)
        total_pages = math.ceil(total / size)
        
        return CompanyListResponse(
            companies=[CompanyResponse.from_orm(c) for c in companies],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list companies",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve companies"
        )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Obtém empresa por ID"""
    
    service = CompanyService(db)
    company = await service.get_company(company_id, current_user)
    
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    return CompanyResponse.from_orm(company)


@router.put("/{company_id}", response_model=CompanyResponse)
async def update_company(
    company_id: UUID,
    company_data: CompanyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Atualiza empresa"""
    
    service = CompanyService(db)
    
    try:
        company = await service.update_company(company_id, company_data, current_user)
        
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company not found"
            )
        
        return CompanyResponse.from_orm(company)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to update company",
            company_id=str(company_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update company"
        )


@router.get("/{company_id}/users")
async def get_company_users(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Lista usuários da empresa"""
    
    service = CompanyService(db)
    
    try:
        users = await service.get_company_users(company_id, current_user)
        return {"users": users}
        
    except Exception as e:
        logger.error(
            "Failed to get company users",
            company_id=str(company_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve company users"
        )


@router.get("/{company_id}/stats", response_model=CompanyStatsResponse)
async def get_company_stats(
    company_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("company:admin"))
):
    """Obtém estatísticas da empresa"""
    
    # TODO: Implementar estatísticas detalhadas
    return CompanyStatsResponse(
        total_users=0,
        active_users=0,
        total_projects=0,
        active_projects=0,
        total_secrets=0,
        secrets_by_environment={},
        storage_used_mb=0,
        storage_limit_mb=1024,
        recent_activity=[]
    )

