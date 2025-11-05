from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.api.v1.users import get_current_user_tenant
from app.core.database import db_manager
from app.main import app
from app.services.auth_service import auth_service
from app.services.user_service import user_service


@pytest.fixture(autouse=True)
def _patch_db_manager(monkeypatch):
    async def _async_noop(*args, **kwargs):
        return None

    monkeypatch.setattr(db_manager, "init_core_db", _async_noop)
    monkeypatch.setattr(db_manager, "close_all", _async_noop)
    monkeypatch.setattr(db_manager, "init_tenant_db", _async_noop)
    yield


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_register_core_user(client, monkeypatch):
    async def fake_register_core_user(email, password, full_name=None):
        return {
            "user": {
                "id": "core-user",
                "email": email,
                "full_name": full_name,
                "is_active": True,
            },
            "access_token": "token-core",
            "token_type": "bearer",
            "scope": "core",
        }

    monkeypatch.setattr(auth_service, "register_core_user", fake_register_core_user)

    response = client.post(
        "/api/v1/auth/register",
        json={"email": "user@example.com", "password": "secret", "full_name": "User"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["scope"] == "core"
    assert payload["user"]["email"] == "user@example.com"


def test_register_tenant_user(client, monkeypatch):
    async def fake_register_tenant_user(tenant_id, email, password, full_name=None):
        return {
            "user": {
                "id": "tenant-user",
                "email": email,
                "full_name": full_name,
                "is_active": True,
                "is_owner": False,
            },
            "access_token": "token-tenant",
            "token_type": "bearer",
            "scope": "tenant",
            "tenant_id": tenant_id,
        }

    monkeypatch.setattr(auth_service, "register_tenant_user", fake_register_tenant_user)

    response = client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-Id": "tenant-123"},
        json={"email": "tenant@example.com", "password": "secret", "full_name": "Tenant"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["tenant_id"] == "tenant-123"
    assert payload["scope"] == "tenant"


def test_login_core_user(client, monkeypatch):
    async def fake_login_core_user(email, password):
        return {
            "user": {
                "id": "core-user",
                "email": email,
                "full_name": "User",
                "is_active": True,
            },
            "access_token": "token-core",
            "token_type": "bearer",
            "scope": "core",
        }

    monkeypatch.setattr(auth_service, "login_core_user", fake_login_core_user)

    response = client.post(
        "/api/v1/auth/login",
        json={"email": "user@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    assert response.json()["scope"] == "core"


def test_login_tenant_user(client, monkeypatch):
    async def fake_login_tenant_user(tenant_id, email, password):
        return {
            "user": {
                "id": "tenant-user",
                "email": email,
                "full_name": "Tenant",
                "is_active": True,
                "is_owner": False,
            },
            "access_token": "token-tenant",
            "token_type": "bearer",
            "scope": "tenant",
            "tenant_id": tenant_id,
        }

    monkeypatch.setattr(auth_service, "login_tenant_user", fake_login_tenant_user)

    response = client.post(
        "/api/v1/auth/login",
        headers={"X-Tenant-Id": "tenant-123"},
        json={"email": "tenant@example.com", "password": "secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["tenant_id"] == "tenant-123"


@pytest.fixture
def tenant_user_override():
    user = SimpleNamespace(id="tenant-user", email="tenant@example.com")

    async def override():
        return user, "tenant-123"

    app.dependency_overrides[get_current_user_tenant] = override
    yield user
    app.dependency_overrides.pop(get_current_user_tenant, None)


def test_get_tenant_profile(client, monkeypatch, tenant_user_override):
    async def fake_get_profile(user_id, tenant_id):
        return {
            "id": str(user_id),
            "email": "tenant@example.com",
            "full_name": "Tenant",
            "phone": None,
            "avatar_url": None,
            "is_owner": False,
            "is_active": True,
            "metadata": {},
            "created_at": "2025-01-01 00:00:00",
            "updated_at": "2025-01-01 00:00:00",
        }

    monkeypatch.setattr(user_service, "get_tenant_user_profile", fake_get_profile)

    response = client.get(
        "/api/v1/users/me",
        headers={"X-Tenant-Id": "tenant-123"},
    )

    assert response.status_code == 200
    assert response.json()["email"] == "tenant@example.com"


def test_update_tenant_profile(client, monkeypatch, tenant_user_override):
    async def fake_update_profile(user_id, tenant_id, **data):
        assert data["full_name"] == "Updated Tenant"
        return {
            "id": str(user_id),
            "email": "tenant@example.com",
            "full_name": data["full_name"],
            "phone": data.get("phone"),
            "avatar_url": data.get("avatar_url"),
            "is_owner": False,
            "is_active": True,
            "metadata": data.get("metadata", {}),
            "updated_at": "2025-01-01 00:00:00",
        }

    monkeypatch.setattr(user_service, "update_tenant_user_profile", fake_update_profile)

    response = client.put(
        "/api/v1/users/me",
        headers={"X-Tenant-Id": "tenant-123"},
        json={"full_name": "Updated Tenant", "metadata": {"role": "member"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["full_name"] == "Updated Tenant"
    assert body["metadata"]["role"] == "member"
