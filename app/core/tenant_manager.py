from contextvars import ContextVar

from fastapi import Header, HTTPException, status

from app.config import get_settings

settings = get_settings()

current_tenant: ContextVar[str | None] = ContextVar("current_tenant", default=None)


class TenantContext:
    """
    Manages tenant context throughout request lifecycle
    Uses ContextVar for thread-safe, async-compatible context storage
    """

    @staticmethod
    def set_tenant(tenant_id: str) -> None:
        """Set current tenant in context"""
        current_tenant.set(tenant_id)

    @staticmethod
    def get_tenant() -> str | None:
        """Get current tenant from context"""
        return current_tenant.get()

    @staticmethod
    def clear_tenant() -> None:
        """Clear tenant context"""
        current_tenant.set(None)

    @staticmethod
    def is_tenant_context() -> bool:
        """Check if we're in a tenant context"""
        return current_tenant.get() is not None

    @staticmethod
    def require_tenant() -> str:
        """
        Get tenant from context, raise exception if not set
        Use this when tenant is required for the operation
        """
        tenant_id = current_tenant.get()
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant context is required but not set",
            )
        return tenant_id


async def get_optional_tenant_from_header(
    x_tenant: str | None = Header(None, alias=settings.TENANT_HEADER_NAME)
) -> str | None:
    """
    Dependency to extract optional tenant header
    Note: This reads from header, but middleware already sets context
    Use get_tenant_from_context() for better performance
    """
    return x_tenant


async def get_required_tenant_from_header(
    x_tenant: str | None = Header(None, alias=settings.TENANT_HEADER_NAME)
) -> str:
    """
    Dependency to extract and validate required tenant header
    Note: This reads from header, but middleware already sets context
    Use require_tenant_from_context() for better performance
    """
    if not x_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {settings.TENANT_HEADER_NAME} header",
        )
    return x_tenant


async def get_tenant_from_context() -> str | None:
    """
    FastAPI dependency to get tenant from context
    Middleware should have already set it from header
    """
    return TenantContext.get_tenant()


async def require_tenant_from_context() -> str:
    """
    FastAPI dependency to require tenant from context
    Raises exception if tenant is not set
    Use this in endpoints that require tenant context
    """
    tenant_id = TenantContext.get_tenant()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tenant context is required but not set. Please provide {settings.TENANT_HEADER_NAME} header.",
        )
    return tenant_id
