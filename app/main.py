from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.core.database import db_manager
from app.middleware.tenant_context import TenantContextMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles database initialization on startup and cleanup on shutdown.
    """
    # Startup: Initialize core database
    await db_manager.init_core_db()
    yield
    # Shutdown: Close all database connections
    await db_manager.close_all()


app = FastAPI(
    title="Multi-Tenant Application",
    version="1.0.0",
    lifespan=lifespan,
)

# Add tenant context middleware
app.add_middleware(TenantContextMiddleware)


@app.get("/")
async def root():
    return {"message": "Multi-Tenant Application API"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
