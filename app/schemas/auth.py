from typing import Optional

from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool


class TenantUserResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_owner: bool = False
    is_active: bool


class AuthResponse(BaseModel):
    user: dict
    access_token: str
    token_type: str = "bearer"
    scope: str
    tenant_id: Optional[str] = None
