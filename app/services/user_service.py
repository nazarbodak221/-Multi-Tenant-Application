from typing import Optional, Dict, Any
from uuid import UUID
from app.repositories.user_repositories import UserRepository, TenantUserRepository
from app.core.database import db_manager
from app.core.exceptions import NotFoundError, ValidationError
from app.core.tenant_manager import TenantContext
from app.core.utils import format_datetime
from app.models.core import User
from app.models.tenant import TenantUser


class UserService:
    """Service for user profile management"""
    
    def __init__(self):
        self.user_repo = UserRepository()
        self.tenant_user_repo = TenantUserRepository()
    
    async def get_core_user_profile(
        self,
        user_id: UUID
    ) -> Dict[str, Any]:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        owned_orgs = await user.owned_organizations.all()
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "created_at": format_datetime(user.created_at),
            "updated_at": format_datetime(user.updated_at),
            "owned_organizations": [
                {
                    "id": str(org.id),
                    "name": org.name,
                    "slug": org.slug,
                    "is_active": org.is_active
                }
                for org in owned_orgs
            ]
        }
    
    async def update_core_user_profile(
        self,
        user_id: UUID,
        full_name: Optional[str] = None,
        **extra_data
    ) -> Dict[str, Any]:
        """
        Update core user profile
        
        Args:
            user_id: User UUID
            full_name: Optional full name
            **extra_data: Additional fields to update
            
        Returns:
            Dictionary with updated user profile data
            
        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If update data is invalid
        """
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise NotFoundError("User", str(user_id))
        
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        
        allowed_fields = {"full_name"}
        for key, value in extra_data.items():
            if key in allowed_fields:
                update_data[key] = value
        
        if not update_data:
            raise ValidationError("No valid fields to update")
        
        updated_user = await self.user_repo.update(user_id, **update_data)
        
        return {
            "id": str(updated_user.id),
            "email": updated_user.email,
            "full_name": updated_user.full_name,
            "is_active": updated_user.is_active,
            "updated_at": format_datetime(updated_user.updated_at)
        }
    
    async def get_tenant_user_profile(
        self,
        user_id: UUID,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        if not tenant_id:
            tenant_id = TenantContext.get_tenant()
            if not tenant_id:
                raise ValidationError("Tenant context is required")
        
=        await db_manager.init_tenant_db(tenant_id)
        
        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
        
        user = await TenantUserModel.get_or_none(id=user_id)
        if not user:
            raise NotFoundError("TenantUser", str(user_id))
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_owner": user.is_owner,
            "is_active": user.is_active,
            "metadata": user.metadata,
            "created_at": format_datetime(user.created_at),
            "updated_at": format_datetime(user.updated_at)
        }
    
    async def update_tenant_user_profile(
        self,
        user_id: UUID,
        tenant_id: Optional[str] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        avatar_url: Optional[str] = None,
        **extra_data
    ) -> Dict[str, Any]:
        """
        Update tenant user profile
        
        Args:
            user_id: User UUID
            tenant_id: Optional tenant ID (uses context if not provided)
            full_name: Optional full name
            phone: Optional phone number
            avatar_url: Optional avatar URL
            **extra_data: Additional fields (metadata, etc.)
            
        Returns:
            Dictionary with updated user profile data
            
        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If tenant context is missing or update data is invalid
        """
=        if not tenant_id:
            tenant_id = TenantContext.get_tenant()
            if not tenant_id:
                raise ValidationError("Tenant context is required")
        
        await db_manager.init_tenant_db(tenant_id)
        
        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
        
        user = await TenantUserModel.get_or_none(id=user_id)
        if not user:
            raise NotFoundError("TenantUser", str(user_id))
        
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if phone is not None:
            update_data["phone"] = phone
        if avatar_url is not None:
            update_data["avatar_url"] = avatar_url
        
        # Handle metadata update
        if "metadata" in extra_data:
            # Merge with existing metadata
            existing_metadata = user.metadata or {}
            new_metadata = extra_data.pop("metadata")
            if isinstance(new_metadata, dict):
                existing_metadata.update(new_metadata)
                update_data["metadata"] = existing_metadata
        
        # Add other extra data (filter to only allow safe fields)
        allowed_fields = {"full_name", "phone", "avatar_url", "metadata"}
        for key, value in extra_data.items():
            if key in allowed_fields:
                update_data[key] = value
        
        if not update_data:
            raise ValidationError("No valid fields to update")
        
        for key, value in update_data.items():
            setattr(user, key, value)
        await user.save()
        
        return {
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "phone": user.phone,
            "avatar_url": user.avatar_url,
            "is_owner": user.is_owner,
            "is_active": user.is_active,
            "metadata": user.metadata,
            "updated_at": format_datetime(user.updated_at)
        }


user_service = UserService()

