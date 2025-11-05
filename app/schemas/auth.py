
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    is_active: bool
    is_owner: bool | None = None


class TenantUserResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    is_owner: bool = False
    is_active: bool


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
    scope: str
    tenant_id: str | None = None
