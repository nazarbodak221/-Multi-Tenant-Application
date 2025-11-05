from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: str
    updated_at: str
    owned_organizations: List[Dict[str, Any]] = []


class TenantUserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    is_owner: bool = False
    is_active: bool
    metadata: Dict[str, Any] = {}
    created_at: str
    updated_at: str


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
