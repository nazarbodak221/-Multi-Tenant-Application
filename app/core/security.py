import logging
import warnings
from datetime import datetime, timedelta
from typing import Any, Dict, Optional
from uuid import UUID

import bcrypt
from jose import JWTError, jwt

from app.config import get_settings
from app.core.exceptions import AuthenticationError, ValidationError

settings = get_settings()

logging.getLogger("passlib.handlers.bcrypt").setLevel(logging.ERROR)


class PasswordHasher:
    """Password hashing utilities using bcrypt"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt, truncating to 72 bytes if needed."""
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode('utf-8')

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash, truncating to 72 bytes if needed.
        """
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)


class TokenScope:
    CORE = "core"
    TENANT = "tenant"


class JWTHandler:
    """JWT token creation and validation"""

    @staticmethod
    def create_access_token(
        data: Dict[str, Any], expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token

        Args:
            data: Dictionary containing token payload (user_id, email, scope, tenant_id)
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({"exp": expire, "iat": datetime.utcnow(), "type": "access"})

        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_token_for_core_user(
        user_id: UUID, email: str, expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a token for platform-level user

        Args:
            user_id: User UUID
            email: User email
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token string
        """
        payload = {
            "user_id": str(user_id),
            "email": email,
            "scope": TokenScope.CORE,
            "tenant_id": None,
        }
        return JWTHandler.create_access_token(payload, expires_delta)

    @staticmethod
    def create_token_for_tenant_user(
        user_id: UUID,
        email: str,
        tenant_id: str,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """
        Create a token for tenant user

        Args:
            user_id: User UUID
            email: User email
            tenant_id: Tenant ID
            expires_delta: Optional expiration time delta

        Returns:
            Encoded JWT token string
        """
        payload = {
            "user_id": str(user_id),
            "email": email,
            "scope": TokenScope.TENANT,
            "tenant_id": tenant_id,
        }
        return JWTHandler.create_access_token(payload, expires_delta)

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """
        Decode and validate a JWT token

        Args:
            token: JWT token string

        Returns:
            Decoded token payload

        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")

    @staticmethod
    def get_token_payload(token: str) -> Dict[str, Any]:
        """
        Get token payload with validation
        Alias for decode_token for clarity

        Args:
            token: JWT token string

        Returns:
            Decoded token payload
        """
        return JWTHandler.decode_token(token)

    @staticmethod
    def validate_token_scope(
        payload: Dict[str, Any], required_scope: str, tenant_id: Optional[str] = None
    ) -> bool:
        """
        Validate token scope and tenant access

        Args:
            payload: Decoded token payload
            required_scope: Required scope (core or tenant)
            tenant_id: Optional tenant ID to validate access

        Returns:
            True if validation passes

        Raises:
            AuthenticationError: If validation fails
        """
        token_scope = payload.get("scope")

        if token_scope != required_scope:
            raise AuthenticationError(
                f"Token scope '{token_scope}' does not match required scope '{required_scope}'"
            )

        if required_scope == TokenScope.TENANT:
            token_tenant_id = payload.get("tenant_id")

            if not token_tenant_id:
                raise AuthenticationError("Tenant ID is required for tenant scope")

            if tenant_id and token_tenant_id != tenant_id:
                raise AuthenticationError(
                    f"Token tenant ID '{token_tenant_id}' does not match required tenant '{tenant_id}'"
                )

        return True

    @staticmethod
    def extract_user_id(payload: Dict[str, Any]) -> UUID:
        user_id_str = payload.get("user_id")
        if not user_id_str:
            raise ValidationError("user_id is missing from token")

        try:
            return UUID(user_id_str)
        except ValueError:
            raise ValidationError(f"Invalid user_id format: {user_id_str}")

    @staticmethod
    def extract_email(payload: Dict[str, Any]) -> str:
        email = payload.get("email")
        if not email:
            raise ValidationError("email is missing from token")
        return email

    @staticmethod
    def extract_scope(payload: Dict[str, Any]) -> str:
        scope = payload.get("scope")
        if not scope:
            raise ValidationError("scope is missing from token")
        return scope

    @staticmethod
    def extract_tenant_id(payload: Dict[str, Any]) -> Optional[str]:
        return payload.get("tenant_id")
def hash_password(password: str) -> str:
    return PasswordHasher.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return PasswordHasher.verify_password(plain_password, hashed_password)


def create_core_token(
    user_id: UUID, email: str, expires_delta: Optional[timedelta] = None
) -> str:
    return JWTHandler.create_token_for_core_user(user_id, email, expires_delta)


def create_tenant_token(
    user_id: UUID, email: str, tenant_id: str, expires_delta: Optional[timedelta] = None
) -> str:
    return JWTHandler.create_token_for_tenant_user(
        user_id, email, tenant_id, expires_delta
    )


def decode_token(token: str) -> Dict[str, Any]:
    return JWTHandler.decode_token(token)
