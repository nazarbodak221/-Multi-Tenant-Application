from typing import Optional

from pydantic import BaseModel


class CreateOrganizationRequest(BaseModel):
    name: str
    slug: Optional[str] = None


class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    database_name: str
    owner_id: str
    is_active: bool
    created_at: str
    updated_at: Optional[str] = None
