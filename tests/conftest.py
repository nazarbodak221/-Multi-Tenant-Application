"""
Test configuration and fixtures
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient
from tortoise import Tortoise
from app.main import app
from app.core.database import db_manager
from app.models.core import User, Organization
from app.models.tenant import TenantUser
from app.core.security import hash_password, create_core_token, create_tenant_token
import asyncpg


# Test database configuration
TEST_CORE_DB_URL = "postgres://postgres:postgres@localhost:5432/test_core"
TEST_TENANT_DB_URL_TEMPLATE = "postgres://postgres:postgres@localhost:5432/test_tenant_{}"

# Override settings for tests
import os
# Set environment variables before importing settings
os.environ.setdefault("CORE_DB_HOST", "localhost")
os.environ.setdefault("CORE_DB_PORT", "5432")
os.environ.setdefault("CORE_DB_NAME", "test_core")
os.environ.setdefault("CORE_DB_USER", "postgres")
os.environ.setdefault("CORE_DB_PASSWORD", "postgres")
os.environ.setdefault("TENANT_DB_HOST", "localhost")
os.environ.setdefault("TENANT_DB_PORT", "5432")
os.environ.setdefault("TENANT_DB_USER", "postgres")
os.environ.setdefault("TENANT_DB_PASSWORD", "postgres")
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "30")

# Clear settings cache to reload with test values
from app.config import get_settings
get_settings.cache_clear()
settings = get_settings()


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def core_db() -> AsyncGenerator:
    """
    Setup and teardown test core database
    Creates fresh database for each test
    """
    # Create test database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    
    # Drop test database if exists
    await conn.execute("DROP DATABASE IF EXISTS test_core")
    await conn.execute("CREATE DATABASE test_core")
    await conn.close()
    
    # Initialize core DB through db_manager
    await db_manager.init_core_db()
    
    yield
    
    # Cleanup
    await db_manager.close_all()
    
    # Drop test database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    await conn.execute("DROP DATABASE IF EXISTS test_core")
    await conn.close()


@pytest.fixture(scope="function")
async def tenant_db(core_db) -> AsyncGenerator:
    """
    Setup and teardown test tenant database
    Creates fresh tenant database for each test
    Requires core_db to be initialized first
    """
    tenant_id = "test_tenant_123"
    db_name = f"test_tenant_{tenant_id}"
    
    # Create test tenant database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    
    # Drop test database if exists
    await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    await conn.execute(f'CREATE DATABASE "{db_name}"')
    await conn.close()
    
    # Initialize tenant DB through db_manager
    await db_manager.init_tenant_db(tenant_id)
    
    yield tenant_id
    
    # Cleanup
    await db_manager.close_all()
    
    # Drop test database
    conn = await asyncpg.connect(
        host="localhost",
        port=5432,
        user="postgres",
        password="postgres",
        database="postgres"
    )
    await conn.execute(f'DROP DATABASE IF EXISTS "{db_name}"')
    await conn.close()


@pytest.fixture
async def core_user(core_db) -> User:
    """Create a test core user"""
    user = await User.create(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Test User",
        is_active=True
    )
    return user


@pytest.fixture
async def core_user_token(core_user) -> str:
    """Create JWT token for core user"""
    return create_core_token(user_id=core_user.id, email=core_user.email)


@pytest.fixture
async def tenant_user(tenant_db) -> TenantUser:
    """Create a test tenant user"""
    tenant_id = tenant_db
    tenant_url = TEST_TENANT_DB_URL_TEMPLATE.format(tenant_id)
    
    # Initialize tenant connection
    await db_manager.init_tenant_db(tenant_id)
    
    # Get tenant model
    TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
    
    user = await TenantUserModel.create(
        email="tenant@example.com",
        hashed_password=hash_password("testpass123"),
        full_name="Tenant User",
        is_active=True,
        is_owner=False
    )
    return user


@pytest.fixture
async def tenant_user_token(tenant_user, tenant_db) -> tuple[str, str]:
    """Create JWT token for tenant user"""
    tenant_id = tenant_db
    token = create_tenant_token(
        user_id=tenant_user.id,
        email=tenant_user.email,
        tenant_id=tenant_id
    )
    return token, tenant_id


@pytest.fixture
async def organization(core_user, core_db) -> Organization:
    """Create a test organization"""
    org = await Organization.create(
        name="Test Organization",
        slug="test-org",
        database_name="test_tenant_org123",
        owner_id=core_user.id,
        is_active=True
    )
    return org


@pytest.fixture
async def test_client() -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def authenticated_core_client(core_user_token, test_client) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated HTTP client for core user"""
    test_client.headers.update({"Authorization": f"Bearer {core_user_token}"})
    yield test_client


@pytest.fixture
async def authenticated_tenant_client(tenant_user_token, test_client) -> AsyncGenerator[AsyncClient, None]:
    """Create authenticated HTTP client for tenant user"""
    token, tenant_id = tenant_user_token
    test_client.headers.update({
        "Authorization": f"Bearer {token}",
        "X-Tenant-Id": tenant_id
    })
    yield test_client

