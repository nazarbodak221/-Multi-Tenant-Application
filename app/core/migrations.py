"""
Migration utilities for tenant databases
"""

import asyncio

from aerich import Command
from tortoise import Tortoise

from app.core.database import get_tenant_orm_config


async def apply_migrations_to_tenant(tenant_id: str) -> bool:
    """
    Apply migrations to a tenant database

    Args:
        tenant_id: Tenant/organization ID

    Returns:
        True if successful, False otherwise
    """
    try:
        # Get tenant ORM config
        tenant_config = get_tenant_orm_config(tenant_id)

        # Initialize Tortoise with tenant config
        await Tortoise.init(config=tenant_config)

        # Create Aerich command instance
        command = Command(
            tortoise_config=tenant_config, app="models", location="./migrations"
        )

        await command.init()

        # Apply all pending migrations
        await command.upgrade(run_in_transaction=True)

        await Tortoise.close_connections()
        return True

    except Exception as e:
        print(f"Error applying migrations to tenant {tenant_id}: {e}")
        try:
            await Tortoise.close_connections()
        except:
            pass
        return False
