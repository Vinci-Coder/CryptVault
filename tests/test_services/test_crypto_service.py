"""
Testes para o serviço de criptografia
"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.crypto_service import CryptoService, CryptoServiceError


@pytest.fixture
def crypto_service():
    """Fixture para o serviço de criptografia"""
    return CryptoService()


@pytest.mark.asyncio
async def test_encrypt_secret_success(crypto_service: CryptoService):
    """Testa criptografia bem-sucedida"""
    
    mock_response = {
        "encrypted_id": "test-encrypted-id",
        "checksum": "test-checksum",
        "size": 100,
        "encrypted_at": "2024-01-01T00:00:00Z"
    }
    
    with patch.object(crypto_service.client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = mock_response
        
        result = await crypto_service.encrypt_secret(
            content="test secret",
            secret_type="text",
            metadata={"test": "data"}
        )
        
        assert result == mock_response
        mock_request.assert_called_once()


@pytest.mark.asyncio
async def test_decrypt_secret_success(crypto_service: CryptoService):
    """Testa descriptografia bem-sucedida"""
    
    with patch.object(crypto_service.client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"data": "decrypted content"}
        
        result = await crypto_service.decrypt_secret("test-encrypted-id")
        
        assert result == "decrypted content"
        mock_request.assert_called_once_with("GET", "/v1/decrypt/test-encrypted-id")


@pytest.mark.asyncio
async def test_verify_secret_integrity_success(crypto_service: CryptoService):
    """Testa verificação de integridade"""
    
    with patch.object(crypto_service.client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {"is_valid": True}
        
        result = await crypto_service.verify_secret_integrity("test-encrypted-id")
        
        assert result is True
        mock_request.assert_called_once_with("GET", "/v1/verify/test-encrypted-id")


@pytest.mark.asyncio
async def test_cleanup_encrypted_data_success(crypto_service: CryptoService):
    """Testa limpeza de dados criptografados"""
    
    with patch.object(crypto_service.client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.return_value = {}
        
        result = await crypto_service.cleanup_encrypted_data("test-encrypted-id")
        
        assert result is True
        mock_request.assert_called_once_with("DELETE", "/v1/encrypted/test-encrypted-id")


@pytest.mark.asyncio
async def test_crypto_service_error():
    """Testa tratamento de erros do serviço"""
    
    service = CryptoService()
    
    with patch.object(service.client, '_make_request', new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = CryptoServiceError("Service unavailable")
        
        with pytest.raises(CryptoServiceError):
            await service.encrypt_secret("test", "text")

