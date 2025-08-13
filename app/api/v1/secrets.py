"""
API endpoints para secrets
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import math

from app.api.deps import get_db, get_current_active_user, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.secret import (
    SecretCreate, SecretUpdate, SecretResponse, SecretWithContentResponse,
    SecretListResponse, SecretSearchRequest, SharedLinkCreate, SharedLinkResponse,
    SecretVersionListResponse, SecretStatsResponse
)
from app.services.secret_service import SecretService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Obtém IP do cliente"""
    return request.client.host if request.client else "unknown"


@router.post("/", response_model=SecretResponse, status_code=status.HTTP_201_CREATED)
async def create_secret(
    secret_data: SecretCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:create"))
):
    """Cria um novo secret"""
    
    logger.info(
        "Creating secret via API",
        user_id=str(current_user.id),
        secret_name=secret_data.name
    )
    
    service = SecretService(db)
    
    try:
        secret = await service.create_secret(
            secret_data=secret_data,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        return SecretResponse.from_orm(secret)
        
    except Exception as e:
        logger.error(
            "Failed to create secret",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create secret"
        )


@router.get("/", response_model=SecretListResponse)
async def list_secrets(
    request: Request,
    q: Optional[str] = Query(None, description="Search query"),
    type: Optional[str] = Query(None, description="Secret type filter"),
    status: Optional[str] = Query(None, description="Secret status filter"),
    project_id: Optional[UUID] = Query(None, description="Project ID filter"),
    environment: Optional[str] = Query(None, description="Environment filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Lista secrets com filtros e paginação"""
    
    # Constrói parâmetros de busca
    search_params = SecretSearchRequest(
        q=q,
        type=type,
        status=status,
        project_id=project_id,
        environment=environment,
        page=page,
        size=size,
        sort_by=sort_by,
        sort_order=sort_order
    )
    
    service = SecretService(db)
    
    try:
        secrets, total = await service.search_secrets(search_params, current_user)
        total_pages = math.ceil(total / size)
        
        return SecretListResponse(
            secrets=[SecretResponse.from_orm(s) for s in secrets],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list secrets",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve secrets"
        )


@router.get("/{secret_id}", response_model=SecretResponse)
async def get_secret(
    secret_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Obtém um secret por ID (sem conteúdo)"""
    
    service = SecretService(db)
    
    secret = await service.get_secret(
        secret_id=secret_id,
        current_user=current_user,
        include_content=False,
        ip_address=get_client_ip(request)
    )
    
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )
    
    return SecretResponse.from_orm(secret)


@router.get("/{secret_id}/content", response_model=SecretWithContentResponse)
async def get_secret_content(
    secret_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Obtém um secret com conteúdo descriptografado"""
    
    service = SecretService(db)
    
    try:
        secret = await service.get_secret(
            secret_id=secret_id,
            current_user=current_user,
            include_content=True,
            ip_address=get_client_ip(request)
        )
        
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found"
            )
        
        # Cria resposta com conteúdo
        response_data = SecretResponse.from_orm(secret).dict()
        response_data['content'] = secret.content
        
        return SecretWithContentResponse(**response_data)
        
    except Exception as e:
        logger.error(
            "Failed to get secret content",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt secret content"
        )


@router.put("/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: UUID,
    secret_data: SecretUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:update"))
):
    """Atualiza um secret"""
    
    service = SecretService(db)
    
    try:
        secret = await service.update_secret(
            secret_id=secret_id,
            secret_data=secret_data,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        if not secret:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found"
            )
        
        return SecretResponse.from_orm(secret)
        
    except Exception as e:
        logger.error(
            "Failed to update secret",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update secret"
        )


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:delete"))
):
    """Remove um secret"""
    
    service = SecretService(db)
    
    try:
        success = await service.delete_secret(
            secret_id=secret_id,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found"
            )
        
    except Exception as e:
        logger.error(
            "Failed to delete secret",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete secret"
        )


@router.post("/{secret_id}/share", response_model=SharedLinkResponse)
async def create_shared_link(
    secret_id: UUID,
    link_data: SharedLinkCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:share"))
):
    """Cria link de compartilhamento temporário"""
    
    service = SecretService(db)
    
    try:
        shared_link = await service.create_shared_link(
            secret_id=secret_id,
            link_data=link_data,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        if not shared_link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Secret not found"
            )
        
        return SharedLinkResponse.from_orm(shared_link)
        
    except Exception as e:
        logger.error(
            "Failed to create shared link",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create shared link"
        )


@router.get("/{secret_id}/versions", response_model=SecretVersionListResponse)
async def list_secret_versions(
    secret_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Lista versões de um secret"""
    
    service = SecretService(db)
    
    secret = await service.get_secret(secret_id, current_user)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )
    
    # Busca versões
    from app.schemas.secret import SecretVersionResponse
    versions = [SecretVersionResponse.from_orm(v) for v in secret.versions]
    
    return SecretVersionListResponse(
        versions=versions,
        total=len(versions)
    )


# Endpoints administrativos
@router.get("/stats/overview", response_model=SecretStatsResponse)
async def get_secrets_stats(
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:admin"))
):
    """Obtém estatísticas dos secrets (admin)"""
    
    # TODO: Implementar estatísticas detalhadas
    return SecretStatsResponse(
        total_secrets=0,
        by_type={},
        by_status={},
        by_environment={},
        expiring_soon=0,
        recently_created=0,
        most_accessed=[]
    )

