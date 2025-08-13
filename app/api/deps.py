"""
Dependências da API
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_async_session
from app.services.auth_service import auth_service, AuthServiceError
from app.schemas.auth import CurrentUser
from app.core.logging import get_logger

logger = get_logger(__name__)

# Configuração do bearer token
security = HTTPBearer(auto_error=False)


async def get_db() -> Generator[AsyncSession, None, None]:
    """Dependency para obter sessão do banco de dados"""
    async for session in get_async_session():
        yield session


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> CurrentUser:
    """Obtém o usuário atual autenticado"""
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    try:
        # Autentica com o MS-AuthManager
        user_data = await auth_service.authenticate_user(token)
        
        # Cria objeto do usuário atual
        current_user = CurrentUser(
            id=user_data["user_id"],
            email=user_data.get("email", ""),
            name=user_data.get("name", ""),
            company_id=user_data["company_id"],
            company_name=user_data.get("company_name", ""),
            roles=user_data.get("roles", []),
            permissions=user_data.get("permissions", []),
            is_active=user_data.get("is_active", True)
        )
        
        # Log da autenticação bem-sucedida
        logger.info(
            "User authenticated",
            user_id=str(current_user.id),
            company_id=str(current_user.company_id),
            ip_address=request.client.host if request.client else None
        )
        
        return current_user
        
    except AuthServiceError as e:
        logger.warning(
            "Authentication failed",
            error=str(e),
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(
            "Authentication error",
            error=str(e),
            ip_address=request.client.host if request.client else None
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service unavailable"
        )


async def get_current_active_user(
    current_user: CurrentUser = Depends(get_current_user)
) -> CurrentUser:
    """Verifica se o usuário atual está ativo"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_permission(permission: str):
    """
    Decorator para verificar permissões específicas
    """
    def permission_dependency(
        current_user: CurrentUser = Depends(get_current_active_user)
    ) -> CurrentUser:
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_dependency


def require_role(role: str):
    """
    Decorator para verificar roles específicos
    """
    def role_dependency(
        current_user: CurrentUser = Depends(get_current_active_user)
    ) -> CurrentUser:
        if role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    
    return role_dependency


async def get_request_info(request: Request) -> dict:
    """Extrai informações da requisição para auditoria"""
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "method": request.method,
        "url": str(request.url),
        "timestamp": logger.info("Request received")
    }

