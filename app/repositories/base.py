from typing import Generic, TypeVar, cast
from uuid import UUID

from tortoise.exceptions import DoesNotExist
from tortoise.models import Model

ModelType = TypeVar("ModelType", bound=Model)


class BaseRepository(Generic[ModelType]):
    """
    Base repository with common CRUD operations
    Follows repository pattern for data access abstraction
    """

    def __init__(self, model: type[ModelType]):
        self.model = model

    async def get_by_id(self, id: UUID) -> ModelType | None:
        """Get entity by ID"""
        try:
            return cast(ModelType, await self.model.get(id=id))
        except DoesNotExist:
            return None

    async def get_by_field(self, **filters) -> ModelType | None:
        """Get entity by field filters"""
        try:
            return cast(ModelType, await self.model.get(**filters))
        except DoesNotExist:
            return None

    async def get_all(self, skip: int = 0, limit: int = 100, **filters) -> list[ModelType]:
        """Get all entities with pagination"""
        query = self.model.filter(**filters)
        return cast(list[ModelType], await query.offset(skip).limit(limit).all())

    async def create(self, **data) -> ModelType:
        """Create new entity"""
        instance = self.model(**data)
        await instance.save()
        return cast(ModelType, instance)

    async def update(self, id: UUID, **data) -> ModelType | None:
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
        return cast(bool, await self.model.exists(**filters))
