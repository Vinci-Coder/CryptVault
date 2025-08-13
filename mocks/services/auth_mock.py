"""
Mock do MS-AuthManager para desenvolvimento e testes
"""
from fastapi import FastAPI, HTTPException, Header
from typing import Optional
import uuid

app = FastAPI(title="AuthManager Mock", version="1.0.0-mock")

# Dados mock para multi-tenant
MOCK_COMPANIES = {
    "550e8400-e29b-41d4-a716-446655440001": {
        "id": "550e8400-e29b-41d4-a716-446655440001",
        "name": "Vinci Code",
        "slug": "vinci-code",
        "type": "agency",
        "status": "active"
    },
    "550e8400-e29b-41d4-a716-446655440003": {
        "id": "550e8400-e29b-41d4-a716-446655440003", 
        "name": "Startup ABC",
        "slug": "startup-abc",
        "type": "startup",
        "status": "trial"
    }
}

MOCK_USERS = {
    "550e8400-e29b-41d4-a716-446655440000": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "admin@vincicode.com",
        "name": "João Silva",
        "full_name": "João Silva",
        "username": "joao.silva",
        "title": "CTO",
        "is_active": True,
        "is_system_admin": True,
        "companies": [
            {
                "company_id": "550e8400-e29b-41d4-a716-446655440001",
                "company_name": "Vinci Code",
                "company_slug": "vinci-code",
                "role": "company_admin",
                "is_primary": True,
                "permissions": [
                    "company:admin", "project:admin", "secret:admin",
                    "user:admin", "audit:admin", "security:admin"
                ]
            }
        ]
    },
    "550e8400-e29b-41d4-a716-446655440002": {
        "id": "550e8400-e29b-41d4-a716-446655440002",
        "email": "dev@vincicode.com",
        "name": "Maria Santos",
        "full_name": "Maria Santos",
        "username": "maria.santos",
        "title": "Full Stack Developer",
        "is_active": True,
        "is_system_admin": False,
        "companies": [
            {
                "company_id": "550e8400-e29b-41d4-a716-446655440001",
                "company_name": "Vinci Code",
                "company_slug": "vinci-code",
                "role": "developer",
                "is_primary": True,
                "permissions": [
                    "secret:read", "secret:create", "secret:update",
                    "project:read", "audit:read"
                ]
            },
            {
                "company_id": "550e8400-e29b-41d4-a716-446655440003",
                "company_name": "Startup ABC",
                "company_slug": "startup-abc",
                "role": "project_manager",
                "is_primary": False,
                "permissions": [
                    "secret:read", "secret:create", "secret:update", "secret:share",
                    "project:admin", "user:read", "audit:read"
                ]
            }
        ]
    },
    "550e8400-e29b-41d4-a716-446655440004": {
        "id": "550e8400-e29b-41d4-a716-446655440004",
        "email": "viewer@test.com",
        "name": "Pedro Viewer",
        "full_name": "Pedro Viewer",
        "username": "pedro.viewer",
        "title": "Auditor",
        "is_active": True,
        "is_system_admin": False,
        "companies": [
            {
                "company_id": "550e8400-e29b-41d4-a716-446655440001",
                "company_name": "Vinci Code",
                "company_slug": "vinci-code",
                "role": "viewer",
                "is_primary": True,
                "permissions": [
                    "secret:read", "audit:read"
                ]
            }
        ]
    }
}

@app.get("/health")
async def health():
    return {
        "status": "healthy", 
        "service": "auth-manager-mock", 
        "version": "1.0.0-mock"
    }

@app.post("/v1/validate-token")
async def validate_token(authorization: Optional[str] = Header(None)):
    """Valida token JWT mock"""
    
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid token format")
    
    token = authorization.replace("Bearer ", "")
    
    # Tokens mock específicos para multi-tenant
    if token == "admin-token":
        user_id = "550e8400-e29b-41d4-a716-446655440000"
    elif token == "dev-token":
        user_id = "550e8400-e29b-41d4-a716-446655440002" 
    elif token == "viewer-token":
        user_id = "550e8400-e29b-41d4-a716-446655440004"
    else:
        # Para qualquer outro token, retorna admin por padrão
        user_id = "550e8400-e29b-41d4-a716-446655440000"
    
    user = MOCK_USERS[user_id]
    
    # Pega empresa primária
    primary_company = next(
        (c for c in user["companies"] if c["is_primary"]), 
        user["companies"][0] if user["companies"] else None
    )
    
    # Agrega todas as permissões de todas as empresas
    all_permissions = set()
    all_roles = set()
    
    for company in user["companies"]:
        all_permissions.update(company["permissions"])
        all_roles.add(company["role"])
    
    return {
        "user_id": user["id"],
        "company_id": primary_company["company_id"] if primary_company else None,
        "email": user["email"],
        "name": user["name"],
        "full_name": user["full_name"],
        "username": user["username"],
        "title": user.get("title"),
        "company_name": primary_company["company_name"] if primary_company else None,
        "roles": list(all_roles),
        "permissions": list(all_permissions),
        "is_active": user["is_active"],
        "is_system_admin": user.get("is_system_admin", False),
        "companies": user["companies"],
        "expires_at": "2024-12-31T23:59:59Z"
    }

@app.get("/v1/users/{user_id}")
async def get_user_info(user_id: str, authorization: Optional[str] = Header(None)):
    """Obtém informações do usuário"""
    
    if user_id not in MOCK_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    return MOCK_USERS[user_id]

@app.get("/v1/users/{user_id}/permissions")
async def get_user_permissions(
    user_id: str, 
    resource: Optional[str] = None,
    authorization: Optional[str] = Header(None)
):
    """Obtém permissões do usuário para um recurso"""
    
    if user_id not in MOCK_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = MOCK_USERS[user_id]
    permissions = user["permissions"]
    
    # Filtrar por recurso se especificado
    if resource:
        permissions = [p for p in permissions if p.startswith(resource)]
    
    return {"permissions": permissions}

@app.post("/v1/users/{user_id}/check-permission")
async def check_permission(
    user_id: str,
    request: dict,
    authorization: Optional[str] = Header(None)
):
    """Verifica se usuário tem uma permissão específica"""
    
    if user_id not in MOCK_USERS:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = MOCK_USERS[user_id]
    permission = request.get("permission")
    
    if not permission:
        raise HTTPException(status_code=400, detail="Permission required")
    
    has_permission = permission in user["permissions"]
    
    return {"has_permission": has_permission}

@app.get("/v1/companies/{company_id}/users")
async def get_company_users(
    company_id: str,
    authorization: Optional[str] = Header(None)
):
    """Lista usuários de uma empresa"""
    
    users = [user for user in MOCK_USERS.values() if user["company_id"] == company_id]
    
    return {"users": users}

@app.post("/v1/audit-logs")
async def create_audit_log(request: dict):
    """Cria log de auditoria"""
    
    print(f"[AUDIT MOCK] {request}")
    
    return {"success": True, "log_id": str(uuid.uuid4())}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
