from tortoise import fields, models
from tortoise.contrib.pydantic import pydantic_model_creator


class User(models.Model):
    """
    Core database user model.
    Stores platform-level users and organization owners.
    """

    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    hashed_password = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Relationships
    owned_organizations: fields.ReverseRelation["Organization"]

    class Meta:
        table = "users"

    def __str__(self):
        return f"User({self.email})"


class Organization(models.Model):
    """
    Organization (tenant) model in core database.
    Each organization gets its own database.
    """

    id = fields.UUIDField(pk=True)
    name = fields.CharField(max_length=255, unique=True, index=True)
    slug = fields.CharField(max_length=100, unique=True, index=True)
    database_name = fields.CharField(max_length=100, unique=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    # Relationships
    owner: fields.ForeignKeyRelation[User] = fields.ForeignKeyField(
        "models.User", related_name="owned_organizations"
    )

    class Meta:
        table = "organizations"

    def __str__(self):
        return f"Organization({self.name})"


# Pydantic models for serialization
User_Pydantic = pydantic_model_creator(User, name="User", exclude=("hashed_password",))
UserIn_Pydantic = pydantic_model_creator(User, name="UserIn", exclude_readonly=True)
Organization_Pydantic = pydantic_model_creator(Organization, name="Organization")
