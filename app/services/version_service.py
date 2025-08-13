"""
Service layer para versionamento de secrets
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.models.secret import Secret, SecretVersion
from app.schemas.auth import CurrentUser
from app.schemas.secret import SecretWithContentResponse, SecretResponse
from app.services.crypto_service import crypto_service
from app.services.secret_service import SecretService
from app.core.logging import get_logger, audit_logger

logger = get_logger(__name__)


class VersionService:
    """Service para gerenciamento de versões de secrets"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.secret_service = SecretService(db)
    
    async def list_versions(
        self,
        secret_id: UUID,
        current_user: CurrentUser
    ) -> List[SecretVersion]:
        """Lista todas as versões de um secret"""
        
        # Verifica se o secret existe e o usuário tem permissão
        secret = await self.secret_service.get_secret(secret_id, current_user)
        if not secret:
            return []
        
        # Busca versões ordenadas por número decrescente
        query = select(SecretVersion).where(
            SecretVersion.secret_id == secret_id
        ).order_by(desc(SecretVersion.version_number))
        
        result = await self.db.execute(query)
        versions = result.scalars().all()
        
        logger.info(
            "Listed secret versions",
            secret_id=str(secret_id),
            user_id=str(current_user.id),
            version_count=len(versions)
        )
        
        return list(versions)
    
    async def get_version(
        self,
        secret_id: UUID,
        version_number: int,
        current_user: CurrentUser
    ) -> Optional[SecretVersion]:
        """Obtém uma versão específica"""
        
        # Verifica se o secret existe e o usuário tem permissão
        secret = await self.secret_service.get_secret(secret_id, current_user)
        if not secret:
            return None
        
        # Busca a versão específica
        query = select(SecretVersion).where(
            and_(
                SecretVersion.secret_id == secret_id,
                SecretVersion.version_number == version_number
            )
        )
        
        result = await self.db.execute(query)
        version = result.scalar_one_or_none()
        
        return version
    
    async def get_version_content(
        self,
        secret_id: UUID,
        version_number: int,
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> Optional[SecretWithContentResponse]:
        """Obtém o conteúdo descriptografado de uma versão"""
        
        # Busca a versão
        version = await self.get_version(secret_id, version_number, current_user)
        if not version:
            return None
        
        # Busca o secret para informações completas
        secret = await self.secret_service.get_secret(secret_id, current_user)
        if not secret:
            return None
        
        try:
            # Descriptografa o conteúdo da versão
            content = await crypto_service.decrypt_secret(version.encrypted_data_id)
            
            # Log de acesso
            audit_logger.log_secret_access(
                user_id=str(current_user.id),
                secret_id=str(secret_id),
                action="read_version_content",
                ip_address=ip_address or "unknown",
                user_agent="api",
                version_number=version_number
            )
            
            # Monta resposta
            secret_data = SecretResponse.from_orm(secret).dict()
            secret_data['content'] = content
            
            return SecretWithContentResponse(**secret_data)
            
        except Exception as e:
            logger.error(
                "Failed to decrypt version content",
                secret_id=str(secret_id),
                version_number=version_number,
                encrypted_id=version.encrypted_data_id,
                error=str(e)
            )
            raise
    
    async def restore_version(
        self,
        secret_id: UUID,
        version_number: int,
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> Optional[SecretVersion]:
        """Restaura uma versão específica como a versão atual"""
        
        # Busca a versão a ser restaurada
        version_to_restore = await self.get_version(secret_id, version_number, current_user)
        if not version_to_restore:
            return None
        
        # Busca o secret
        secret = await self.secret_service.get_secret(secret_id, current_user)
        if not secret:
            return None
        
        # Verifica permissão de escrita
        if not await self.secret_service._check_write_permission(secret, current_user):
            return None
        
        # Se já é a versão atual, retorna ela mesmo
        if version_to_restore.is_current:
            return version_to_restore
        
        try:
            # Obtém o conteúdo da versão a ser restaurada
            old_content = await crypto_service.decrypt_secret(version_to_restore.encrypted_data_id)
            
            # Criptografa novamente (nova chave/algoritmo se necessário)
            new_version_number = secret.current_version + 1
            encryption_result = await crypto_service.encrypt_secret(
                content=old_content,
                secret_type=secret.type.value,
                metadata={
                    "name": secret.name,
                    "version": new_version_number,
                    "restored_from": version_number,
                    "company_id": str(current_user.company_id),
                    "owner_id": str(current_user.id)
                }
            )
            
            # Marca todas as versões como não atuais
            await self.db.execute(
                SecretVersion.__table__.update()
                .where(SecretVersion.secret_id == secret_id)
                .values(is_current=False)
            )
            
            # Cria nova versão baseada na restaurada
            new_version = SecretVersion(
                secret_id=secret_id,
                version_number=new_version_number,
                encrypted_data_id=encryption_result["encrypted_id"],
                encrypted_metadata={
                    "checksum": encryption_result["checksum"],
                    "size": encryption_result["size"],
                    "restored_from": version_number
                },
                size_bytes=encryption_result["size"],
                checksum=encryption_result["checksum"],
                created_by=current_user.id,
                change_description=f"Restored from version {version_number}",
                is_current=True
            )
            
            self.db.add(new_version)
            
            # Atualiza o secret
            secret.encrypted_data_id = encryption_result["encrypted_id"]
            secret.current_version = new_version_number
            
            await self.db.commit()
            
            # Log de auditoria
            audit_logger.log_secret_modification(
                user_id=str(current_user.id),
                secret_id=str(secret_id),
                action="restore_version",
                changes={
                    "restored_from_version": version_number,
                    "new_version": new_version_number,
                    "encrypted_id": encryption_result["encrypted_id"]
                },
                ip_address=ip_address or "unknown"
            )
            
            logger.info(
                "Version restored successfully",
                secret_id=str(secret_id),
                restored_from=version_number,
                new_version=new_version_number,
                user_id=str(current_user.id)
            )
            
            return new_version
            
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to restore version",
                secret_id=str(secret_id),
                version_number=version_number,
                user_id=str(current_user.id),
                error=str(e)
            )
            raise
    
    async def delete_version(
        self,
        secret_id: UUID,
        version_number: int,
        current_user: CurrentUser,
        ip_address: Optional[str] = None
    ) -> bool:
        """Remove uma versão específica (não pode ser a versão atual)"""
        
        # Busca a versão
        version = await self.get_version(secret_id, version_number, current_user)
        if not version:
            return False
        
        # Não pode deletar a versão atual
        if version.is_current:
            logger.warning(
                "Attempt to delete current version",
                secret_id=str(secret_id),
                version_number=version_number,
                user_id=str(current_user.id)
            )
            return False
        
        # Verifica se o secret existe e permissões
        secret = await self.secret_service.get_secret(secret_id, current_user)
        if not secret:
            return False
        
        if not await self.secret_service._check_delete_permission(secret, current_user):
            return False
        
        try:
            # Remove dados criptografados do serviço
            await crypto_service.cleanup_encrypted_data(version.encrypted_data_id)
            
            # Remove a versão do banco
            await self.db.delete(version)
            await self.db.commit()
            
            # Log de auditoria
            audit_logger.log_secret_modification(
                user_id=str(current_user.id),
                secret_id=str(secret_id),
                action="delete_version",
                changes={
                    "deleted_version": version_number,
                    "encrypted_id": version.encrypted_data_id
                },
                ip_address=ip_address or "unknown"
            )
            
            logger.info(
                "Version deleted successfully",
                secret_id=str(secret_id),
                version_number=version_number,
                user_id=str(current_user.id)
            )
            
            return True
            
        except Exception as e:
            await self.db.rollback()
            logger.error(
                "Failed to delete version",
                secret_id=str(secret_id),
                version_number=version_number,
                user_id=str(current_user.id),
                error=str(e)
            )
            return False
    
    async def cleanup_old_versions(
        self,
        secret_id: UUID,
        keep_last_n: int = 10
    ) -> int:
        """Limpa versões antigas, mantendo apenas as N mais recentes"""
        
        # Busca todas as versões ordenadas por número decrescente
        query = select(SecretVersion).where(
            SecretVersion.secret_id == secret_id
        ).order_by(desc(SecretVersion.version_number))
        
        result = await self.db.execute(query)
        all_versions = result.scalars().all()
        
        # Identifica versões a serem removidas (exceto a atual)
        versions_to_keep = []
        versions_to_delete = []
        
        for version in all_versions:
            if version.is_current:
                versions_to_keep.append(version)
            elif len(versions_to_keep) < keep_last_n:
                versions_to_keep.append(version)
            else:
                versions_to_delete.append(version)
        
        deleted_count = 0
        
        # Remove versões antigas
        for version in versions_to_delete:
            try:
                # Remove dados criptografados
                await crypto_service.cleanup_encrypted_data(version.encrypted_data_id)
                
                # Remove do banco
                await self.db.delete(version)
                deleted_count += 1
                
            except Exception as e:
                logger.warning(
                    "Failed to cleanup version",
                    secret_id=str(secret_id),
                    version_number=version.version_number,
                    error=str(e)
                )
        
        if deleted_count > 0:
            await self.db.commit()
            
            logger.info(
                "Cleaned up old versions",
                secret_id=str(secret_id),
                deleted_count=deleted_count,
                kept_count=len(versions_to_keep)
            )
        
        return deleted_count

