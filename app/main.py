from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import auth, organizations, users
from app.config import get_settings
from app.core.database import db_manager
from app.events.handlers import register_handlers
from app.middleware.logging import StructuredLoggingMiddleware, setup_logging
from app.middleware.tenant_context import TenantContextMiddleware

settings = get_settings()

# Setup logging
setup_logging(level="INFO" if not settings.DEBUG else "DEBUG")

# Register event handlers
register_handlers()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles database initialization on startup and cleanup on shutdown.
    """
    await db_manager.init_core_db()
    yield
    await db_manager.close_all()


app = FastAPI(
    title="Multi-Tenant Application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(TenantContextMiddleware)
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(organizations.router, prefix=settings.API_V1_PREFIX)
app.include_router(users.router, prefix=settings.API_V1_PREFIX)

@app.get("/health", tags=["System"])
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
