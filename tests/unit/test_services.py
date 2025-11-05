"""
Unit tests for services with mocks
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import AuthenticationError, ConflictError
from app.services.auth_service import AuthService
from app.services.organization_service import OrganizationService
from app.services.user_service import UserService


@pytest.mark.asyncio
class TestAuthService:
    """Tests for AuthService with mocks"""

    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.hash_password")
    @patch("app.services.auth_service.create_core_token")
    async def test_register_core_user(self, mock_token, mock_hash, mock_repo_class):
        """Test registering core user"""
        # Setup mocks
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_email = AsyncMock(return_value=None)

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_repo.create_user = AsyncMock(return_value=mock_user)

        mock_hash.return_value = "hashed_password"
        mock_token.return_value = "token123"

        # Test
        service = AuthService()
        result = await service.register_core_user(
            email="test@example.com", password="pass123", full_name="Test User"
        )

        # Assertions
        assert result["user"]["email"] == "test@example.com"
        assert result["access_token"] == "token123"
        assert result["scope"] == "core"
        mock_repo.get_by_email.assert_awaited_once()
        mock_repo.create_user.assert_awaited_once()

    @patch("app.services.auth_service.UserRepository")
    async def test_register_core_user_duplicate(self, mock_repo_class):
        """Test registering duplicate email raises error"""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_user = MagicMock()
        mock_repo.get_by_email = AsyncMock(return_value=mock_user)

        service = AuthService()
        with pytest.raises(ConflictError):
            await service.register_core_user(
                email="test@example.com", password="pass123"
            )

    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.verify_password")
    @patch("app.services.auth_service.create_core_token")
    async def test_login_core_user(self, mock_token, mock_verify, mock_repo_class):
        """Test logging in core user"""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.hashed_password = "hashed"
        mock_repo.get_by_email = AsyncMock(return_value=mock_user)

        mock_verify.return_value = True
        mock_token.return_value = "token123"

        service = AuthService()
        result = await service.login_core_user(
            email="test@example.com", password="pass123"
        )

        assert result["access_token"] == "token123"
        assert result["user"]["email"] == "test@example.com"

    @patch("app.services.auth_service.UserRepository")
    @patch("app.services.auth_service.verify_password")
    async def test_login_core_user_wrong_password(self, mock_verify, mock_repo_class):
        """Test login with wrong password"""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        mock_user = MagicMock()
        mock_user.hashed_password = "hashed"
        mock_repo.get_by_email = AsyncMock(return_value=mock_user)
        mock_verify.return_value = False

        service = AuthService()
        with pytest.raises(AuthenticationError):
            await service.login_core_user(email="test@example.com", password="wrong")

    @patch("app.services.auth_service.UserRepository")
    async def test_login_core_user_invalid_email(self, mock_repo_class):
        """Test login with invalid email"""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo
        mock_repo.get_by_email = AsyncMock(return_value=None)

        service = AuthService()
        with pytest.raises(AuthenticationError):
            await service.login_core_user(
                email="nonexistent@example.com", password="pass123"
            )

    @patch("app.services.auth_service.db_manager")
    @patch("app.services.auth_service.TenantUser")
    @patch("app.services.auth_service.Tortoise")
    @patch("app.services.auth_service.hash_password")
    @patch("app.services.auth_service.create_tenant_token")
    async def test_register_tenant_user(
        self, mock_token, mock_hash, mock_tortoise, mock_tenant_user, mock_db
    ):
        """Test registering tenant user"""
        # Setup mocks
        mock_db.init_tenant_db = AsyncMock()
        mock_db.get_tenant_connection_name = MagicMock(return_value="tenant_test")
        mock_conn = MagicMock()
        mock_tortoise.get_connection = MagicMock(return_value=mock_conn)

        mock_filter = MagicMock()
        mock_filter.using_db = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=None)
        mock_tenant_user.filter = MagicMock(return_value=mock_filter)

        mock_using = MagicMock()
        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "tenant@example.com"
        mock_user.full_name = "Tenant User"
        mock_user.is_owner = False
        mock_user.is_active = True
        mock_using.create = AsyncMock(return_value=mock_user)
        mock_tenant_user.using_db = MagicMock(return_value=mock_using)

        mock_hash.return_value = "hashed"
        mock_token.return_value = "token123"

        service = AuthService()
        result = await service.register_tenant_user(
            tenant_id="test_tenant",
            email="tenant@example.com",
            password="pass123",
            full_name="Tenant User",
        )

        assert result["user"]["email"] == "tenant@example.com"
        assert result["tenant_id"] == "test_tenant"
        assert result["scope"] == "tenant"

    @patch("app.services.auth_service.db_manager")
    @patch("app.services.auth_service.TenantUser")
    @patch("app.services.auth_service.Tortoise")
    @patch("app.services.auth_service.verify_password")
    @patch("app.services.auth_service.create_tenant_token")
    async def test_login_tenant_user(
        self, mock_token, mock_verify, mock_tortoise, mock_tenant_user, mock_db
    ):
        """Test logging in tenant user"""
        mock_db.init_tenant_db = AsyncMock()
        mock_db.get_tenant_connection_name = MagicMock(return_value="tenant_test")
        mock_conn = MagicMock()
        mock_tortoise.get_connection = MagicMock(return_value=mock_conn)

        mock_user = MagicMock()
        mock_user.id = uuid4()
        mock_user.email = "tenant@example.com"
        mock_user.hashed_password = "hashed"
        mock_user.is_active = True
        mock_user.is_owner = False
        mock_user.full_name = "Tenant User"

        mock_filter = MagicMock()
        mock_filter.using_db = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_user)
        mock_tenant_user.filter = MagicMock(return_value=mock_filter)

        mock_verify.return_value = True
        mock_token.return_value = "token123"

        service = AuthService()
        result = await service.login_tenant_user(
            tenant_id="test_tenant", email="tenant@example.com", password="pass123"
        )

        assert result["access_token"] == "token123"
        assert result["tenant_id"] == "test_tenant"


@pytest.mark.asyncio
class TestUserService:
    """Tests for UserService with mocks"""

    @patch("app.services.user_service.UserRepository")
    async def test_get_core_user_profile(self, mock_repo_class):
        """Test getting core user profile"""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True

        # Mock owned_organizations relationship
        mock_orgs = AsyncMock()
        mock_orgs.all = AsyncMock(return_value=[])
        mock_user.owned_organizations = mock_orgs

        mock_repo.get_by_id = AsyncMock(return_value=mock_user)

        service = UserService()
        result = await service.get_core_user_profile(user_id)

        assert result["id"] == str(user_id)
        assert result["email"] == "test@example.com"

    @patch("app.services.user_service.UserRepository")
    async def test_update_core_user_profile(self, mock_repo_class):
        """Test updating core user profile"""
        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "test@example.com"
        mock_user.full_name = "Updated Name"
        mock_user.is_active = True
        mock_repo.update = AsyncMock(return_value=mock_user)

        service = UserService()
        result = await service.update_core_user_profile(
            user_id, full_name="Updated Name"
        )

        assert result["full_name"] == "Updated Name"

    @patch("app.services.user_service.db_manager")
    @patch("app.services.user_service.TenantUser")
    @patch("app.services.user_service.Tortoise")
    async def test_get_tenant_user_profile(
        self, mock_tortoise, mock_tenant_user, mock_db
    ):
        """Test getting tenant user profile"""
        mock_db.init_tenant_db = AsyncMock()
        mock_db.get_tenant_connection_name = MagicMock(return_value="tenant_test")
        mock_conn = MagicMock()
        mock_tortoise.get_connection = MagicMock(return_value=mock_conn)

        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "tenant@example.com"
        mock_user.full_name = "Tenant User"
        mock_user.is_owner = False
        mock_user.is_active = True

        mock_filter = MagicMock()
        mock_filter.using_db = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_user)
        mock_tenant_user.filter = MagicMock(return_value=mock_filter)

        service = UserService()
        result = await service.get_tenant_user_profile("test_tenant", user_id)

        assert result["id"] == str(user_id)
        assert result["email"] == "tenant@example.com"

    @patch("app.services.user_service.db_manager")
    @patch("app.services.user_service.TenantUser")
    @patch("app.services.user_service.Tortoise")
    async def test_update_tenant_user_profile(
        self, mock_tortoise, mock_tenant_user, mock_db
    ):
        """Test updating tenant user profile"""
        mock_db.init_tenant_db = AsyncMock()
        mock_db.get_tenant_connection_name = MagicMock(return_value="tenant_test")
        mock_conn = MagicMock()
        mock_tortoise.get_connection = MagicMock(return_value=mock_conn)

        user_id = uuid4()
        mock_user = MagicMock()
        mock_user.id = user_id
        mock_user.email = "tenant@example.com"
        mock_user.full_name = "Updated Name"
        mock_user.is_owner = False
        mock_user.is_active = True
        mock_user.save = AsyncMock()

        mock_filter = MagicMock()
        mock_filter.using_db = MagicMock(return_value=mock_filter)
        mock_filter.first = AsyncMock(return_value=mock_user)
        mock_tenant_user.filter = MagicMock(return_value=mock_filter)

        service = UserService()
        result = await service.update_tenant_user_profile(
            "test_tenant", user_id, full_name="Updated Name"
        )

        assert result["full_name"] == "Updated Name"


@pytest.mark.asyncio
class TestOrganizationService:
    """Tests for OrganizationService with mocks"""

    @pytest.mark.skip(reason="Complex mocking required for database operations")
    @patch("app.services.organization_service.UserRepository")
    @patch("app.services.organization_service.OrganizationRepository")
    @patch("app.services.organization_service.db_manager")
    @patch("app.events.emitter.event_emitter")
    async def test_create_organization(
        self, mock_emitter, mock_db, mock_org_repo_class, mock_user_repo_class
    ):
        """Test creating organization"""
        from datetime import datetime

        mock_org_repo = AsyncMock()
        mock_org_repo_class.return_value = mock_org_repo

        mock_user_repo = AsyncMock()
        mock_user_repo_class.return_value = mock_user_repo

        org_id = uuid4()
        owner_id = uuid4()

        # Mock owner user
        mock_owner = MagicMock()
        mock_owner.id = owner_id
        mock_owner.email = "owner@example.com"
        mock_user_repo.get_by_id = AsyncMock(return_value=mock_owner)

        # Mock organization
        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.name = "Test Org"
        mock_org.slug = "test-org"
        mock_org.owner_id = owner_id
        mock_org.database_name = "tenant_test"
        mock_org.is_active = True
        mock_org.created_at = datetime(2025, 1, 1, 0, 0, 0)
        mock_org.updated_at = datetime(2025, 1, 1, 0, 0, 0)

        mock_org_repo.get_by_slug = AsyncMock(return_value=None)
        mock_org_repo.get_by_field = AsyncMock(
            return_value=None
        )  # No existing org with same name
        mock_org_repo.create_organization = AsyncMock(return_value=mock_org)
        mock_db.create_tenant_database = AsyncMock(return_value=True)
        mock_emitter.emit = AsyncMock()

        service = OrganizationService()
        result = await service.create_organization(
            owner_id=owner_id, name="Test Org", slug="test-org"
        )

        assert result["id"] == str(org_id)
        assert result["name"] == "Test Org"
        assert result["slug"] == "test-org"

    @patch("app.services.organization_service.OrganizationRepository")
    async def test_get_organization(self, mock_repo_class):
        """Test getting organization by slug"""
        from datetime import datetime

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        org_id = uuid4()
        owner_id = uuid4()
        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.name = "Test Org"
        mock_org.slug = "test-org"
        mock_org.owner_id = owner_id
        mock_org.is_active = True
        mock_org.created_at = datetime(2025, 1, 1, 0, 0, 0)
        mock_org.updated_at = datetime(2025, 1, 1, 0, 0, 0)

        # Mock get_by_id as well since service calls it internally
        mock_repo.get_by_id = AsyncMock(return_value=mock_org)

        service = OrganizationService()
        result = await service.get_organization(org_id)

        assert result["slug"] == "test-org"

    @patch("app.services.organization_service.OrganizationRepository")
    async def test_get_organizations_by_owner(self, mock_repo_class):
        """Test getting organizations by owner"""
        from datetime import datetime

        mock_repo = AsyncMock()
        mock_repo_class.return_value = mock_repo

        owner_id = uuid4()
        org_id = uuid4()
        mock_org = MagicMock()
        mock_org.id = org_id
        mock_org.name = "Test Org"
        mock_org.slug = "test-org"
        mock_org.owner_id = owner_id
        mock_org.is_active = True
        mock_org.created_at = datetime(2025, 1, 1, 0, 0, 0)
        mock_org.updated_at = datetime(2025, 1, 1, 0, 0, 0)

        mock_repo.get_by_owner = AsyncMock(return_value=[mock_org])

        service = OrganizationService()
        result = await service.get_organizations_by_owner(owner_id)

        assert len(result) == 1
        assert result[0]["owner_id"] == str(owner_id)
