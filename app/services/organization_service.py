import re
from typing import Any
from uuid import UUID

from app.core.database import db_manager
from app.core.exceptions import (
    ConflictError,
    DatabaseError,
    NotFoundError,
)
from app.core.utils import format_datetime
from app.events.emitter import EventType, event_emitter
from app.models.core import Organization, User
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.user_repositories import UserRepository


class OrganizationService:
    """Service for organization management"""

    def __init__(self):
        self.org_repo = OrganizationRepository()
        self.user_repo = UserRepository()

    @staticmethod
    def generate_slug(name: str) -> str:
        """Generate URL-friendly slug from organization name"""
        slug = name.lower()
        slug = re.sub(r"[^\w\s-]", "", slug)
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-")

    @staticmethod
    def generate_database_name(org_id: str) -> str:
        return f"tenant_{org_id}"

    async def create_organization(
        self, name: str, owner_id: UUID, slug: str | None = None
    ) -> dict[str, Any]:
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

        organization = Organization(name=name, slug=slug, owner_id=owner_id, database_name="")
        await organization.save()

        database_name = self.generate_database_name(str(organization.id))
        organization.database_name = database_name
        await organization.save()

        tenant_id = str(organization.id)
        db_created = await db_manager.create_tenant_database(tenant_id)

        if not db_created:
            # Rollback: delete organization if database creation failed
            await organization.delete()
            raise DatabaseError("Failed to create tenant database")

        from app.core.migrations import apply_migrations_to_tenant

        migrations_applied = await apply_migrations_to_tenant(tenant_id)

        if not migrations_applied:
            # Rollback: delete organization and database if migrations failed
            await organization.delete()
            # Optionally drop database
            raise DatabaseError("Failed to apply migrations to tenant database")

        await db_manager.init_tenant_db(tenant_id)

        await self._sync_owner_to_tenant(tenant_id, owner)

        await event_emitter.emit(
            EventType.ORGANIZATION_CREATED,
            {
                "organization_id": str(organization.id),
                "organization_name": organization.name,
                "owner_id": str(owner.id),
                "owner_email": owner.email,
            },
        )

        return {
            "id": str(organization.id),
            "name": organization.name,
            "slug": organization.slug,
            "database_name": organization.database_name,
            "owner_id": str(owner_id),
            "is_active": organization.is_active,
            "created_at": format_datetime(organization.created_at),
            "updated_at": (
                format_datetime(organization.updated_at) if organization.updated_at else None
            ),
        }

    async def _sync_owner_to_tenant(self, tenant_id: str, owner: User) -> None:
        """
        Sync organization owner to tenant database as owner user

        Args:
            tenant_id: Tenant/organization ID
            owner: Owner user object
        """
        await db_manager.init_tenant_db(tenant_id)

        from tortoise import Tortoise

        from app.models.tenant import TenantUser

        connection_name = db_manager.get_tenant_connection_name(tenant_id)
        conn = Tortoise.get_connection(connection_name)

        existing_owner = await TenantUser.filter(email=owner.email).using_db(conn).first()

        if not existing_owner:
            from app.core.security import hash_password

            default_password = hash_password("changeme123")

            tenant_user = TenantUser(
                email=owner.email,
                hashed_password=default_password,
                full_name=owner.full_name,
                is_owner=True,
                is_active=True,
            )
            await tenant_user.save(using_db=conn)

    async def get_organization(self, org_id: UUID) -> dict[str, Any]:
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
            "updated_at": format_datetime(organization.updated_at),
        }

    async def get_organizations_by_owner(self, owner_id: UUID) -> list[dict[str, Any]]:
        organizations = await self.org_repo.get_by_owner(owner_id)

        return [
            {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "database_name": org.database_name,
                "owner_id": str(org.owner_id),
                "is_active": org.is_active,
                "created_at": format_datetime(org.created_at),
                "updated_at": (format_datetime(org.updated_at) if org.updated_at else None),
            }
            for org in organizations
        ]


organization_service = OrganizationService()
