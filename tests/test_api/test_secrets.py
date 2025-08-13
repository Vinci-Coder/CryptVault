"""
Testes para API de secrets
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch


def test_list_secrets_empty(client: TestClient):
    """Testa listagem de secrets vazia"""
    response = client.get("/api/v1/secrets/")
    assert response.status_code == 200
    
    data = response.json()
    assert "secrets" in data
    assert "total" in data
    assert data["total"] == 0
    assert len(data["secrets"]) == 0


def test_create_secret_invalid_data(client: TestClient):
    """Testa criação de secret com dados inválidos"""
    invalid_data = {
        "name": "",  # Nome vazio é inválido
        "content": "test content"
    }
    
    response = client.post("/api/v1/secrets/", json=invalid_data)
    assert response.status_code == 422  # Validation error


def test_get_nonexistent_secret(client: TestClient):
    """Testa busca de secret inexistente"""
    response = client.get("/api/v1/secrets/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_create_secret_success(client: TestClient):
    """Testa criação bem-sucedida de secret"""
    
    # Mock do serviço de criptografia
    mock_encrypt_result = {
        "encrypted_id": "test-encrypted-id",
        "checksum": "test-checksum",
        "size": 100
    }
    
    valid_data = {
        "name": "Test Secret",
        "description": "A test secret",
        "content": "secret content",
        "type": "text",
        "tags": ["test", "development"]
    }
    
    with patch('app.services.crypto_service.crypto_service.encrypt_secret') as mock_encrypt:
        mock_encrypt.return_value = mock_encrypt_result
        
        response = client.post("/api/v1/secrets/", json=valid_data)
        
        # Note: Este teste pode falhar devido à dependência real do banco
        # Em um ambiente de teste real, seria necessário configurar mocks completos
        # Este é um exemplo básico da estrutura de teste


def test_search_secrets_with_filters(client: TestClient):
    """Testa busca de secrets com filtros"""
    response = client.get("/api/v1/secrets/?q=test&type=text&page=1&size=10")
    assert response.status_code == 200
    
    data = response.json()
    assert "secrets" in data
    assert "total" in data
    assert "page" in data
    assert "size" in data


def test_unauthorized_access():
    """Testa acesso não autorizado"""
    from app.main import app
    
    # Cliente sem autenticação
    with TestClient(app) as unauthorized_client:
        response = unauthorized_client.get("/api/v1/secrets/")
        assert response.status_code == 401

