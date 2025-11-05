from fastapi import HTTPException, status


class BaseApplicationException(HTTPException):
    """Base exception for application-specific errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: dict = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)


class NotFoundError(BaseApplicationException):
    """Resource not found"""
    
    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f" with id: {identifier}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=message
        )


class ValidationError(BaseApplicationException):
    """Validation error"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail
        )


class AuthenticationError(BaseApplicationException):
    """Authentication failed"""
    
    def __init__(self, detail: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseApplicationException):
    """Authorization failed - user doesn't have permission"""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class TenantNotFoundError(BaseApplicationException):
    """Tenant not found or not accessible"""
    
    def __init__(self, tenant_id: str = None):
        detail = "Tenant not found"
        if tenant_id:
            detail += f": {tenant_id}"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        )


class TenantAccessError(BaseApplicationException):
    """User doesn't have access to this tenant"""
    
    def __init__(self, tenant_id: str = None):
        detail = "Access denied to tenant"
        if tenant_id:
            detail += f": {tenant_id}"
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DatabaseError(BaseApplicationException):
    """Database operation failed"""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ConflictError(BaseApplicationException):
    """Resource conflict (e.g., duplicate entry)"""
    
    def __init__(self, detail: str = "Resource conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class BadRequestError(BaseApplicationException):
    """Bad request error"""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )

