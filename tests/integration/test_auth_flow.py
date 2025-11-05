"""
Integration tests for authentication flow
"""

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
class TestAuthFlow:
    """Integration tests for full authentication flow"""

    async def test_register_and_login_core_user(
        self, core_db, test_client: AsyncClient
    ):
        """Test complete flow: register → login core user"""
        # Register
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "password123",
                "full_name": "New User",
            },
        )

        assert register_response.status_code == 201
        register_data = register_response.json()
        assert "access_token" in register_data
        assert register_data["scope"] == "core"

        # Login
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": "newuser@example.com", "password": "password123"},
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert "access_token" in login_data
        assert login_data["user"]["email"] == "newuser@example.com"

    async def test_register_and_login_tenant_user(
        self, core_db, tenant_db, test_client: AsyncClient
    ):
        """Test complete flow: register → login tenant user"""
        tenant_id = tenant_db

        # Register tenant user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": tenant_id},
            json={
                "email": "tenant@example.com",
                "password": "password123",
                "full_name": "Tenant User",
            },
        )

        assert register_response.status_code == 201
        register_data = register_response.json()
        assert register_data["scope"] == "tenant"
        assert register_data["tenant_id"] == tenant_id

        # Login tenant user
        login_response = await test_client.post(
            "/api/v1/auth/login",
            headers={"X-Tenant-Id": tenant_id},
            json={"email": "tenant@example.com", "password": "password123"},
        )

        assert login_response.status_code == 200
        login_data = login_response.json()
        assert login_data["scope"] == "tenant"
        assert login_data["tenant_id"] == tenant_id

    async def test_login_wrong_password(
        self, core_db, core_user, test_client: AsyncClient
    ):
        """Test login with wrong password"""
        response = await test_client.post(
            "/api/v1/auth/login",
            json={"email": core_user.email, "password": "wrongpassword"},
        )

        assert response.status_code == 401

    async def test_register_duplicate_email(
        self, core_db, core_user, test_client: AsyncClient
    ):
        """Test registering duplicate email"""
        response = await test_client.post(
            "/api/v1/auth/register",
            json={"email": core_user.email, "password": "password123"},
        )

        assert response.status_code == 400
