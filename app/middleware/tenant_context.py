
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import get_settings
from app.core.tenant_manager import TenantContext

settings = get_settings()


class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware that extracts X-Tenant-Id header and sets it in context
    This allows tenant context to be available throughout the request lifecycle
    """

    async def dispatch(self, request: Request, call_next):
        """
        Extract tenant ID from header and set in context
        Clears context after request completes
        """
        tenant_id: str | None = request.headers.get(
            settings.TENANT_HEADER_NAME, None
        )

        if tenant_id:
            TenantContext.set_tenant(tenant_id)

        try:
            response = await call_next(request)
            return response
        finally:
            TenantContext.clear_tenant()
