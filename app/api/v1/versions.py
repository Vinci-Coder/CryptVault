"""
API endpoints para versionamento de secrets
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_db, get_current_active_user, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.secret import SecretVersionResponse, SecretWithContentResponse
from app.services.version_service import VersionService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_client_ip(request: Request) -> str:
    """Obtém IP do cliente"""
    return request.client.host if request.client else "unknown"


@router.get("/{secret_id}/versions", response_model=List[SecretVersionResponse])
async def list_versions(
    secret_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Lista todas as versões de um secret"""
    
    service = VersionService(db)
    
    try:
        versions = await service.list_versions(secret_id, current_user)
        return [SecretVersionResponse.from_orm(v) for v in versions]
        
    except Exception as e:
        logger.error(
            "Failed to list versions",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve versions"
        )


@router.get("/{secret_id}/versions/{version_number}", response_model=SecretVersionResponse)
async def get_version(
    secret_id: UUID,
    version_number: int,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Obtém uma versão específica de um secret"""
    
    service = VersionService(db)
    
    version = await service.get_version(secret_id, version_number, current_user)
    
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found"
        )
    
    return SecretVersionResponse.from_orm(version)


@router.get("/{secret_id}/versions/{version_number}/content", response_model=SecretWithContentResponse)
async def get_version_content(
    secret_id: UUID,
    version_number: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:read"))
):
    """Obtém o conteúdo de uma versão específica"""
    
    service = VersionService(db)
    
    try:
        secret_content = await service.get_version_content(
            secret_id=secret_id,
            version_number=version_number,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        if not secret_content:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return secret_content
        
    except Exception as e:
        logger.error(
            "Failed to get version content",
            secret_id=str(secret_id),
            version_number=version_number,
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve version content"
        )


@router.post("/{secret_id}/versions/{version_number}/restore", response_model=SecretVersionResponse)
async def restore_version(
    secret_id: UUID,
    version_number: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:update"))
):
    """Restaura uma versão específica como a versão atual"""
    
    service = VersionService(db)
    
    try:
        new_version = await service.restore_version(
            secret_id=secret_id,
            version_number=version_number,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        if not new_version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Version not found"
            )
        
        return SecretVersionResponse.from_orm(new_version)
        
    except Exception as e:
        logger.error(
            "Failed to restore version",
            secret_id=str(secret_id),
            version_number=version_number,
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to restore version"
        )


@router.delete("/{secret_id}/versions/{version_number}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_version(
    secret_id: UUID,
    version_number: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("secret:delete"))
):
    """Remove uma versão específica (não pode ser a versão atual)"""
    
    service = VersionService(db)
    
    try:
        success = await service.delete_version(
            secret_id=secret_id,
            version_number=version_number,
            current_user=current_user,
            ip_address=get_client_ip(request)
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete current version or version not found"
            )
        
    except Exception as e:
        logger.error(
            "Failed to delete version",
            secret_id=str(secret_id),
            version_number=version_number,
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete version"
        )

