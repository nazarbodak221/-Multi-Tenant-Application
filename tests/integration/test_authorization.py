"""
Integration tests for authorization
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestAuthorization:
    """Test authorization rules"""

    async def test_only_core_user_can_create_organization(
        self, core_db, test_client: AsyncClient
    ):
        """Test that only core users can create organizations"""
        # Try without authentication
        response = await test_client.post(
            "/api/v1/organizations", json={"name": "Test Org"}
        )
        assert response.status_code == 403  # Forbidden

        # Register core user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "owner@example.com", "password": "password123"},
        )
        core_token = register_response.json()["access_token"]

        # Create organization with core token (should work)
        org_response = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={"name": "Test Org"},
        )
        assert org_response.status_code == 201

    async def test_tenant_user_cannot_create_organization(
        self, core_db, tenant_db, test_client: AsyncClient
    ):
        """Test that tenant users cannot create organizations"""
        tenant_id = tenant_db

        # Register tenant user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": tenant_id},
            json={"email": "tenant@example.com", "password": "password123"},
        )
        tenant_token = register_response.json()["access_token"]

        # Try to create organization with tenant token (should fail)
        response = await test_client.post(
            "/api/v1/organizations",
            headers={
                "Authorization": f"Bearer {tenant_token}",
                "X-Tenant-Id": tenant_id,
            },
            json={"name": "Test Org"},
        )
        # Should fail because tenant token scope is not "core"
        assert response.status_code in [400, 403]

    async def test_core_user_can_access_own_organizations(
        self, core_db, test_client: AsyncClient
    ):
        """Test core user can access their own organizations"""
        # Register and create org
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={"email": "owner@example.com", "password": "password123"},
        )
        core_token = register_response.json()["access_token"]

        # Create organization
        org_response = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={"name": "My Org"},
        )
        org_id = org_response.json()["id"]

        # Get my organizations
        my_orgs = await test_client.get(
            "/api/v1/organizations/me",
            headers={"Authorization": f"Bearer {core_token}"},
        )
        assert my_orgs.status_code == 200
        orgs = my_orgs.json()
        assert len(orgs) >= 1
        assert any(org["id"] == org_id for org in orgs)

    async def test_tenant_user_requires_tenant_header(
        self, core_db, tenant_db, test_client: AsyncClient
    ):
        """Test tenant user endpoints require X-Tenant-Id header"""
        tenant_id = tenant_db

        # Register tenant user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": tenant_id},
            json={"email": "tenant@example.com", "password": "password123"},
        )
        tenant_token = register_response.json()["access_token"]

        # Try to access profile without tenant header
        response = await test_client.get(
            "/api/v1/users/me", headers={"Authorization": f"Bearer {tenant_token}"}
        )
        # Should fail - tenant context required
        assert response.status_code in [400, 403]

        # Try with tenant header (should work)
        response = await test_client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {tenant_token}",
                "X-Tenant-Id": tenant_id,
            },
        )
        assert response.status_code == 200
