"""
Script to apply migrations to tenant databases
Usage: 
  python scripts/migrate_tenant.py <tenant_id>  # Migrate specific tenant
  python scripts/migrate_tenant.py              # Migrate all tenants
"""
import asyncio
import sys


async def migrate_tenant(tenant_id: str):
    """
    Apply migrations to a tenant database
    
    Args:
        tenant_id: Tenant/organization ID
    """
    from app.core.migrations import apply_migrations_to_tenant
    
    print(f"Applying migrations to tenant: {tenant_id}")
    
    success = await apply_migrations_to_tenant(tenant_id)
    
    if success:
        print(f"GOOD: Migrations applied successfully to tenant {tenant_id}")
    else:
        print(f"BAD: Failed to apply migrations to tenant {tenant_id}")
        raise Exception(f"Migration failed for tenant {tenant_id}")


async def migrate_all_tenants():
    """
    Apply migrations to all existing tenant databases
    """
    from app.repositories.organization_repository import OrganizationRepository
    from app.core.database import db_manager
    
    # Initialize core DB
    await db_manager.init_core_db()
    
    # Get all organizations
    org_repo = OrganizationRepository()
    organizations = await org_repo.get_all()
    
    print(f"Found {len(organizations)} organizations")
    
    for org in organizations:
        tenant_id = str(org.id)
        try:
            await migrate_tenant(tenant_id)
        except Exception as e:
            print(f"Failed to migrate tenant {tenant_id}: {e}")
            continue
    
    await db_manager.close_all()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Migrate specific tenant
        tenant_id = sys.argv[1]
        asyncio.run(migrate_tenant(tenant_id))
    else:
        # Migrate all tenants
        asyncio.run(migrate_all_tenants())

