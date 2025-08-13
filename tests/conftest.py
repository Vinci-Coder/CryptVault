"""
Configuração de testes pytest
"""
import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
import uuid

from app.main import app
from app.models.base import Base
from app.api.deps import get_db
from app.schemas.auth import CurrentUser


# Database de teste
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Engine de teste
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True,
)

# Session de teste
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop():
    """Cria um event loop para toda a sessão de testes"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Fixture para sessão de banco de dados de teste"""
    
    # Cria tabelas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Sessão de teste
    async with test_session_maker() as session:
        yield session
    
    # Limpa tabelas
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def mock_current_user() -> CurrentUser:
    """Fixture para usuário mock"""
    return CurrentUser(
        id=uuid.uuid4(),
        email="test@example.com",
        name="Test User",
        company_id=uuid.uuid4(),
        company_name="Test Company",
        roles=["user"],
        permissions=["secret:read", "secret:create", "secret:update", "secret:delete"],
        is_active=True
    )


@pytest.fixture
def mock_admin_user() -> CurrentUser:
    """Fixture para usuário admin mock"""
    return CurrentUser(
        id=uuid.uuid4(),
        email="admin@example.com",
        name="Admin User",
        company_id=uuid.uuid4(),
        company_name="Test Company",
        roles=["admin"],
        permissions=[
            "secret:read", "secret:create", "secret:update", "secret:delete",
            "audit:read", "audit:admin", "security:read", "security:manage"
        ],
        is_active=True
    )


@pytest.fixture
def client(db_session: AsyncSession, mock_current_user: CurrentUser):
    """Fixture para cliente de teste"""
    
    # Override da dependência do banco
    async def get_test_db():
        yield db_session
    
    # Override da dependência do usuário
    async def get_test_user():
        return mock_current_user
    
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_current_active_user] = get_test_user
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpa overrides
    app.dependency_overrides.clear()


@pytest.fixture
def admin_client(db_session: AsyncSession, mock_admin_user: CurrentUser):
    """Fixture para cliente admin de teste"""
    
    # Override da dependência do banco
    async def get_test_db():
        yield db_session
    
    # Override da dependência do usuário
    async def get_test_admin():
        return mock_admin_user
    
    from app.api.deps import get_current_active_user
    app.dependency_overrides[get_db] = get_test_db
    app.dependency_overrides[get_current_active_user] = get_test_admin
    
    with TestClient(app) as test_client:
        yield test_client
    
    # Limpa overrides
    app.dependency_overrides.clear()

