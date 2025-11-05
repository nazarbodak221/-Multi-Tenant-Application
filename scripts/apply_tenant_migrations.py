"""
Script to apply migrations to a newly created tenant database
This is called automatically when a new organization is created
"""
import asyncio
import sys
from app.core.migrations import apply_migrations_to_tenant


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/apply_tenant_migrations.py <tenant_id>")
        sys.exit(1)
    
    tenant_id = sys.argv[1]
    success = asyncio.run(apply_migrations_to_tenant(tenant_id))
    sys.exit(0 if success else 1)

