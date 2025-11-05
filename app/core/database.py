from contextlib import asynccontextmanager
from typing import Dict, Optional

import asyncpg
from tortoise import Tortoise

from app.config import get_settings

settings = get_settings()


# Tortoise ORM configuration for Aerich
def get_tortoise_orm_config() -> dict:
    """Get Tortoise ORM config with current settings"""
    return {
        "connections": {
            "default": settings.core_database_url,
        },
        "apps": {
            "models": {
                "models": ["app.models.core", "aerich.models"],
                "default_connection": "default",
            },
        },
    }


TORTOISE_ORM = get_tortoise_orm_config()


# Tenant ORM configuration template
def get_tenant_orm_config(tenant_id: str) -> dict:
    """Get Tortoise ORM config for tenant database"""
    return {
        "connections": {
            "tenant": settings.tenant_database_url(tenant_id),
        },
        "apps": {
            "models": {
                "models": ["app.models.tenant", "aerich.models"],
                "default_connection": "tenant",
            },
        },
    }


class DatabaseManager:
    """
    Manages connections to core and tenant databases
    Implements connection pooling and dynamic tenant routing
    Each tenant gets its own connection pool for better isolation
    """

    _instance: Optional["DatabaseManager"] = None
    _tenant_connections: Dict[str, bool] = {}
    _core_initialized: bool = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def init_core_db(self):
        """Initialize core database connection with named connection"""
        if self._core_initialized:
            return

        connections_dict = {
            "default": settings.core_database_url,
        }

        for tenant_id in self._tenant_connections.keys():
            connection_name = self.get_tenant_connection_name(tenant_id)
            connections_dict[connection_name] = settings.tenant_database_url(tenant_id)

        apps_dict = {
            "core": {
                "models": ["app.models.core"],
                "default_connection": "default",
            }
        }

        if self._tenant_connections:
            first_tenant = list(self._tenant_connections.keys())[0]
            tenant_conn_name = self.get_tenant_connection_name(first_tenant)
            apps_dict["tenant"] = {
                "models": ["app.models.tenant"],
                "default_connection": tenant_conn_name,
            }

        config = {
            "connections": connections_dict,
            "apps": apps_dict
        }
        await Tortoise.init(config=config)
        await Tortoise.generate_schemas()
        self._core_initialized = True

    async def init_tenant_db(self, tenant_id: str):
        """Initialize or connect to tenant database with its own connection pool"""
        connection_name = self.get_tenant_connection_name(tenant_id)

        # Check if connection already exists
        if tenant_id in self._tenant_connections:
            return

        # Re-initialize Tortoise with all connections including new tenant
        self._tenant_connections[tenant_id] = True

        # Close existing connections
        if Tortoise._inited:
            await Tortoise.close_connections()
            self._core_initialized = False

        connections_dict = {
            "default": settings.core_database_url,
        }

        for tid in self._tenant_connections.keys():
            conn_name = self.get_tenant_connection_name(tid)
            connections_dict[conn_name] = settings.tenant_database_url(tid)

        apps_dict = {
            "core": {
                "models": ["app.models.core"],
                "default_connection": "default",
            },
            "tenant": {
                "models": ["app.models.tenant"],
                "default_connection": connection_name, 
            }
        }

        config = {
            "connections": connections_dict,
            "apps": apps_dict
        }
        await Tortoise.init(config=config)

    def get_tenant_connection_name(self, tenant_id: str) -> str:
        """Get connection name for tenant"""
        return f"tenant_{tenant_id}"

    async def create_tenant_database(self, tenant_id: str) -> bool:
        """
        Creates a new PostgreSQL database for a tenant
        Returns True if successful, False otherwise
        """
        db_name = f"tenant_{tenant_id}"

        try:
            conn = await asyncpg.connect(
                host=settings.TENANT_DB_HOST,
                port=settings.TENANT_DB_PORT,
                user=settings.TENANT_DB_USER,
                password=settings.TENANT_DB_PASSWORD,
                database="postgres",
            )

            # Check if database exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )

            if not exists:
                await conn.execute(f'CREATE DATABASE "{db_name}"')

            await conn.close()

            # Initialize tenant database with schema
            await self.init_tenant_db(tenant_id)

            return True

        except Exception as e:
            print(f"Error creating tenant database: {e}")
            return False

    @asynccontextmanager
    async def get_tenant_connection(self, tenant_id: str):
        """
        Context manager for tenant database connections
        Ensures connection is initialized and returns the connection pool
        """
        if tenant_id not in self._tenant_connections:
            await self.init_tenant_db(tenant_id)

        connection_name = self.get_tenant_connection_name(tenant_id)
        try:
            connection = Tortoise.get_connection(connection_name)
            yield connection
        except Exception as e:
            # Re-initialize if connection was closed
            if tenant_id in self._tenant_connections:
                del self._tenant_connections[tenant_id]
            await self.init_tenant_db(tenant_id)
            connection = Tortoise.get_connection(connection_name)
            yield connection

    def get_tenant_model(self, tenant_id: str, model_class):
        """Return model class bound to a specific tenant connection"""
        return model_class

    async def close_all(self):
        """Close all database connections"""
        await Tortoise.close_connections()
        self._tenant_connections.clear()
        self._core_initialized = False


db_manager = DatabaseManager()
