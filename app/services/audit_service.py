"""
Service layer para auditoria e logs
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from uuid import UUID

from app.models.audit import AuditLog, SecurityEvent, AccessLog, AuditAction, AuditLevel
from app.schemas.auth import CurrentUser
from app.schemas.audit import AuditLogSearchRequest
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditService:
    """Service para gerenciamento de auditoria"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_audit_logs(
        self,
        search_params: AuditLogSearchRequest,
        current_user: CurrentUser
    ) -> Tuple[List[AuditLog], int]:
        """Busca logs de auditoria com filtros"""
        
        # Query base - filtra por empresa
        query = select(AuditLog).where(AuditLog.company_id == current_user.company_id)
        count_query = select(func.count(AuditLog.id)).where(AuditLog.company_id == current_user.company_id)
        
        # Filtros
        if search_params.q:
            search_filter = or_(
                AuditLog.description.ilike(f"%{search_params.q}%"),
                AuditLog.resource_type.ilike(f"%{search_params.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if search_params.action:
            try:
                action_enum = AuditAction(search_params.action)
                query = query.where(AuditLog.action == action_enum)
                count_query = count_query.where(AuditLog.action == action_enum)
            except ValueError:
                pass
        
        if search_params.user_id:
            query = query.where(AuditLog.user_id == search_params.user_id)
            count_query = count_query.where(AuditLog.user_id == search_params.user_id)
        
        if search_params.resource_id:
            query = query.where(AuditLog.resource_id == search_params.resource_id)
            count_query = count_query.where(AuditLog.resource_id == search_params.resource_id)
        
        if search_params.level:
            try:
                level_enum = AuditLevel(search_params.level)
                query = query.where(AuditLog.level == level_enum)
                count_query = count_query.where(AuditLog.level == level_enum)
            except ValueError:
                pass
        
        # Filtros de data
        if search_params.start_date:
            query = query.where(AuditLog.created_at >= search_params.start_date)
            count_query = count_query.where(AuditLog.created_at >= search_params.start_date)
        
        if search_params.end_date:
            query = query.where(AuditLog.created_at <= search_params.end_date)
            count_query = count_query.where(AuditLog.created_at <= search_params.end_date)
        
        # Ordenação (mais recentes primeiro)
        query = query.order_by(desc(AuditLog.created_at))
        
        # Paginação
        offset = (search_params.page - 1) * search_params.size
        query = query.offset(offset).limit(search_params.size)
        
        # Executa queries
        result = await self.db.execute(query)
        logs = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(logs), total
    
    async def get_audit_log(
        self,
        log_id: UUID,
        current_user: CurrentUser
    ) -> Optional[AuditLog]:
        """Obtém um log de auditoria específico"""
        
        query = select(AuditLog).where(
            and_(
                AuditLog.id == log_id,
                AuditLog.company_id == current_user.company_id
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def search_security_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        is_resolved: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        size: int = 20,
        current_user: CurrentUser = None
    ) -> Tuple[List[SecurityEvent], int]:
        """Busca eventos de segurança"""
        
        # Query base
        query = select(SecurityEvent).where(SecurityEvent.company_id == current_user.company_id)
        count_query = select(func.count(SecurityEvent.id)).where(SecurityEvent.company_id == current_user.company_id)
        
        # Filtros
        if event_type:
            query = query.where(SecurityEvent.event_type == event_type)
            count_query = count_query.where(SecurityEvent.event_type == event_type)
        
        if severity:
            try:
                severity_enum = AuditLevel(severity)
                query = query.where(SecurityEvent.severity == severity_enum)
                count_query = count_query.where(SecurityEvent.severity == severity_enum)
            except ValueError:
                pass
        
        if is_resolved:
            query = query.where(SecurityEvent.is_resolved == is_resolved)
            count_query = count_query.where(SecurityEvent.is_resolved == is_resolved)
        
        if start_date:
            query = query.where(SecurityEvent.created_at >= start_date)
            count_query = count_query.where(SecurityEvent.created_at >= start_date)
        
        if end_date:
            query = query.where(SecurityEvent.created_at <= end_date)
            count_query = count_query.where(SecurityEvent.created_at <= end_date)
        
        # Ordenação
        query = query.order_by(desc(SecurityEvent.created_at))
        
        # Paginação
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)
        
        # Executa queries
        result = await self.db.execute(query)
        events = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(events), total
    
    async def get_secret_access_logs(
        self,
        secret_id: UUID,
        since: datetime,
        current_user: CurrentUser
    ) -> List[AccessLog]:
        """Obtém logs de acesso de um secret"""
        
        query = select(AccessLog).where(
            and_(
                AccessLog.secret_id == secret_id,
                AccessLog.company_id == current_user.company_id,
                AccessLog.timestamp >= since
            )
        ).order_by(desc(AccessLog.timestamp))
        
        result = await self.db.execute(query)
        return list(result.scalars().all())
    
    async def get_audit_summary(
        self,
        since: datetime,
        current_user: CurrentUser
    ) -> Dict[str, Any]:
        """Obtém resumo estatístico de auditoria"""
        
        # Total de eventos
        total_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.created_at >= since
            )
        )
        total_result = await self.db.execute(total_query)
        total_events = total_result.scalar()
        
        # Eventos por ação
        action_query = select(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.created_at >= since
            )
        ).group_by(AuditLog.action)
        
        action_result = await self.db.execute(action_query)
        by_action = {row.action.value: row.count for row in action_result}
        
        # Eventos por nível
        level_query = select(
            AuditLog.level,
            func.count(AuditLog.id).label('count')
        ).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.created_at >= since
            )
        ).group_by(AuditLog.level)
        
        level_result = await self.db.execute(level_query)
        by_level = {row.level.value: row.count for row in level_result}
        
        # Top usuários por atividade
        user_query = select(
            AuditLog.user_id,
            func.count(AuditLog.id).label('count')
        ).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.created_at >= since,
                AuditLog.user_id.isnot(None)
            )
        ).group_by(AuditLog.user_id).order_by(desc('count')).limit(10)
        
        user_result = await self.db.execute(user_query)
        by_user = [{"user_id": str(row.user_id), "count": row.count} for row in user_result]
        
        # Eventos críticos recentes
        critical_query = select(AuditLog).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.level == AuditLevel.CRITICAL,
                AuditLog.created_at >= since
            )
        ).order_by(desc(AuditLog.created_at)).limit(5)
        
        critical_result = await self.db.execute(critical_query)
        recent_critical = list(critical_result.scalars().all())
        
        # Eventos de segurança
        security_query = select(func.count(SecurityEvent.id)).where(
            and_(
                SecurityEvent.company_id == current_user.company_id,
                SecurityEvent.created_at >= since
            )
        )
        security_result = await self.db.execute(security_query)
        security_events_count = security_result.scalar()
        
        # Eventos de segurança não resolvidos
        unresolved_query = select(func.count(SecurityEvent.id)).where(
            and_(
                SecurityEvent.company_id == current_user.company_id,
                SecurityEvent.is_resolved == "pending"
            )
        )
        unresolved_result = await self.db.execute(unresolved_query)
        unresolved_security_events = unresolved_result.scalar()
        
        # Secrets mais acessados
        access_query = select(
            AccessLog.secret_id,
            func.count(AccessLog.id).label('count')
        ).where(
            and_(
                AccessLog.company_id == current_user.company_id,
                AccessLog.timestamp >= since
            )
        ).group_by(AccessLog.secret_id).order_by(desc('count')).limit(10)
        
        access_result = await self.db.execute(access_query)
        most_accessed_secrets = [{"secret_id": str(row.secret_id), "count": row.count} for row in access_result]
        
        # Autenticações falhadas
        failed_auth_query = select(func.count(AuditLog.id)).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.action == AuditAction.AUTH_FAILED,
                AuditLog.created_at >= since
            )
        )
        failed_auth_result = await self.db.execute(failed_auth_query)
        failed_authentications = failed_auth_result.scalar()
        
        # Usuários únicos
        unique_users_query = select(func.count(func.distinct(AuditLog.user_id))).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.created_at >= since,
                AuditLog.user_id.isnot(None)
            )
        )
        unique_users_result = await self.db.execute(unique_users_query)
        unique_users = unique_users_result.scalar()
        
        # IPs únicos
        unique_ips_query = select(func.count(func.distinct(AuditLog.ip_address))).where(
            and_(
                AuditLog.company_id == current_user.company_id,
                AuditLog.created_at >= since,
                AuditLog.ip_address.isnot(None)
            )
        )
        unique_ips_result = await self.db.execute(unique_ips_query)
        unique_ips = unique_ips_result.scalar()
        
        return {
            "total_events": total_events,
            "by_action": by_action,
            "by_level": by_level,
            "by_user": by_user,
            "recent_critical": recent_critical,
            "security_events_count": security_events_count,
            "unresolved_security_events": unresolved_security_events,
            "most_accessed_secrets": most_accessed_secrets,
            "failed_authentications": failed_authentications,
            "unique_users": unique_users,
            "unique_ips": unique_ips
        }
    
    async def resolve_security_event(
        self,
        event_id: UUID,
        resolution_notes: str,
        current_user: CurrentUser
    ) -> Optional[SecurityEvent]:
        """Marca um evento de segurança como resolvido"""
        
        query = select(SecurityEvent).where(
            and_(
                SecurityEvent.id == event_id,
                SecurityEvent.company_id == current_user.company_id
            )
        )
        
        result = await self.db.execute(query)
        event = result.scalar_one_or_none()
        
        if not event:
            return None
        
        # Atualiza evento
        event.is_resolved = "resolved"
        event.resolved_at = datetime.utcnow()
        event.resolved_by = current_user.id
        event.resolution_notes = resolution_notes
        
        await self.db.commit()
        
        logger.info(
            "Security event resolved",
            event_id=str(event_id),
            resolved_by=str(current_user.id),
            event_type=event.event_type
        )
        
        return event
    
    async def create_security_event(
        self,
        event_type: str,
        title: str,
        description: str,
        severity: AuditLevel = AuditLevel.MEDIUM,
        user_id: Optional[UUID] = None,
        company_id: Optional[UUID] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None
    ) -> SecurityEvent:
        """Cria um novo evento de segurança"""
        
        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            user_id=user_id,
            company_id=company_id,
            title=title,
            description=description,
            source_ip=source_ip,
            user_agent=user_agent,
            event_data=event_data or {}
        )
        
        self.db.add(event)
        await self.db.commit()
        
        logger.warning(
            "Security event created",
            event_type=event_type,
            severity=severity.value,
            title=title,
            user_id=str(user_id) if user_id else None,
            company_id=str(company_id) if company_id else None
        )
        
        return event

