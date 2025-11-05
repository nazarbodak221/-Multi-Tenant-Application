from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from tortoise import fields, models


class TenantUser(models.Model):
    """
    Tenant-specific user model.
    Each tenant has isolated user data.
    """

    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    hashed_password = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=50, null=True)
    avatar_url = fields.CharField(max_length=500, null=True)
    is_owner = fields.BooleanField(default=False)
    is_active = fields.BooleanField(default=True)
    metadata = fields.JSONField(default=dict)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"

    def __str__(self):
        return f"TenantUser({self.email})"


class TenantUser_Pydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    is_owner: bool
    is_active: bool
    metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class TenantUserIn_Pydantic(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    email: str
    password: str
    full_name: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
