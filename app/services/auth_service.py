from typing import Any

from tortoise import Tortoise

from app.core.database import db_manager
from app.core.exceptions import AuthenticationError, ConflictError
from app.core.security import (
    TokenScope,
    create_core_token,
    create_tenant_token,
    hash_password,
    verify_password,
)
from app.models.tenant import TenantUser
from app.repositories.user_repositories import TenantUserRepository, UserRepository


class AuthService:
    """Authentication service for core and tenant users"""

    def __init__(self):
        self.user_repo = UserRepository()
        self.tenant_user_repo = TenantUserRepository()

    async def register_core_user(
        self, email: str, password: str, full_name: str | None = None
    ) -> dict[str, Any]:
        """
        Register a new platform-level user

        Args:
            email: User email
            password: Plain text password
            full_name: Optional full name

        Returns:
            Dictionary with user data and access token

        Raises:
            ConflictError: If user with email already exists
        """
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ConflictError(f"User with email {email} already exists")

        hashed_password = hash_password(password)

        user = await self.user_repo.create_user(
            email=email, hashed_password=hashed_password, full_name=full_name
        )

        access_token = create_core_token(user_id=user.id, email=user.email)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_owner": None,
            },
            "access_token": access_token,
            "token_type": "bearer",
            "scope": TokenScope.CORE,
        }

    async def login_core_user(self, email: str, password: str) -> dict[str, Any]:
        """
        Login core user

        Args:
            email: User email
            password: Plain text password

        Returns:
            Dictionary with user data and access token

        Raises:
            AuthenticationError: If credentials are invalid
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        access_token = create_core_token(user_id=user.id, email=user.email)

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "is_owner": None,
            },
            "access_token": access_token,
            "token_type": "bearer",
            "scope": TokenScope.CORE,
        }

    async def register_tenant_user(
        self,
        tenant_id: str,
        email: str,
        password: str,
        full_name: str | None = None,
        is_owner: bool = False,
        **extra_data,
    ) -> dict[str, Any]:
        """
        Register a new tenant user

        Args:
            tenant_id: Tenant/organization ID
            email: User email
            password: Plain text password
            full_name: Optional full name
            is_owner: Whether user is tenant owner
            **extra_data: Additional user data (phone, avatar_url, etc.)

        Returns:
            Dictionary with user data and access token

        Raises:
            ConflictError: If user with email already exists in tenant
            NotFoundError: If tenant database doesn't exist
        """
        await db_manager.init_tenant_db(tenant_id)

        connection_name = db_manager.get_tenant_connection_name(tenant_id)
        conn = Tortoise.get_connection(connection_name)

        existing_user = await TenantUser.filter(email=email).using_db(conn).first()
        if existing_user:
            raise ConflictError(
                f"User with email {email} already exists in this tenant"
            )

        hashed_password = hash_password(password)

        user = await TenantUser.using_db(conn).create(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_owner=is_owner,
            **extra_data,
        )

        access_token = create_tenant_token(
            user_id=user.id, email=user.email, tenant_id=tenant_id
        )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_owner": user.is_owner,
                "is_active": user.is_active,
            },
            "access_token": access_token,
            "token_type": "bearer",
            "scope": TokenScope.TENANT,
            "tenant_id": tenant_id,
        }

    async def login_tenant_user(
        self, tenant_id: str, email: str, password: str
    ) -> dict[str, Any]:
        """
        Login tenant user

        Args:
            tenant_id: Tenant/organization ID
            email: User email
            password: Plain text password

        Returns:
            Dictionary with user data and access token

        Raises:
            AuthenticationError: If credentials are invalid
            NotFoundError: If tenant database doesn't exist
        """
        await db_manager.init_tenant_db(tenant_id)

        connection_name = db_manager.get_tenant_connection_name(tenant_id)
        conn = Tortoise.get_connection(connection_name)

        user = await TenantUser.filter(email=email).using_db(conn).first()
        if not user:
            raise AuthenticationError("Invalid email or password")

        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        if not user.is_active:
            raise AuthenticationError("User account is inactive")

        access_token = create_tenant_token(
            user_id=user.id, email=user.email, tenant_id=tenant_id
        )

        return {
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "is_owner": user.is_owner,
                "is_active": user.is_active,
            },
            "access_token": access_token,
            "token_type": "bearer",
            "scope": TokenScope.TENANT,
            "tenant_id": tenant_id,
        }


auth_service = AuthService()
