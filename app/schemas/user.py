from typing import Any

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    is_active: bool
    created_at: str
    updated_at: str
    owned_organizations: list[dict[str, Any]] = []


class TenantUserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    is_owner: bool = False
    is_active: bool
    metadata: dict[str, Any] = {}
    created_at: str
    updated_at: str


class UpdateProfileRequest(BaseModel):
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    metadata: dict[str, Any] | None = None
