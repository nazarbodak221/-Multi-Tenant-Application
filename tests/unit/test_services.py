"""
Unit tests for services
"""

from uuid import uuid4

import pytest

from app.core.exceptions import (AuthenticationError, ConflictError,
                                 NotFoundError)
from app.services.auth_service import auth_service
from app.services.organization_service import organization_service
from app.services.user_service import user_service


@pytest.mark.asyncio
class TestAuthService:
    """Tests for AuthService"""

    async def test_register_core_user(self, core_db):
        """Test registering core user"""
        result = await auth_service.register_core_user(
            email="newuser@example.com", password="password123", full_name="New User"
        )

        assert "user" in result
        assert "access_token" in result
        assert result["user"]["email"] == "newuser@example.com"
        assert result["scope"] == "core"
        assert result["token_type"] == "bearer"

    async def test_register_core_user_duplicate(self, core_db, core_user):
        """Test registering duplicate email raises error"""
        with pytest.raises(ConflictError):
            await auth_service.register_core_user(
                email=core_user.email, password="password123"
            )

    async def test_login_core_user(self, core_db, core_user):
        """Test logging in core user"""
        result = await auth_service.login_core_user(
            email=core_user.email, password="testpass123"
        )

        assert "access_token" in result
        assert result["user"]["email"] == core_user.email
        assert result["scope"] == "core"

    async def test_login_core_user_wrong_password(self, core_db, core_user):
        """Test login with wrong password"""
        with pytest.raises(AuthenticationError):
            await auth_service.login_core_user(
                email=core_user.email, password="wrongpassword"
            )

    async def test_login_core_user_invalid_email(self, core_db):
        """Test login with non-existent email"""
        with pytest.raises(AuthenticationError):
            await auth_service.login_core_user(
                email="nonexistent@example.com", password="password123"
            )

    async def test_register_tenant_user(self, tenant_db):
        """Test registering tenant user"""
        tenant_id = tenant_db

        result = await auth_service.register_tenant_user(
            tenant_id=tenant_id,
            email="tenant@example.com",
            password="password123",
            full_name="Tenant User",
        )

        assert "access_token" in result
        assert result["user"]["email"] == "tenant@example.com"
        assert result["scope"] == "tenant"
        assert result["tenant_id"] == tenant_id

    async def test_login_tenant_user(self, tenant_db, tenant_user):
        """Test logging in tenant user"""
        tenant_id = tenant_db

        result = await auth_service.login_tenant_user(
            tenant_id=tenant_id, email=tenant_user.email, password="testpass123"
        )

        assert "access_token" in result
        assert result["user"]["email"] == tenant_user.email
        assert result["scope"] == "tenant"


@pytest.mark.asyncio
class TestUserService:
    """Tests for UserService"""

    async def test_get_core_user_profile(self, core_db, core_user):
        """Test getting core user profile"""
        profile = await user_service.get_core_user_profile(core_user.id)

        assert profile["id"] == str(core_user.id)
        assert profile["email"] == core_user.email
        assert "owned_organizations" in profile

    async def test_update_core_user_profile(self, core_db, core_user):
        """Test updating core user profile"""
        profile = await user_service.update_core_user_profile(
            core_user.id, full_name="Updated Name"
        )

        assert profile["full_name"] == "Updated Name"
        assert profile["email"] == core_user.email

    async def test_get_tenant_user_profile(self, tenant_db, tenant_user):
        """Test getting tenant user profile"""
        tenant_id = tenant_db

        profile = await user_service.get_tenant_user_profile(
            tenant_user.id, tenant_id=tenant_id
        )

        assert profile["id"] == str(tenant_user.id)
        assert profile["email"] == tenant_user.email

    async def test_update_tenant_user_profile(self, tenant_db, tenant_user):
        """Test updating tenant user profile"""
        tenant_id = tenant_db

        profile = await user_service.update_tenant_user_profile(
            tenant_user.id,
            tenant_id=tenant_id,
            full_name="Updated Name",
            phone="+1234567890",
        )

        assert profile["full_name"] == "Updated Name"
        assert profile["phone"] == "+1234567890"


@pytest.mark.asyncio
class TestOrganizationService:
    """Tests for OrganizationService"""

    async def test_create_organization(self, core_db, core_user):
        """Test creating organization"""
        result = await organization_service.create_organization(
            name="New Organization", owner_id=core_user.id
        )

        assert result["name"] == "New Organization"
        assert result["owner_id"] == str(core_user.id)
        assert "slug" in result
        assert "database_name" in result

    async def test_get_organization(self, core_db, organization):
        """Test getting organization"""
        result = await organization_service.get_organization(organization.id)

        assert result["id"] == str(organization.id)
        assert result["name"] == organization.name

    async def test_get_organizations_by_owner(self, core_db, core_user, organization):
        """Test getting organizations by owner"""
        orgs = await organization_service.get_organizations_by_owner(core_user.id)

        assert len(orgs) >= 1
        assert any(org["id"] == str(organization.id) for org in orgs)

    async def test_generate_slug(self):
        """Test slug generation"""
        slug = organization_service.generate_slug("My Company LLC")

        assert slug == "my-company-llc"
        assert "-" in slug
        assert slug.islower()
