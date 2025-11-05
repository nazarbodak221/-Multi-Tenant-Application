"""
Integration tests for complete application flow
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestFullFlow:
    """Test complete flow: register → login → create org → tenant register → tenant operations"""
    
    async def test_complete_flow(
        self, core_db, test_client: AsyncClient
    ):
        """Test complete application flow"""
        # Step 1: Register core user
        register_response = await test_client.post(
            "/api/v1/auth/register",
            json={
                "email": "owner@example.com",
                "password": "password123",
                "full_name": "Owner User"
            }
        )
        assert register_response.status_code == 201
        register_data = register_response.json()
        core_token = register_data["access_token"]
        owner_id = register_data["user"]["id"]
        
        # Step 2: Login core user
        login_response = await test_client.post(
            "/api/v1/auth/login",
            json={
                "email": "owner@example.com",
                "password": "password123"
            }
        )
        assert login_response.status_code == 200
        
        # Step 3: Create organization
        create_org_response = await test_client.post(
            "/api/v1/organizations",
            headers={"Authorization": f"Bearer {core_token}"},
            json={
                "name": "My Company",
                "slug": "my-company"
            }
        )
        assert create_org_response.status_code == 201
        org_data = create_org_response.json()
        org_id = org_data["id"]
        
        # Step 4: Register tenant user
        tenant_register_response = await test_client.post(
            "/api/v1/auth/register",
            headers={"X-Tenant-Id": org_id},
            json={
                "email": "employee@example.com",
                "password": "password123",
                "full_name": "Employee User"
            }
        )
        assert tenant_register_response.status_code == 201
        tenant_data = tenant_register_response.json()
        tenant_token = tenant_data["access_token"]
        
        # Step 5: Tenant operations - get profile
        profile_response = await test_client.get(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {tenant_token}",
                "X-Tenant-Id": org_id
            }
        )
        assert profile_response.status_code == 200
        profile = profile_response.json()
        assert profile["email"] == "employee@example.com"
        
        # Step 6: Tenant operations - update profile
        update_response = await test_client.put(
            "/api/v1/users/me",
            headers={
                "Authorization": f"Bearer {tenant_token}",
                "X-Tenant-Id": org_id
            },
            json={
                "full_name": "Updated Employee",
                "phone": "+1234567890"
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["full_name"] == "Updated Employee"
        assert updated["phone"] == "+1234567890"

