"""
Mock do Crypto Service para desenvolvimento e testes
"""
from fastapi import FastAPI, HTTPException, Header
from typing import Optional, Dict, Any
import uuid
import hashlib
import base64
import json
from datetime import datetime

app = FastAPI(title="Crypto Service Mock", version="1.0.0-mock")

# Storage em memória para dados "criptografados"
encrypted_storage: Dict[str, Dict[str, Any]] = {}

def mock_encrypt(data: str) -> str:
    """Criptografia mock usando base64"""
    return base64.b64encode(data.encode()).decode()

def mock_decrypt(encrypted_data: str) -> str:
    """Descriptografia mock"""
    try:
        return base64.b64decode(encrypted_data).decode()
    except:
        raise ValueError("Invalid encrypted data")

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "crypto-service-mock",
        "version": "1.0.0-mock"
    }

@app.post("/v1/encrypt")
async def encrypt_data(
    request: dict,
    authorization: Optional[str] = Header(None)
):
    """Criptografa dados"""
    
    data = request.get("data")
    data_type = request.get("data_type", "text")
    metadata = request.get("metadata", {})
    algorithm = request.get("algorithm", "AES-256-GCM")
    
    if not data:
        raise HTTPException(status_code=400, detail="Data is required")
    
    encrypted_id = str(uuid.uuid4())
    encrypted_content = mock_encrypt(data)
    checksum = hashlib.sha256(data.encode()).hexdigest()
    size = len(data)
    
    # Armazena dados "criptografados"
    encrypted_storage[encrypted_id] = {
        "encrypted_content": encrypted_content,
        "data_type": data_type,
        "metadata": metadata,
        "algorithm": algorithm,
        "checksum": checksum,
        "size": size,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    print(f"[CRYPTO MOCK] Encrypted data: {encrypted_id} (size: {size} bytes)")
    
    return {
        "encrypted_id": encrypted_id,
        "checksum": checksum,
        "size": size,
        "encrypted_at": encrypted_storage[encrypted_id]["created_at"]
    }

@app.get("/v1/decrypt/{encrypted_id}")
async def decrypt_data(
    encrypted_id: str,
    authorization: Optional[str] = Header(None)
):
    """Descriptografa dados"""
    
    if encrypted_id not in encrypted_storage:
        raise HTTPException(status_code=404, detail="Encrypted data not found")
    
    stored_data = encrypted_storage[encrypted_id]
    
    try:
        decrypted_content = mock_decrypt(stored_data["encrypted_content"])
        
        print(f"[CRYPTO MOCK] Decrypted data: {encrypted_id}")
        
        return {
            "data": decrypted_content,
            "data_type": stored_data["data_type"],
            "metadata": stored_data["metadata"],
            "checksum": stored_data["checksum"],
            "encrypted_at": stored_data["created_at"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")

@app.delete("/v1/encrypted/{encrypted_id}")
async def delete_encrypted_data(
    encrypted_id: str,
    authorization: Optional[str] = Header(None)
):
    """Remove dados criptografados"""
    
    if encrypted_id in encrypted_storage:
        del encrypted_storage[encrypted_id]
        print(f"[CRYPTO MOCK] Deleted encrypted data: {encrypted_id}")
    
    return {"success": True}

@app.post("/v1/reencrypt/{encrypted_id}")
async def reencrypt_data(
    encrypted_id: str,
    request: dict = {},
    authorization: Optional[str] = Header(None)
):
    """Re-criptografa dados com novo algoritmo"""
    
    if encrypted_id not in encrypted_storage:
        raise HTTPException(status_code=404, detail="Encrypted data not found")
    
    stored_data = encrypted_storage[encrypted_id]
    
    # Descriptografa dados existentes
    original_data = mock_decrypt(stored_data["encrypted_content"])
    
    # Cria nova entrada criptografada
    new_encrypted_id = str(uuid.uuid4())
    new_encrypted_content = mock_encrypt(original_data)
    new_algorithm = request.get("algorithm", "AES-256-GCM")
    
    encrypted_storage[new_encrypted_id] = {
        **stored_data,
        "encrypted_content": new_encrypted_content,
        "algorithm": new_algorithm,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    print(f"[CRYPTO MOCK] Re-encrypted {encrypted_id} -> {new_encrypted_id}")
    
    return {
        "encrypted_id": new_encrypted_id,
        "checksum": stored_data["checksum"],
        "size": stored_data["size"],
        "encrypted_at": encrypted_storage[new_encrypted_id]["created_at"]
    }

@app.get("/v1/verify/{encrypted_id}")
async def verify_integrity(
    encrypted_id: str,
    authorization: Optional[str] = Header(None)
):
    """Verifica integridade dos dados criptografados"""
    
    if encrypted_id not in encrypted_storage:
        raise HTTPException(status_code=404, detail="Encrypted data not found")
    
    stored_data = encrypted_storage[encrypted_id]
    
    try:
        # Tenta descriptografar para verificar integridade
        decrypted_content = mock_decrypt(stored_data["encrypted_content"])
        current_checksum = hashlib.sha256(decrypted_content.encode()).hexdigest()
        
        is_valid = current_checksum == stored_data["checksum"]
        
        print(f"[CRYPTO MOCK] Integrity check for {encrypted_id}: {'VALID' if is_valid else 'INVALID'}")
        
        return {
            "is_valid": is_valid,
            "encrypted_id": encrypted_id,
            "checksum": stored_data["checksum"],
            "current_checksum": current_checksum
        }
        
    except Exception as e:
        return {
            "is_valid": False,
            "encrypted_id": encrypted_id,
            "error": str(e)
        }

@app.get("/v1/metadata/{encrypted_id}")
async def get_encrypted_metadata(
    encrypted_id: str,
    authorization: Optional[str] = Header(None)
):
    """Obtém metadados sem descriptografar"""
    
    if encrypted_id not in encrypted_storage:
        raise HTTPException(status_code=404, detail="Encrypted data not found")
    
    stored_data = encrypted_storage[encrypted_id]
    
    return {
        "encrypted_id": encrypted_id,
        "data_type": stored_data["data_type"],
        "metadata": stored_data["metadata"],
        "algorithm": stored_data["algorithm"],
        "size": stored_data["size"],
        "checksum": stored_data["checksum"],
        "encrypted_at": stored_data["created_at"]
    }

@app.post("/v1/encrypt/bulk")
async def bulk_encrypt(
    request: dict,
    authorization: Optional[str] = Header(None)
):
    """Criptografia em lote"""
    
    data_list = request.get("data_list", [])
    
    if not data_list:
        raise HTTPException(status_code=400, detail="data_list is required")
    
    results = []
    
    for item in data_list:
        try:
            # Simula chamada individual de encrypt
            encrypted_result = await encrypt_data(item)
            results.append({
                "success": True,
                **encrypted_result
            })
        except Exception as e:
            results.append({
                "success": False,
                "error": str(e)
            })
    
    print(f"[CRYPTO MOCK] Bulk encrypted {len(data_list)} items")
    
    return {"results": results}

@app.get("/v1/stats")
async def get_stats():
    """Estatísticas do serviço mock"""
    return {
        "total_encrypted": len(encrypted_storage),
        "service_uptime": "mock",
        "algorithms_supported": ["AES-256-GCM", "AES-256-CBC"],
        "memory_usage": f"{len(str(encrypted_storage))} bytes"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

