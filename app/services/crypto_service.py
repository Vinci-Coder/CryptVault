"""
Interface para o microserviço de criptografia em GO
"""
import httpx
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CryptoServiceError(Exception):
    """Exceção para erros do serviço de criptografia"""
    pass


class CryptoServiceClient:
    """Cliente para comunicação com o microserviço de criptografia"""
    
    def __init__(self):
        self.base_url = settings.CRYPTO_SERVICE_URL
        self.api_key = settings.CRYPTO_SERVICE_API_KEY
        self.timeout = 30.0
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Faz uma requisição para o serviço de criptografia"""
        
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Service": "CryptVault-Core"
        }
        
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
                        "Crypto service request failed",
                        method=method,
                        url=url,
                        status_code=response.status_code,
                        error=error_detail
                    )
                    raise CryptoServiceError(f"Crypto service error: {error_detail}")
                
                return response.json()
                
        except httpx.TimeoutException:
            logger.error("Crypto service timeout", method=method, url=url)
            raise CryptoServiceError("Crypto service timeout")
        except httpx.RequestError as e:
            logger.error("Crypto service request error", method=method, url=url, error=str(e))
            raise CryptoServiceError(f"Crypto service connection error: {str(e)}")
    
    async def encrypt_data(
        self,
        data: str,
        data_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Criptografa dados usando AES-256
        
        Returns:
            {
                "encrypted_id": "uuid",
                "checksum": "sha256_hash",
                "size": 1024,
                "encrypted_at": "2024-01-01T00:00:00Z"
            }
        """
        request_data = {
            "data": data,
            "data_type": data_type,
            "metadata": metadata or {},
            "algorithm": "AES-256-GCM"
        }
        
        logger.info("Encrypting data", data_type=data_type, size=len(data))
        
        result = await self._make_request("POST", "/v1/encrypt", data=request_data)
        
        logger.info("Data encrypted successfully", encrypted_id=result.get("encrypted_id"))
        return result
    
    async def decrypt_data(self, encrypted_id: str) -> Dict[str, Any]:
        """
        Descriptografa dados pelo ID
        
        Returns:
            {
                "data": "decrypted_content",
                "data_type": "text",
                "metadata": {},
                "checksum": "sha256_hash",
                "encrypted_at": "2024-01-01T00:00:00Z"
            }
        """
        logger.info("Decrypting data", encrypted_id=encrypted_id)
        
        result = await self._make_request("GET", f"/v1/decrypt/{encrypted_id}")
        
        logger.info("Data decrypted successfully", encrypted_id=encrypted_id)
        return result
    
    async def delete_encrypted_data(self, encrypted_id: str) -> bool:
        """Remove dados criptografados"""
        logger.info("Deleting encrypted data", encrypted_id=encrypted_id)
        
        await self._make_request("DELETE", f"/v1/encrypted/{encrypted_id}")
        
        logger.info("Encrypted data deleted", encrypted_id=encrypted_id)
        return True
    
    async def reencrypt_data(
        self,
        encrypted_id: str,
        new_algorithm: Optional[str] = None
    ) -> Dict[str, Any]:
        """Re-criptografa dados com novo algoritmo ou chave"""
        request_data = {}
        if new_algorithm:
            request_data["algorithm"] = new_algorithm
        
        logger.info("Re-encrypting data", encrypted_id=encrypted_id)
        
        result = await self._make_request(
            "POST", 
            f"/v1/reencrypt/{encrypted_id}", 
            data=request_data
        )
        
        logger.info("Data re-encrypted successfully", 
                   old_id=encrypted_id, 
                   new_id=result.get("encrypted_id"))
        return result
    
    async def verify_integrity(self, encrypted_id: str) -> Dict[str, Any]:
        """Verifica integridade dos dados criptografados"""
        logger.info("Verifying data integrity", encrypted_id=encrypted_id)
        
        result = await self._make_request("GET", f"/v1/verify/{encrypted_id}")
        
        logger.info("Integrity verification completed", 
                   encrypted_id=encrypted_id,
                   is_valid=result.get("is_valid"))
        return result
    
    async def get_encrypted_metadata(self, encrypted_id: str) -> Dict[str, Any]:
        """Obtém metadados dos dados criptografados sem descriptografar"""
        result = await self._make_request("GET", f"/v1/metadata/{encrypted_id}")
        return result
    
    async def bulk_encrypt(
        self, 
        data_list: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Criptografia em lote para múltiplos dados"""
        request_data = {"data_list": data_list}
        
        logger.info("Bulk encrypting data", count=len(data_list))
        
        result = await self._make_request("POST", "/v1/encrypt/bulk", data=request_data)
        
        logger.info("Bulk encryption completed", count=len(result.get("results", [])))
        return result.get("results", [])
    
    async def health_check(self) -> Dict[str, Any]:
        """Verifica saúde do serviço de criptografia"""
        try:
            result = await self._make_request("GET", "/health")
            return {
                "status": "healthy",
                "service": result.get("service", "crypto-service"),
                "version": result.get("version", "unknown"),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


class CryptoService:
    """Service layer para operações de criptografia"""
    
    def __init__(self):
        self.client = CryptoServiceClient()
    
    async def encrypt_secret(
        self,
        content: str,
        secret_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Criptografa conteúdo de um secret"""
        enhanced_metadata = {
            "secret_type": secret_type,
            "content_length": len(content),
            "encrypted_by": "cryptvault-core",
            **(metadata or {})
        }
        
        return await self.client.encrypt_data(
            data=content,
            data_type=secret_type,
            metadata=enhanced_metadata
        )
    
    async def decrypt_secret(self, encrypted_id: str) -> str:
        """Descriptografa conteúdo de um secret"""
        result = await self.client.decrypt_data(encrypted_id)
        return result["data"]
    
    async def verify_secret_integrity(self, encrypted_id: str) -> bool:
        """Verifica integridade de um secret"""
        result = await self.client.verify_integrity(encrypted_id)
        return result.get("is_valid", False)
    
    async def cleanup_encrypted_data(self, encrypted_id: str) -> bool:
        """Remove dados criptografados do serviço"""
        return await self.client.delete_encrypted_data(encrypted_id)


# Instância global do serviço
crypto_service = CryptoService()

