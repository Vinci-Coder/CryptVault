"""
Interface para o MS-AuthManager
"""
import httpx
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthServiceError(Exception):
    """Exceção para erros do serviço de autenticação"""
    pass


class AuthManagerClient:
    """Cliente para comunicação com o MS-AuthManager"""
    
    def __init__(self):
        self.base_url = settings.AUTH_MANAGER_URL
        self.api_key = settings.AUTH_MANAGER_API_KEY
        self.timeout = 10.0
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Faz uma requisição para o MS-AuthManager"""
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
            "X-Service": "CryptVault"
        }
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=data,
                    params=params,
                    headers=headers
                )
                
                if response.status_code >= 400:
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get("detail", error_detail)
                    except:
                        pass
                    
                    logger.error(
                        "Auth service request failed",
                        method=method,
                        url=url,
                        status_code=response.status_code,
                        error=error_detail
                    )
                    raise AuthServiceError(f"Auth service error: {error_detail}")
                
                return response.json()
                
        except httpx.TimeoutException:
            logger.error("Auth service timeout", method=method, url=url)
            raise AuthServiceError("Auth service timeout")
        except httpx.RequestError as e:
            logger.error("Auth service request error", method=method, url=url, error=str(e))
            raise AuthServiceError(f"Auth service connection error: {str(e)}")
    
    async def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Valida um token JWT com o AuthManager
        
        Returns:
            {
                "user_id": "uuid",
                "company_id": "uuid", 
                "roles": ["role1", "role2"],
                "permissions": ["perm1", "perm2"],
                "expires_at": "2024-01-01T00:00:00Z"
            }
        """
        result = await self._make_request("POST", "/v1/validate-token", token=token)
        return result
    
    async def get_user_info(self, user_id: str, token: str) -> Dict[str, Any]:
        """Obtém informações do usuário"""
        result = await self._make_request(
            "GET", 
            f"/v1/users/{user_id}",
            token=token
        )
        return result
    
    async def get_user_permissions(
        self, 
        user_id: str, 
        resource: str,
        token: str
    ) -> List[str]:
        """Obtém permissões do usuário para um recurso específico"""
        params = {"resource": resource}
        result = await self._make_request(
            "GET",
            f"/v1/users/{user_id}/permissions",
            params=params,
            token=token
        )
        return result.get("permissions", [])
    
    async def check_permission(
        self,
        user_id: str,
        permission: str,
        resource_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> bool:
        """Verifica se usuário tem uma permissão específica"""
        data = {
            "permission": permission,
            "resource_id": resource_id
        }
        
        result = await self._make_request(
            "POST",
            f"/v1/users/{user_id}/check-permission",
            data=data,
            token=token
        )
        return result.get("has_permission", False)
    
    async def get_company_users(
        self, 
        company_id: str, 
        token: str
    ) -> List[Dict[str, Any]]:
        """Lista usuários de uma empresa"""
        result = await self._make_request(
            "GET",
            f"/v1/companies/{company_id}/users",
            token=token
        )
        return result.get("users", [])
    
    async def create_audit_log(
        self,
        user_id: str,
        action: str,
        resource: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> bool:
        """Cria log de auditoria no AuthManager"""
        data = {
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "details": details,
            "ip_address": ip_address,
            "service": "CryptVault",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self._make_request("POST", "/v1/audit-logs", data=data)
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do MS-AuthManager"""
        try:
            result = await self._make_request("GET", "/health")
            return {
                "status": "healthy",
                "service": result.get("service", "auth-manager"),
                "version": result.get("version", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy", 
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class AuthService:
    """Service layer para operações de autenticação"""
    
    def __init__(self):
        self.client = AuthManagerClient()
    
    async def authenticate_user(self, token: str) -> Dict[str, Any]:
        """Autentica usuário via token"""
        try:
            user_data = await self.client.validate_token(token)
            
            logger.info(
                "User authenticated successfully",
                user_id=user_data.get("user_id"),
                company_id=user_data.get("company_id")
            )
            
            return user_data
            
        except AuthServiceError as e:
            logger.warning("Authentication failed", error=str(e))
            raise
    
    async def check_secret_permission(
        self,
        user_id: str,
        action: str,
        secret_id: Optional[str] = None,
        token: Optional[str] = None
    ) -> bool:
        """Verifica permissão específica para secrets"""
        permission = f"secret:{action}"
        
        return await self.client.check_permission(
            user_id=user_id,
            permission=permission,
            resource_id=secret_id,
            token=token
        )
    
    async def log_user_action(
        self,
        user_id: str,
        action: str,
        resource_id: str,
        details: Dict[str, Any],
        ip_address: Optional[str] = None
    ) -> None:
        """Registra ação do usuário no sistema de auditoria"""
        await self.client.create_audit_log(
            user_id=user_id,
            action=action,
            resource=f"secret:{resource_id}",
            details=details,
            ip_address=ip_address
        )


# Instância global do serviço
auth_service = AuthService()

