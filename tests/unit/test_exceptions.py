"""
Unit tests for custom exceptions
"""

import pytest
from fastapi import status

from app.core.exceptions import (AuthenticationError, AuthorizationError,
                                 BadRequestError, ConflictError, DatabaseError,
                                 NotFoundError, TenantAccessError,
                                 TenantNotFoundError, ValidationError)


class TestExceptions:
    """Tests for custom exceptions"""

    def test_not_found_error(self):
        """Test NotFoundError"""
        error = NotFoundError("User", "123")

        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert "User" in error.detail
        assert "123" in error.detail

    def test_validation_error(self):
        """Test ValidationError"""
        error = ValidationError("Invalid input")

        assert error.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert error.detail == "Invalid input"

    def test_authentication_error(self):
        """Test AuthenticationError"""
        error = AuthenticationError("Invalid credentials")

        assert error.status_code == status.HTTP_401_UNAUTHORIZED
        assert error.detail == "Invalid credentials"
        assert "WWW-Authenticate" in error.headers

    def test_authorization_error(self):
        """Test AuthorizationError"""
        error = AuthorizationError("Access denied")

        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert error.detail == "Access denied"

    def test_tenant_not_found_error(self):
        """Test TenantNotFoundError"""
        error = TenantNotFoundError("123")

        assert error.status_code == status.HTTP_404_NOT_FOUND
        assert "123" in error.detail

    def test_tenant_access_error(self):
        """Test TenantAccessError"""
        error = TenantAccessError("123")

        assert error.status_code == status.HTTP_403_FORBIDDEN
        assert "123" in error.detail

    def test_database_error(self):
        """Test DatabaseError"""
        error = DatabaseError("Connection failed")

        assert error.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert error.detail == "Connection failed"

    def test_conflict_error(self):
        """Test ConflictError"""
        error = ConflictError("Resource already exists")

        assert error.status_code == status.HTTP_409_CONFLICT
        assert error.detail == "Resource already exists"

    def test_bad_request_error(self):
        """Test BadRequestError"""
        error = BadRequestError("Invalid request")

        assert error.status_code == status.HTTP_400_BAD_REQUEST
        assert error.detail == "Invalid request"
