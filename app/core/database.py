from typing import Optional, Dict
from contextlib import asynccontextmanager
from tortoise import Tortoise
import asyncpg
from app.config import get_settings

settings = get_settings()

class DatabaseManager:
    """
    Manages connections to core and tenant databases.
    Implements connection pooling and dynamic tenant routing.
    """
    _instance: Optional["DatabaseManager"] = None
    _tenant_connections: Dict[str, bool] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def init_core_db(self):
        """Initialize core database connection."""
        await Tortoise.init(
            db_url=settings.core_database_url,
            modules={"models": ["app.models.core"]},
        )
        await Tortoise.generate_schemas()
    
    async def init_tenant_db(self, tenant_id: str):
        """Initialize or connect to tenant database."""
        db_name = f"tenant_{tenant_id}"
        
        if tenant_id in self._tenant_connections:
            return
        
        tenant_url = settings.tenant_database_url(tenant_id)
        
        await Tortoise.init(
            db_url=tenant_url,
            modules={"models": ["app.models.tenant"]},
            _create_db=False,
            use_tz=True,
        )
        
        await Tortoise.generate_schemas()
        self._tenant_connections[tenant_id] = True
    
    async def create_tenant_database(self, tenant_id: str) -> bool:
        """
        Creates a new PostgreSQL database for a tenant.
        Returns True if successful, False otherwise.
        """
        db_name = f"tenant_{tenant_id}"
        
        try:
            # Connect to postgres database to create new database
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
        """Context manager for tenant database connections."""
        if tenant_id not in self._tenant_connections:
            await self.init_tenant_db(tenant_id)
        
        connection_name = f"tenant_{tenant_id}"
        try:
            yield Tortoise.get_connection(connection_name)
        finally:
            pass
    
    async def close_all(self):
        """Close all database connections."""
        await Tortoise.close_connections()
        self._tenant_connections.clear()


db_manager = DatabaseManager()