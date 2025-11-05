from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from tortoise import Tortoise

from app.config import get_settings
from app.core.database import db_manager
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import JWTHandler, TokenScope, decode_token
from app.core.tenant_manager import (
    get_tenant_from_context,
)
from app.models.core import User
from app.models.tenant import TenantUser
from app.repositories.user_repositories import UserRepository

settings = get_settings()
security = HTTPBearer()


async def get_current_user_core(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Dependency to get current platform-level user from JWT token
    Validates token and checks scope="core"

    Returns:
        User object

    Raises:
        AuthenticationError: If token is invalid or user doesn't exist
        AuthorizationError: If token scope is not "core"
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)

        scope = JWTHandler.extract_scope(payload)
        if scope != TokenScope.CORE:
            raise AuthorizationError(
                f"Token scope '{scope}' is not valid for this endpoint. Required: 'core'"
            )

        user_id = JWTHandler.extract_user_id(payload)

        user_repo = UserRepository()
        user = await user_repo.get_by_id(user_id)

        if not user:
            raise AuthenticationError("User not found")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user

    except AuthenticationError:
        raise
    except Exception as e:
        raise AuthenticationError(f"Invalid authentication: {str(e)}") from e


async def get_current_user_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    x_tenant_header: str | None = Depends(get_tenant_from_context),
) -> tuple[TenantUser, str]:
    """
    Dependency to get current tenant user from JWT token
    Validates token, checks scope="tenant"
    Uses tenant_id from token (not from header)

    Returns:
        Tuple of (TenantUser object, tenant_id)

    Raises:
        AuthenticationError: If token is invalid or user doesn't exist
        AuthorizationError: If token scope is not "tenant"
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)

        scope = JWTHandler.extract_scope(payload)
        if scope != TokenScope.TENANT:
            raise AuthorizationError(
                f"Token scope '{scope}' is not valid for this endpoint. Required: 'tenant'"
            )

        tenant_id = JWTHandler.extract_tenant_id(payload)
        if not tenant_id:
            raise AuthenticationError("Tenant ID is missing from token")

        if x_tenant_header and x_tenant_header != tenant_id:
            raise AuthorizationError(
                f"X-Tenant-Id header '{x_tenant_header}' does not match token tenant '{tenant_id}'"
            )

        user_id = JWTHandler.extract_user_id(payload)

        await db_manager.init_tenant_db(tenant_id)

        connection_name = db_manager.get_tenant_connection_name(tenant_id)
        conn = Tortoise.get_connection(connection_name)

        user = await TenantUser.filter(id=user_id).using_db(conn).first()

        if not user:
            raise AuthenticationError("User not found in tenant")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user, tenant_id

    except (AuthenticationError, AuthorizationError):
        raise
    except Exception as e:
        raise AuthenticationError(f"Invalid authentication: {str(e)}") from e


async def get_tenant_id(
    x_tenant: str | None = Header(None, alias=settings.TENANT_HEADER_NAME),
) -> str | None:
    """
    Dependency to extract tenant ID from X-Tenant-Id header
    Returns None if header is not present (optional tenant)
    """
    return x_tenant
