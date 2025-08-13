"""
Testes para a aplicação principal
"""
import pytest
from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Testa endpoint raiz"""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert "CryptVault" in data["message"]


def test_health_endpoint(client: TestClient):
    """Testa endpoint de health check"""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_status_endpoint(client: TestClient):
    """Testa endpoint de status"""
    response = client.get("/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "environment" in data
    assert "external_services" in data


def test_cors_headers(client: TestClient):
    """Testa headers CORS"""
    response = client.options("/health")
    assert response.status_code == 200


def test_api_version_header(client: TestClient):
    """Testa header de versão da API"""
    response = client.get("/health")
    assert "X-API-Version" in response.headers

