"""
Unit tests for security utilities
"""

from uuid import UUID, uuid4

import pytest

from app.core.exceptions import AuthenticationError, ValidationError
from app.core.security import (
    JWTHandler,
    PasswordHasher,
    TokenScope,
    create_core_token,
    create_tenant_token,
    decode_token,
    hash_password,
    verify_password,
)


class TestPasswordHasher:
    """Tests for password hashing"""

    def test_hash_password(self):
        """Test password hashing"""
        password = "testpassword123"
        hashed = PasswordHasher.hash_password(password)

        assert hashed != password
        assert len(hashed) > 0
        assert hashed.startswith("$2b$")  # bcrypt format

    def test_verify_password_correct(self):
        """Test password verification with correct password"""
        password = "testpassword123"
        hashed = PasswordHasher.hash_password(password)

        assert PasswordHasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test password verification with incorrect password"""
        password = "testpassword123"
        wrong_password = "wrongpassword"
        hashed = PasswordHasher.hash_password(password)

        assert PasswordHasher.verify_password(wrong_password, hashed) is False

    def test_hash_password_different_hashes(self):
        """Test that same password produces different hashes (due to salt)"""
        password = "testpassword123"
        hashed1 = PasswordHasher.hash_password(password)
        hashed2 = PasswordHasher.hash_password(password)

        # Hashes should be different (bcrypt uses random salt)
        assert hashed1 != hashed2
        # But both should verify correctly
        assert PasswordHasher.verify_password(password, hashed1) is True
        assert PasswordHasher.verify_password(password, hashed2) is True


class TestJWTHandler:
    """Tests for JWT token handling"""

    def test_create_core_token(self):
        """Test creating token for core user"""
        user_id = uuid4()
        email = "test@example.com"

        token = JWTHandler.create_token_for_core_user(user_id, email)

        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_tenant_token(self):
        """Test creating token for tenant user"""
        user_id = uuid4()
        email = "test@example.com"
        tenant_id = "123"

        token = JWTHandler.create_token_for_tenant_user(user_id, email, tenant_id)

        assert token is not None
        assert isinstance(token, str)

    def test_decode_token_core(self):
        """Test decoding core token"""
        user_id = uuid4()
        email = "test@example.com"
        token = create_core_token(user_id, email)

        payload = JWTHandler.decode_token(token)

        assert payload["user_id"] == str(user_id)
        assert payload["email"] == email
        assert payload["scope"] == TokenScope.CORE
        assert payload["tenant_id"] is None
        assert "exp" in payload
        assert "iat" in payload

    def test_decode_token_tenant(self):
        """Test decoding tenant token"""
        user_id = uuid4()
        email = "test@example.com"
        tenant_id = "123"
        token = create_tenant_token(user_id, email, tenant_id)

        payload = JWTHandler.decode_token(token)

        assert payload["user_id"] == str(user_id)
        assert payload["email"] == email
        assert payload["scope"] == TokenScope.TENANT
        assert payload["tenant_id"] == tenant_id

    def test_decode_invalid_token(self):
        """Test decoding invalid token raises exception"""
        invalid_token = "invalid.token.here"

        with pytest.raises(AuthenticationError):
            JWTHandler.decode_token(invalid_token)

    def test_extract_user_id(self):
        """Test extracting user_id from payload"""
        user_id = uuid4()
        payload = {"user_id": str(user_id)}

        extracted = JWTHandler.extract_user_id(payload)

        assert extracted == user_id

    def test_extract_user_id_missing(self):
        """Test extracting user_id when missing raises exception"""
        payload = {}

        with pytest.raises(ValidationError):
            JWTHandler.extract_user_id(payload)

    def test_extract_email(self):
        """Test extracting email from payload"""
        email = "test@example.com"
        payload = {"email": email}

        extracted = JWTHandler.extract_email(payload)

        assert extracted == email

    def test_extract_scope(self):
        """Test extracting scope from payload"""
        payload = {"scope": TokenScope.CORE}

        extracted = JWTHandler.extract_scope(payload)

        assert extracted == TokenScope.CORE

    def test_extract_tenant_id(self):
        """Test extracting tenant_id from payload"""
        tenant_id = "123"
        payload = {"tenant_id": tenant_id}

        extracted = JWTHandler.extract_tenant_id(payload)

        assert extracted == tenant_id

    def test_validate_token_scope_core(self):
        """Test validating core token scope"""
        payload = {"scope": TokenScope.CORE, "tenant_id": None}

        result = JWTHandler.validate_token_scope(payload, TokenScope.CORE)

        assert result is True

    def test_validate_token_scope_tenant(self):
        """Test validating tenant token scope"""
        payload = {"scope": TokenScope.TENANT, "tenant_id": "123"}

        result = JWTHandler.validate_token_scope(
            payload, TokenScope.TENANT, tenant_id="123"
        )

        assert result is True

    def test_validate_token_scope_mismatch(self):
        """Test validating token scope mismatch raises exception"""
        payload = {"scope": TokenScope.CORE, "tenant_id": None}

        with pytest.raises(AuthenticationError):
            JWTHandler.validate_token_scope(payload, TokenScope.TENANT)

    def test_validate_token_scope_tenant_mismatch(self):
        """Test validating tenant token with wrong tenant_id"""
        payload = {"scope": TokenScope.TENANT, "tenant_id": "123"}

        with pytest.raises(AuthenticationError):
            JWTHandler.validate_token_scope(payload, TokenScope.TENANT, tenant_id="456")
