from typing import Dict, Any, Optional, List
from uuid import UUID
import re
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repositories import UserRepository
from app.core.database import db_manager
from app.core.exceptions import (
    NotFoundError,
    ConflictError,
    ValidationError,
    DatabaseError
)
from app.core.utils import format_datetime
from app.models.core import Organization, User


class OrganizationService:
    """Service for organization management"""
    
    def __init__(self):
        self.org_repo = OrganizationRepository()
        self.user_repo = UserRepository()
    
    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from organization name"""
        slug = name.lower()
        # Replace spaces and special chars with hyphens
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        # Remove leading/trailing hyphens
        slug = slug.strip('-')
        return slug
    
    @staticmethod
    def generate_database_name(org_id: str) -> str:
        return f"tenant_{org_id}"
    
    async def create_organization(
        self,
        name: str,
        owner_id: UUID,
        slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new organization with tenant database
        
        Args:
            name: Organization name
            owner_id: Owner (user) UUID
            slug: Optional custom slug (auto-generated if not provided)
            
        Returns:
            Dictionary with organization data
            
        Raises:
            NotFoundError: If owner user doesn't exist
            ConflictError: If organization with name/slug already exists
            DatabaseError: If tenant database creation fails
        """
        owner = await self.user_repo.get_by_id(owner_id)
        if not owner:
            raise NotFoundError("User", str(owner_id))
        
        if not slug:
            slug = self.generate_slug(name)
        
        existing_org = await self.org_repo.get_by_field(name=name)
        if existing_org:
            raise ConflictError(f"Organization with name '{name}' already exists")
        
        existing_slug = await self.org_repo.get_by_slug(slug)
        if existing_slug:
            raise ConflictError(f"Organization with slug '{slug}' already exists")
        
        organization = Organization(
            name=name,
            slug=slug,
            owner_id=owner_id,
            database_name=""
        )
        await organization.save()
        
        # Generate database name from organization ID
        database_name = self.generate_database_name(str(organization.id))
        organization.database_name = database_name
        await organization.save()
        
        # Create tenant database
        tenant_id = str(organization.id)
        db_created = await db_manager.create_tenant_database(tenant_id)
        
        if not db_created:
            # Rollback: delete organization if database creation failed
            await organization.delete()
            raise DatabaseError("Failed to create tenant database")
        
        # Sync owner to tenant database as owner user
        # This ensures the owner has access to tenant
        await self._sync_owner_to_tenant(tenant_id, owner)
        
        return {
            "id": str(organization.id),
            "name": organization.name,
            "slug": organization.slug,
            "database_name": organization.database_name,
            "owner_id": str(organization.owner_id),
            "is_active": organization.is_active,
            "created_at": format_datetime(organization.created_at)
        }
    
    async def _sync_owner_to_tenant(
        self,
        tenant_id: str,
        owner: User
    ) -> None:
        """
        Sync organization owner to tenant database as owner user
        
        Args:
            tenant_id: Tenant/organization ID
            owner: Owner user object
        """
        await db_manager.init_tenant_db(tenant_id)
        
        from app.models.tenant import TenantUser
        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
        
        # Check if owner already exists in tenant
        existing_owner = await TenantUserModel.get_or_none(email=owner.email)
        
        if not existing_owner:
            # Create owner user in tenant database
            from app.core.security import hash_password
            default_password = hash_password("changeme123")  # Should be changed on first login
            
            await TenantUserModel.create(
                email=owner.email,
                hashed_password=default_password,
                full_name=owner.full_name,
                is_owner=True,
                is_active=True
            )
    
    async def get_organization(
        self,
        org_id: UUID
    ) -> Dict[str, Any]:
        organization = await self.org_repo.get_by_id(org_id)
        if not organization:
            raise NotFoundError("Organization", str(org_id))
        
        return {
            "id": str(organization.id),
            "name": organization.name,
            "slug": organization.slug,
            "database_name": organization.database_name,
            "owner_id": str(organization.owner_id),
            "is_active": organization.is_active,
            "created_at": format_datetime(organization.created_at),
            "updated_at": format_datetime(organization.updated_at)
        }
    
    async def get_organizations_by_owner(
        self,
        owner_id: UUID
    ) -> List[Dict[str, Any]]:
        organizations = await self.org_repo.get_by_owner(owner_id)
        
        return [
            {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "database_name": org.database_name,
                "is_active": org.is_active,
                "created_at": format_datetime(org.created_at)
            }
            for org in organizations
        ]


organization_service = OrganizationService()

