from typing import Optional, List
from uuid import UUID
from app.models.core import Organization
from app.repositories.base import BaseRepository

class OrganizationRepository(BaseRepository[Organization]):
    """Repository for organizations"""
    
    def __init__(self):
        super().__init__(Organization)
    
    async def get_by_slug(self, slug: str) -> Optional[Organization]:
        """Get organization by slug"""
        return await self.get_by_field(slug=slug)
    
    async def get_by_owner(self, owner_id: UUID) -> List[Organization]:
        """Get all organizations owned by user"""
        return await self.get_all(owner_id=owner_id)
    
    async def create_organization(
        self,
        name: str,
        slug: str,
        owner_id: UUID,
        database_name: str
    ) -> Organization:
        """Create new organization"""
        return await self.create(
            name=name,
            slug=slug,
            owner_id=owner_id,
            database_name=database_name
        )