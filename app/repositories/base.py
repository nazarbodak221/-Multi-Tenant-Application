from typing import TypeVar, Generic, Optional, List, Type
from uuid import UUID
from tortoise.models import Model
from tortoise.exceptions import DoesNotExist

ModelType = TypeVar("ModelType", bound=Model)

class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations
    Follows repository pattern for data access abstraction
    """
    
    def __init__(self, model: Type[ModelType]):
        self.model = model
    
    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Get entity by ID"""
        try:
            return await self.model.get(id=id)
        except DoesNotExist:
            return None
    
    async def get_by_field(self, **filters) -> Optional[ModelType]:
        """Get entity by field filters"""
        try:
            return await self.model.get(**filters)
        except DoesNotExist:
            return None
    
    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[ModelType]:
        """Get all entities with pagination"""
        query = self.model.filter(**filters)
        return await query.offset(skip).limit(limit).all()
    
    async def create(self, **data) -> ModelType:
        """Create new entity"""
        instance = self.model(**data)
        await instance.save()
        return instance
    
    async def update(self, id: UUID, **data) -> Optional[ModelType]:
        """Update entity by ID"""
        instance = await self.get_by_id(id)
        if instance:
            await instance.update_from_dict(data)
            await instance.save()
        return instance
    
    async def delete(self, id: UUID) -> bool:
        """Delete entity by ID"""
        instance = await self.get_by_id(id)
        if instance:
            await instance.delete()
            return True
        return False
    
    async def exists(self, **filters) -> bool:
        """Check if entity exists"""
        return await self.model.exists(**filters)