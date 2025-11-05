from typing import Optional, Tuple
from uuid import UUID

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings
from app.core.database import db_manager
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import JWTHandler, TokenScope, decode_token
from app.core.tenant_manager import TenantContext, require_tenant_from_context
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
        raise AuthenticationError(f"Invalid authentication: {str(e)}")


async def get_current_user_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    tenant_id: str = Depends(require_tenant_from_context),
) -> Tuple[TenantUser, str]:
    """
    Dependency to get current tenant user from JWT token
    Validates token, checks scope="tenant" and tenant_id match

    Returns:
        Tuple of (TenantUser object, tenant_id)

    Raises:
        AuthenticationError: If token is invalid or user doesn't exist
        AuthorizationError: If token scope is not "tenant" or tenant_id doesn't match
    """
    token = credentials.credentials

    try:
        payload = decode_token(token)

        scope = JWTHandler.extract_scope(payload)
        if scope != TokenScope.TENANT:
            raise AuthorizationError(
                f"Token scope '{scope}' is not valid for this endpoint. Required: 'tenant'"
            )

        token_tenant_id = JWTHandler.extract_tenant_id(payload)
        if not token_tenant_id:
            raise AuthenticationError("Tenant ID is missing from token")

        if token_tenant_id != tenant_id:
            raise AuthorizationError(
                f"Token tenant ID '{token_tenant_id}' does not match request tenant '{tenant_id}'"
            )

        user_id = JWTHandler.extract_user_id(payload)

        await db_manager.init_tenant_db(tenant_id)

        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)

        user = await TenantUserModel.get_or_none(id=user_id)

        if not user:
            raise AuthenticationError("User not found in tenant")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        return user, tenant_id

    except (AuthenticationError, AuthorizationError):
        raise
    except Exception as e:
        raise AuthenticationError(f"Invalid authentication: {str(e)}")


async def get_tenant_id(
    x_tenant: Optional[str] = Header(None, alias=settings.TENANT_HEADER_NAME)
) -> Optional[str]:
    """
    Dependency to extract tenant ID from X-Tenant-Id header
    Returns None if header is not present (optional tenant)
    """
    return x_tenant
