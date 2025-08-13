"""
Schemas para autenticação
"""
from typing import List, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime


class TokenData(BaseModel):
    """Dados decodificados do token"""
    user_id: UUID4
    company_id: UUID4
    roles: List[str]
    permissions: List[str]
    expires_at: datetime


class CurrentUser(BaseModel):
    """Informações do usuário atual"""
    id: UUID4
    email: str
    name: str
    company_id: UUID4
    company_name: str
    roles: List[str]
    permissions: List[str]
    is_active: bool = True
    
    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    """Resposta de autenticação"""
    authenticated: bool
    user: Optional[CurrentUser] = None
    error: Optional[str] = None

