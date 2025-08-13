"""
API endpoints para auditoria e logs
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from uuid import UUID
import math

from app.api.deps import get_db, get_current_active_user, require_permission
from app.schemas.auth import CurrentUser
from app.schemas.audit import (
    AuditLogResponse, AuditLogSearchRequest, AuditLogListResponse,
    SecurityEventResponse, SecurityEventListResponse, AccessLogResponse
)
from app.services.audit_service import AuditService
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/logs", response_model=AuditLogListResponse)
async def list_audit_logs(
    q: Optional[str] = Query(None, description="Search query"),
    action: Optional[str] = Query(None, description="Action filter"),
    user_id: Optional[UUID] = Query(None, description="User ID filter"),
    resource_id: Optional[UUID] = Query(None, description="Resource ID filter"),
    level: Optional[str] = Query(None, description="Level filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("audit:read"))
):
    """Lista logs de auditoria com filtros"""
    
    # Constrói parâmetros de busca
    search_params = AuditLogSearchRequest(
        q=q,
        action=action,
        user_id=user_id,
        resource_id=resource_id,
        level=level,
        start_date=start_date,
        end_date=end_date,
        page=page,
        size=size
    )
    
    service = AuditService(db)
    
    try:
        logs, total = await service.search_audit_logs(search_params, current_user)
        total_pages = math.ceil(total / size)
        
        return AuditLogListResponse(
            logs=[AuditLogResponse.from_orm(log) for log in logs],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list audit logs",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("audit:read"))
):
    """Obtém um log de auditoria específico"""
    
    service = AuditService(db)
    
    log = await service.get_audit_log(log_id, current_user)
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit log not found"
        )
    
    return AuditLogResponse.from_orm(log)


@router.get("/security-events", response_model=SecurityEventListResponse)
async def list_security_events(
    event_type: Optional[str] = Query(None, description="Event type filter"),
    severity: Optional[str] = Query(None, description="Severity filter"),
    is_resolved: Optional[str] = Query(None, description="Resolution status filter"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("security:read"))
):
    """Lista eventos de segurança"""
    
    service = AuditService(db)
    
    try:
        events, total = await service.search_security_events(
            event_type=event_type,
            severity=severity,
            is_resolved=is_resolved,
            start_date=start_date,
            end_date=end_date,
            page=page,
            size=size,
            current_user=current_user
        )
        
        total_pages = math.ceil(total / size)
        
        return SecurityEventListResponse(
            events=[SecurityEventResponse.from_orm(event) for event in events],
            total=total,
            page=page,
            size=size,
            total_pages=total_pages
        )
        
    except Exception as e:
        logger.error(
            "Failed to list security events",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security events"
        )


@router.get("/access-logs/{secret_id}", response_model=List[AccessLogResponse])
async def get_secret_access_logs(
    secret_id: UUID,
    hours: int = Query(24, ge=1, le=720, description="Hours back to search"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("audit:read"))
):
    """Obtém logs de acesso de um secret específico"""
    
    service = AuditService(db)
    
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        access_logs = await service.get_secret_access_logs(
            secret_id=secret_id,
            since=since,
            current_user=current_user
        )
        
        return [AccessLogResponse.from_orm(log) for log in access_logs]
        
    except Exception as e:
        logger.error(
            "Failed to get secret access logs",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve access logs"
        )


@router.get("/stats/summary")
async def get_audit_summary(
    hours: int = Query(24, ge=1, le=720, description="Hours back to analyze"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("audit:admin"))
):
    """Obtém resumo estatístico de auditoria"""
    
    service = AuditService(db)
    
    try:
        since = datetime.utcnow() - timedelta(hours=hours)
        
        summary = await service.get_audit_summary(
            since=since,
            current_user=current_user
        )
        
        return summary
        
    except Exception as e:
        logger.error(
            "Failed to get audit summary",
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit summary"
        )


@router.post("/security-events/{event_id}/resolve", response_model=SecurityEventResponse)
async def resolve_security_event(
    event_id: UUID,
    resolution_notes: str = Query(..., description="Resolution notes"),
    db: AsyncSession = Depends(get_db),
    current_user: CurrentUser = Depends(require_permission("security:manage"))
):
    """Marca um evento de segurança como resolvido"""
    
    service = AuditService(db)
    
    try:
        event = await service.resolve_security_event(
            event_id=event_id,
            resolution_notes=resolution_notes,
            current_user=current_user
        )
        
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Security event not found"
            )
        
        return SecurityEventResponse.from_orm(event)
        
    except Exception as e:
        logger.error(
            "Failed to resolve security event",
            event_id=str(event_id),
            user_id=str(current_user.id),
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve security event"
        )

