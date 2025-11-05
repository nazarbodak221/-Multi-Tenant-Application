from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


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


# Pydantic models
TenantUser_Pydantic = pydantic_model_creator(
    TenantUser, name="TenantUser", exclude=("hashed_password",)
)
TenantUserIn_Pydantic = pydantic_model_creator(
    TenantUser, name="TenantUserIn", exclude_readonly=True
)
