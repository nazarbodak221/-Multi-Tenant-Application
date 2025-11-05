"""
Script to create initial migration for core database
Run this after setting up Aerich
"""

import asyncio

from aerich import Command

from app.core.database import get_tortoise_orm_config


async def create_initial_migration():
    """Create initial migration from models"""
    print("Creating initial migration for core database...")

    config = get_tortoise_orm_config()

    command = Command(tortoise_config=config, app="models", location="./migrations")

    await command.init()

    await command.init_db()

    print("GOOD: Initial migration created successfully")
    print("Migration files created in migrations/models/")


if __name__ == "__main__":
    asyncio.run(create_initial_migration())
