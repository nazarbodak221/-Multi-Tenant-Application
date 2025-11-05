"""
Initialize Aerich for core database
Run this once to set up Aerich migrations
"""

import asyncio

from aerich import Command

from app.core.database import TORTOISE_ORM


async def init_aerich():
    """Initialize Aerich for core database"""
    print("Initializing Aerich for core database...")

    command = Command(
        tortoise_config=TORTOISE_ORM, app="models", location="./migrations"
    )

    await command.init()
    print("GOOD: Aerich initialized successfully")
    print("RUN: 'aerich init-db' to create initial migration")
    print("RUN: 'aerich migrate' to create new migrations")
    print("RUN: 'aerich upgrade' to apply migrations")


if __name__ == "__main__":
    asyncio.run(init_aerich())
