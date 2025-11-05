from typing import Optional
from uuid import UUID

from app.models.core import User
from app.models.tenant import TenantUser
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """Repository for core users"""

    def __init__(self):
        super().__init__(User)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return await self.get_by_field(email=email)

    async def create_user(
        self, email: str, hashed_password: str, full_name: Optional[str] = None
    ) -> User:
        """Create new user"""
        return await self.create(
            email=email, hashed_password=hashed_password, full_name=full_name
        )


class TenantUserRepository(BaseRepository[TenantUser]):
    """Repository for tenant users"""

    def __init__(self):
        super().__init__(TenantUser)

    async def get_by_email(self, email: str) -> Optional[TenantUser]:
        """Get tenant user by email"""
        return await self.get_by_field(email=email)

    async def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        is_owner: bool = False,
        **extra_data
    ) -> TenantUser:
        """Create new tenant user"""
        return await self.create(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_owner=is_owner,
            **extra_data
        )

    async def update_profile(
        self, user_id: UUID, **profile_data
    ) -> Optional[TenantUser]:
        """Update user profile"""
        return await self.update(user_id, **profile_data)
