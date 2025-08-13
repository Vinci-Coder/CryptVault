"""
Service layer para operações com secrets
"""
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
import hashlib
import secrets

from app.models.secret import Secret, SecretVersion, SecretPermission, SharedLink, SecretType, SecretStatus
from app.models.audit import AuditLog, AuditAction, AuditLevel
from app.schemas.secret import (
    SecretCreate, SecretUpdate, SecretSearchRequest,
    SharedLinkCreate, SecretPermissionCreate
)
from app.schemas.auth import CurrentUser
from app.services.crypto_service import crypto_service
from app.core.logging import get_logger, audit_logger

logger = get_logger(__name__)


class SecretService:
    """Service para gerenciamento de secrets"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_secret(
        self, 
        secret_data: SecretCreate, 
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> Secret:
        """Cria um novo secret"""
        
        logger.info(
            "Creating new secret",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            secret_name=secret_data.name
        )
        
        # Criptografa o conteúdo
        encryption_result = await crypto_service.encrypt_secret(
            content=secret_data.content,
            secret_type=secret_data.type.value,
            metadata={
                "name": secret_data.name,
                "description": secret_data.description,
                "company_id": str(current_user.company_id),
                "owner_id": str(current_user.id)
            }
        )
        
        # Cria o secret
        secret = Secret(
            name=secret_data.name,
            description=secret_data.description,
            type=SecretType(secret_data.type.value),
            encrypted_data_id=encryption_result["encrypted_id"],
            encrypted_metadata={
                "checksum": encryption_result["checksum"],
                "size": encryption_result["size"]
            },
            company_id=current_user.company_id,
            project_id=secret_data.project_id,
            environment=secret_data.environment,
            tags=secret_data.tags,
            owner_id=current_user.id,
            expires_at=secret_data.expires_at,
            format_validation=secret_data.format_validation
        )
        
        self.db.add(secret)
        await self.db.flush()
        
        # Cria a primeira versão
        version = SecretVersion(
            secret_id=secret.id,
            version_number=1,
            encrypted_data_id=encryption_result["encrypted_id"],
            encrypted_metadata=secret.encrypted_metadata,
            size_bytes=encryption_result["size"],
            checksum=encryption_result["checksum"],
            created_by=current_user.id,
            is_current=True
        )
        
        self.db.add(version)
        await self.db.commit()
        
        # Log de auditoria
        audit_logger.log_secret_modification(
            user_id=str(current_user.id),
            secret_id=str(secret.id),
            action="create",
            changes={
                "name": secret_data.name,
                "type": secret_data.type.value,
                "encrypted_id": encryption_result["encrypted_id"]
            },
            ip_address=ip_address or "unknown"
        )
        
        logger.info(
            "Secret created successfully",
            secret_id=str(secret.id),
            user_id=str(current_user.id)
        )
        
        return secret
    
    async def get_secret(
        self, 
        secret_id: UUID, 
        current_user: CurrentUser,
        include_content: bool = False,
        ip_address: Optional[str] = None
    ) -> Optional[Secret]:
        """Obtém um secret por ID"""
        
        query = select(Secret).where(
            and_(
                Secret.id == secret_id,
                Secret.company_id == current_user.company_id
            )
        ).options(selectinload(Secret.versions))
        
        result = await self.db.execute(query)
        secret = result.scalar_one_or_none()
        
        if not secret:
            return None
        
        # Verifica permissões
        if not await self._check_read_permission(secret, current_user):
            return None
        
        # Se precisa do conteúdo, descriptografa
        if include_content:
            try:
                content = await crypto_service.decrypt_secret(secret.encrypted_data_id)
                secret.content = content  # Adiciona propriedade temporária
                
                # Log de acesso
                audit_logger.log_secret_access(
                    user_id=str(current_user.id),
                    secret_id=str(secret.id),
                    action="read_content",
                    ip_address=ip_address or "unknown",
                    user_agent="api"
                )
                
            except Exception as e:
                logger.error(
                    "Failed to decrypt secret content",
                    secret_id=str(secret.id),
                    error=str(e)
                )
                raise
        
        return secret
    
    async def update_secret(
        self,
        secret_id: UUID,
        secret_data: SecretUpdate,
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> Optional[Secret]:
        """Atualiza um secret"""
        
        secret = await self.get_secret(secret_id, current_user)
        if not secret:
            return None
        
        # Verifica permissão de escrita
        if not await self._check_write_permission(secret, current_user):
            return None
        
        changes = {}
        
        # Atualiza campos básicos
        if secret_data.name is not None:
            changes["name"] = {"old": secret.name, "new": secret_data.name}
            secret.name = secret_data.name
        
        if secret_data.description is not None:
            changes["description"] = {"old": secret.description, "new": secret_data.description}
            secret.description = secret_data.description
        
        if secret_data.project_id is not None:
            changes["project_id"] = {"old": str(secret.project_id) if secret.project_id else None, "new": str(secret_data.project_id)}
            secret.project_id = secret_data.project_id
        
        if secret_data.environment is not None:
            changes["environment"] = {"old": secret.environment, "new": secret_data.environment}
            secret.environment = secret_data.environment
        
        if secret_data.tags is not None:
            changes["tags"] = {"old": secret.tags, "new": secret_data.tags}
            secret.tags = secret_data.tags
        
        if secret_data.expires_at is not None:
            changes["expires_at"] = {"old": secret.expires_at.isoformat() if secret.expires_at else None, "new": secret_data.expires_at.isoformat()}
            secret.expires_at = secret_data.expires_at
        
        if secret_data.status is not None:
            changes["status"] = {"old": secret.status.value, "new": secret_data.status.value}
            secret.status = SecretStatus(secret_data.status.value)
        
        # Se o conteúdo foi alterado, cria nova versão
        if secret_data.content is not None:
            new_version_number = secret.current_version + 1
            
            # Criptografa o novo conteúdo
            encryption_result = await crypto_service.encrypt_secret(
                content=secret_data.content,
                secret_type=secret.type.value,
                metadata={
                    "name": secret.name,
                    "version": new_version_number,
                    "company_id": str(current_user.company_id),
                    "owner_id": str(current_user.id)
                }
            )
            
            # Atualiza secret
            secret.encrypted_data_id = encryption_result["encrypted_id"]
            secret.current_version = new_version_number
            
            # Marca versão anterior como não atual
            await self.db.execute(
                SecretVersion.__table__.update()
                .where(SecretVersion.secret_id == secret.id)
                .values(is_current=False)
            )
            
            # Cria nova versão
            new_version = SecretVersion(
                secret_id=secret.id,
                version_number=new_version_number,
                encrypted_data_id=encryption_result["encrypted_id"],
                encrypted_metadata={
                    "checksum": encryption_result["checksum"],
                    "size": encryption_result["size"]
                },
                size_bytes=encryption_result["size"],
                checksum=encryption_result["checksum"],
                created_by=current_user.id,
                change_description=secret_data.change_description,
                is_current=True
            )
            
            self.db.add(new_version)
            changes["content"] = {"new_version": new_version_number, "encrypted_id": encryption_result["encrypted_id"]}
        
        await self.db.commit()
        
        # Log de auditoria
        audit_logger.log_secret_modification(
            user_id=str(current_user.id),
            secret_id=str(secret.id),
            action="update",
            changes=changes,
            ip_address=ip_address or "unknown"
        )
        
        logger.info(
            "Secret updated successfully",
            secret_id=str(secret.id),
            user_id=str(current_user.id),
            changes=list(changes.keys())
        )
        
        return secret
    
    async def delete_secret(
        self,
        secret_id: UUID,
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> bool:
        """Remove um secret"""
        
        secret = await self.get_secret(secret_id, current_user)
        if not secret:
            return False
        
        # Verifica permissão de exclusão
        if not await self._check_delete_permission(secret, current_user):
            return False
        
        # Remove dados criptografados do serviço
        try:
            await crypto_service.cleanup_encrypted_data(secret.encrypted_data_id)
            
            # Remove dados das versões também
            for version in secret.versions:
                await crypto_service.cleanup_encrypted_data(version.encrypted_data_id)
        
        except Exception as e:
            logger.warning(
                "Failed to cleanup encrypted data",
                secret_id=str(secret.id),
                error=str(e)
            )
        
        # Remove do banco
        await self.db.delete(secret)
        await self.db.commit()
        
        # Log de auditoria
        audit_logger.log_secret_modification(
            user_id=str(current_user.id),
            secret_id=str(secret.id),
            action="delete",
            changes={"name": secret.name, "type": secret.type.value},
            ip_address=ip_address or "unknown"
        )
        
        logger.info(
            "Secret deleted successfully",
            secret_id=str(secret.id),
            user_id=str(current_user.id)
        )
        
        return True
    
    async def search_secrets(
        self,
        search_params: SecretSearchRequest,
        current_user: CurrentUser
    ) -> Tuple[List[Secret], int]:
        """Busca secrets com filtros"""
        
        # Query base
        query = select(Secret).where(Secret.company_id == current_user.company_id)
        count_query = select(func.count(Secret.id)).where(Secret.company_id == current_user.company_id)
        
        # Filtros
        if search_params.q:
            search_filter = or_(
                Secret.name.ilike(f"%{search_params.q}%"),
                Secret.description.ilike(f"%{search_params.q}%")
            )
            query = query.where(search_filter)
            count_query = count_query.where(search_filter)
        
        if search_params.type:
            query = query.where(Secret.type == SecretType(search_params.type.value))
            count_query = count_query.where(Secret.type == SecretType(search_params.type.value))
        
        if search_params.status:
            query = query.where(Secret.status == SecretStatus(search_params.status.value))
            count_query = count_query.where(Secret.status == SecretStatus(search_params.status.value))
        
        if search_params.project_id:
            query = query.where(Secret.project_id == search_params.project_id)
            count_query = count_query.where(Secret.project_id == search_params.project_id)
        
        if search_params.environment:
            query = query.where(Secret.environment == search_params.environment)
            count_query = count_query.where(Secret.environment == search_params.environment)
        
        if search_params.owner_id:
            query = query.where(Secret.owner_id == search_params.owner_id)
            count_query = count_query.where(Secret.owner_id == search_params.owner_id)
        
        if search_params.tags:
            # PostgreSQL JSON contains
            for tag in search_params.tags:
                query = query.where(Secret.tags.contains([tag]))
                count_query = count_query.where(Secret.tags.contains([tag]))
        
        # Filtros de data
        if search_params.created_after:
            query = query.where(Secret.created_at >= search_params.created_after)
            count_query = count_query.where(Secret.created_at >= search_params.created_after)
        
        if search_params.created_before:
            query = query.where(Secret.created_at <= search_params.created_before)
            count_query = count_query.where(Secret.created_at <= search_params.created_before)
        
        if search_params.expires_after:
            query = query.where(Secret.expires_at >= search_params.expires_after)
            count_query = count_query.where(Secret.expires_at >= search_params.expires_after)
        
        if search_params.expires_before:
            query = query.where(Secret.expires_at <= search_params.expires_before)
            count_query = count_query.where(Secret.expires_at <= search_params.expires_before)
        
        # Ordenação
        order_column = getattr(Secret, search_params.sort_by, Secret.created_at)
        if search_params.sort_order == "asc":
            query = query.order_by(asc(order_column))
        else:
            query = query.order_by(desc(order_column))
        
        # Paginação
        offset = (search_params.page - 1) * search_params.size
        query = query.offset(offset).limit(search_params.size)
        
        # Executa queries
        result = await self.db.execute(query)
        secrets = result.scalars().all()
        
        count_result = await self.db.execute(count_query)
        total = count_result.scalar()
        
        return list(secrets), total
    
    async def create_shared_link(
        self,
        secret_id: UUID,
        link_data: SharedLinkCreate,
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> Optional[SharedLink]:
        """Cria link de compartilhamento temporário"""
        
        secret = await self.get_secret(secret_id, current_user)
        if not secret:
            return None
        
        # Verifica permissão de compartilhamento
        if not await self._check_share_permission(secret, current_user):
            return None
        
        # Gera token único
        token = secrets.token_urlsafe(32)
        
        # Calcula expiração
        expires_at = datetime.utcnow() + timedelta(hours=link_data.expires_in_hours)
        
        # Hash da senha se fornecida
        password_hash = None
        if link_data.requires_password and link_data.password:
            password_hash = hashlib.sha256(link_data.password.encode()).hexdigest()
        
        # Cria link
        shared_link = SharedLink(
            secret_id=secret_id,
            token=token,
            max_downloads=link_data.max_downloads,
            requires_password=link_data.requires_password,
            password_hash=password_hash,
            expires_at=expires_at,
            created_by=current_user.id,
            description=link_data.description,
            allowed_ips=link_data.allowed_ips
        )
        
        self.db.add(shared_link)
        await self.db.commit()
        
        # Log de auditoria
        audit_logger.log_secret_modification(
            user_id=str(current_user.id),
            secret_id=str(secret.id),
            action="share",
            changes={
                "token": token[:8] + "...",
                "expires_at": expires_at.isoformat(),
                "max_downloads": link_data.max_downloads
            },
            ip_address=ip_address or "unknown"
        )
        
        logger.info(
            "Shared link created",
            secret_id=str(secret.id),
            user_id=str(current_user.id),
            token=token[:8] + "..."
        )
        
        return shared_link
    
    async def _check_read_permission(self, secret: Secret, current_user: CurrentUser) -> bool:
        """Verifica permissão de leitura"""
        # Proprietário sempre pode ler
        if secret.owner_id == current_user.id:
            return True
        
        # Admin da empresa pode ler
        if "admin" in current_user.roles:
            return True
        
        # Verifica permissões específicas (implementar conforme necessário)
        # TODO: Implementar verificação de permissões granulares
        
        return False
    
    async def _check_write_permission(self, secret: Secret, current_user: CurrentUser) -> bool:
        """Verifica permissão de escrita"""
        # Proprietário sempre pode escrever
        if secret.owner_id == current_user.id:
            return True
        
        # Admin da empresa pode escrever
        if "admin" in current_user.roles:
            return True
        
        return False
    
    async def _check_delete_permission(self, secret: Secret, current_user: CurrentUser) -> bool:
        """Verifica permissão de exclusão"""
        # Proprietário sempre pode deletar
        if secret.owner_id == current_user.id:
            return True
        
        # Admin da empresa pode deletar
        if "admin" in current_user.roles:
            return True
        
        return False
    
    async def _check_share_permission(self, secret: Secret, current_user: CurrentUser) -> bool:
        """Verifica permissão de compartilhamento"""
        # Proprietário sempre pode compartilhar
        if secret.owner_id == current_user.id:
            return True
        
        # Admin da empresa pode compartilhar
        if "admin" in current_user.roles:
            return True
        
        return False

