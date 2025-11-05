from typing import Optional
from contextvars import ContextVar
from fastapi import Header, HTTPException, status
from app.config import get_settings

settings = get_settings()

# Context variable for current tenant
current_tenant: ContextVar[Optional[str]] = ContextVar("current_tenant", default=None)

class TenantContext:
    """Manages tenant context throughout request lifecycle"""
    
    @staticmethod
    def set_tenant(tenant_id: str) -> None:
        """Set current tenant in context"""
        current_tenant.set(tenant_id)
    
    @staticmethod
    def get_tenant() -> Optional[str]:
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


async def get_optional_tenant(
    x_tenant: Optional[str] = Header(None, alias=settings.TENANT_HEADER_NAME)
) -> Optional[str]:
    """Dependency to extract optional tenant header"""
    return x_tenant


async def get_required_tenant(
    x_tenant: Optional[str] = Header(None, alias=settings.TENANT_HEADER_NAME)
) -> str:
    """Dependency to extract and validate required tenant header"""
    if not x_tenant:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing {settings.TENANT_HEADER_NAME} header"
        )
    return x_tenant