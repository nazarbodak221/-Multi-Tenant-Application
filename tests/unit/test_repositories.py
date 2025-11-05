"""
Unit tests for repositories
"""
import pytest
from uuid import uuid4
from app.repositories.user_repositories import UserRepository, TenantUserRepository
from app.repositories.organization_repository import OrganizationRepository
from app.models.core import User, Organization
from app.models.tenant import TenantUser
from app.core.security import hash_password


@pytest.mark.asyncio
class TestUserRepository:
    """Tests for UserRepository"""
    
    async def test_create_user(self, core_db):
        """Test creating a new user"""
        repo = UserRepository()
        
        user = await repo.create_user(
            email="new@example.com",
            hashed_password=hash_password("password123"),
            full_name="New User"
        )
        
        assert user.id is not None
        assert user.email == "new@example.com"
        assert user.full_name == "New User"
        assert user.is_active is True
    
    async def test_get_by_id(self, core_db, core_user):
        """Test getting user by ID"""
        repo = UserRepository()
        
        user = await repo.get_by_id(core_user.id)
        
        assert user is not None
        assert user.id == core_user.id
        assert user.email == core_user.email
    
    async def test_get_by_id_not_found(self, core_db):
        """Test getting non-existent user"""
        repo = UserRepository()
        fake_id = uuid4()
        
        user = await repo.get_by_id(fake_id)
        
        assert user is None
    
    async def test_get_by_email(self, core_db, core_user):
        """Test getting user by email"""
        repo = UserRepository()
        
        user = await repo.get_by_email(core_user.email)
        
        assert user is not None
        assert user.email == core_user.email
    
    async def test_get_by_email_not_found(self, core_db):
        """Test getting user by non-existent email"""
        repo = UserRepository()
        
        user = await repo.get_by_email("nonexistent@example.com")
        
        assert user is None
    
    async def test_update_user(self, core_db, core_user):
        """Test updating user"""
        repo = UserRepository()
        
        updated = await repo.update(
            core_user.id,
            full_name="Updated Name"
        )
        
        assert updated is not None
        assert updated.full_name == "Updated Name"
        assert updated.email == core_user.email
    
    async def test_delete_user(self, core_db, core_user):
        """Test deleting user"""
        repo = UserRepository()
        user_id = core_user.id
        
        result = await repo.delete(user_id)
        
        assert result is True
        
        # Verify user is deleted
        user = await repo.get_by_id(user_id)
        assert user is None
    
    async def test_get_all(self, core_db):
        """Test getting all users with pagination"""
        repo = UserRepository()
        
        # Create multiple users
        for i in range(5):
            await repo.create_user(
                email=f"user{i}@example.com",
                hashed_password=hash_password("pass123")
            )
        
        users = await repo.get_all(skip=0, limit=10)
        
        assert len(users) >= 5
    
    async def test_exists(self, core_db, core_user):
        """Test checking if user exists"""
        repo = UserRepository()
        
        exists = await repo.exists(email=core_user.email)
        
        assert exists is True
        
        exists = await repo.exists(email="nonexistent@example.com")
        assert exists is False


@pytest.mark.asyncio
class TestTenantUserRepository:
    """Tests for TenantUserRepository"""
    
    async def test_create_tenant_user(self, tenant_db):
        """Test creating tenant user"""
        tenant_id = tenant_db
        from app.core.database import db_manager
        
        await db_manager.init_tenant_db(tenant_id)
        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
        
        user = await TenantUserModel.create(
            email="tenant@example.com",
            hashed_password=hash_password("pass123"),
            full_name="Tenant User",
            is_owner=False
        )
        
        assert user.id is not None
        assert user.email == "tenant@example.com"
        assert user.is_owner is False
    
    async def test_update_profile(self, tenant_db, tenant_user):
        """Test updating tenant user profile"""
        tenant_id = tenant_db
        from app.core.database import db_manager
        
        await db_manager.init_tenant_db(tenant_id)
        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
        
        user = await TenantUserModel.get(id=tenant_user.id)
        user.full_name = "Updated Name"
        user.phone = "+1234567890"
        await user.save()
        
        updated = await TenantUserModel.get(id=tenant_user.id)
        
        assert updated.full_name == "Updated Name"
        assert updated.phone == "+1234567890"


@pytest.mark.asyncio
class TestOrganizationRepository:
    """Tests for OrganizationRepository"""
    
    async def test_create_organization(self, core_db, core_user):
        """Test creating organization"""
        repo = OrganizationRepository()
        
        org = await repo.create_organization(
            name="Test Org",
            slug="test-org",
            owner_id=core_user.id,
            database_name="tenant_123"
        )
        
        assert org.id is not None
        assert org.name == "Test Org"
        assert org.slug == "test-org"
        assert org.owner_id == core_user.id
    
    async def test_get_by_slug(self, core_db, organization):
        """Test getting organization by slug"""
        repo = OrganizationRepository()
        
        org = await repo.get_by_slug(organization.slug)
        
        assert org is not None
        assert org.slug == organization.slug
    
    async def test_get_by_owner(self, core_db, core_user, organization):
        """Test getting organizations by owner"""
        repo = OrganizationRepository()
        
        orgs = await repo.get_by_owner(core_user.id)
        
        assert len(orgs) >= 1
        assert any(org.id == organization.id for org in orgs)

