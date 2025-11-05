"""
Integration tests for tenant isolation
"""
import pytest
from httpx import AsyncClient
from app.core.database import db_manager
from app.models.tenant import TenantUser


@pytest.mark.asyncio
class TestTenantIsolation:
    """Test tenant data isolation"""
    
    async def test_tenant_a_cannot_see_tenant_b_data(
        self, core_db, test_client: AsyncClient
    ):
        """Test user from tenant A cannot see data from tenant B"""
        # Create two organizations
        # Register core user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@example.com",
                "password": "password123"
            }
        )
        core_token = register_response.json()["access_token"]
        
        # Create organization A
        org_a_response = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={"name": "Company A"}
        )
        org_a_id = org_a_response.json()["id"]
        
        # Create organization B
        org_b_response = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={"name": "Company B"}
        )
        org_b_id = org_b_response.json()["id"]
        
        # Register user in tenant A
        user_a_response = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": org_a_id},
            json={
                "email": "user_a@example.com",
                "password": "password123"
            }
        )
        user_a_token = user_a_response.json()["access_token"]
        
        # Register user in tenant B
        user_b_response = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": org_b_id},
            json={
                "email": "user_b@example.com",
                "password": "password123"
            }
        )
        user_b_token = user_b_response.json()["access_token"]
        user_b_id = user_b_response.json()["user"]["id"]
        
        # User A tries to access User B's profile (should fail)
        # Note: This tests that tenant context is properly enforced
        # User A can only see their own data in tenant A
        
        # User A gets their own profile (should work)
        profile_a = await test_client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {user_a_token}",
                "X-Tenant-Id": org_a_id
            }
        )
        assert profile_a.status_code == 200
        assert profile_a.json()["email"] == "user_a@example.com"
        
        # User A tries to access with tenant B context (should fail - wrong tenant)
        profile_b_attempt = await test_client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {user_a_token}",
                "X-Tenant-Id": org_b_id
            }
        )
        # Should fail because token tenant_id doesn't match requested tenant_id
        assert profile_b_attempt.status_code in [400, 403]
    
    async def test_users_in_different_tenants_can_have_same_email(
        self, core_db, test_client: AsyncClient
    ):
        """Test that same email can exist in different tenants"""
        # Register core user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@example.com",
                "password": "password123"
            }
        )
        core_token = register_response.json()["access_token"]
        
        # Create two organizations
        org_a = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={"name": "Company A"}
        )
        org_a_id = org_a.json()["id"]
        
        org_b = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={"name": "Company B"}
        )
        org_b_id = org_b.json()["id"]
        
        # Register same email in tenant A
        user_a = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": org_a_id},
            json={
                "email": "same@example.com",
                "password": "password123"
            }
        )
        assert user_a.status_code == 201
        
        # Register same email in tenant B (should work - different tenants)
        user_b = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": org_b_id},
            json={
                "email": "same@example.com",
                "password": "password123"
            }
        )
        assert user_b.status_code == 201
        
        # Both should have same email but different IDs
        assert user_a.json()["user"]["email"] == "same@example.com"
        assert user_b.json()["user"]["email"] == "same@example.com"
        assert user_a.json()["user"]["id"] != user_b.json()["user"]["id"]

