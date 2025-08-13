"""
API endpoints para gerenciamento de projetos
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import math

from app.api.deps import get_db, get_current_active_user
from app.schemas.auth import CurrentUser
from app.schemas.organization import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
    ProjectSearchRequest, ProjectWithDetailsResponse
)
from app.services.organization_service import ProjectService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Cria um novo projeto"""
    
    service = ProjectService(db)
    
    try:
        project = await service.create_project(project_data, current_user)
        return ProjectResponse.from_orm(project)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            "Failed to create project",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create project"
        )


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    q: str = Query(None, description="Search query"),
    company_id: UUID = Query(None, description="Company filter"),
    status: str = Query(None, description="Project status filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Lista projetos do usuário"""
    
    search_params = ProjectSearchRequest(
        q=q,
        company_id=company_id,
        status=status,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    # TODO: Implementar busca de projetos
    return ProjectListResponse(
        projects=[],
        total=0,
        page=page,
        size=size,
        total_pages=0
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Obtém projeto por ID"""
    
    # TODO: Implementar busca de projeto
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found"
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    project_data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Atualiza projeto"""
    
    # TODO: Implementar atualização de projeto
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found"
    )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(get_current_active_user)
):
    """Remove projeto"""
    
    # TODO: Implementar remoção de projeto
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found"
    )

