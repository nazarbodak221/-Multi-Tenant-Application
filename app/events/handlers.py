"""
Event handlers for application events
"""
import logging
from typing import Dict, Any
from app.events.emitter import EventType
from app.core.database import db_manager
from app.models.tenant import TenantUser
from app.core.security import hash_password

logger = logging.getLogger(__name__)


async def handle_organization_created(data: Dict[str, Any]):
    """
    Handle organization.created event
    Syncs organization owner to tenant database as owner user
    
    Args:
        data: Event data containing organization_id, owner_id, owner_email
    """
    try:
        organization_id = data.get("organization_id")
        owner_id = data.get("owner_id")
        owner_email = data.get("owner_email")
        
        if not all([organization_id, owner_id, owner_email]):
            logger.warning(
                "Missing required data for organization.created event",
                extra={"data": data}
            )
            return
        
        tenant_id = str(organization_id)
        
        logger.info(
            f"Syncing owner to tenant database",
            extra={
                "organization_id": organization_id,
                "tenant_id": tenant_id,
                "owner_id": owner_id
            }
        )
        
        await db_manager.init_tenant_db(tenant_id)
        
        TenantUserModel = db_manager.get_tenant_model(tenant_id, TenantUser)
        
        existing_owner = await TenantUserModel.get_or_none(email=owner_email)
        
        if existing_owner:
            logger.info(
                f"Owner already exists in tenant, updating to owner",
                extra={"tenant_id": tenant_id, "user_id": str(existing_owner.id)}
            )
            existing_owner.is_owner = True
            await existing_owner.save()
            return
        
        # Create owner user in tenant database
        default_password = hash_password("changeme123")  # Should be changed on first login
        
        owner_user = await TenantUserModel.create(
            email=owner_email,
            hashed_password=default_password,
            full_name=None,
            is_owner=True,
            is_active=True
        )
        
        logger.info(
            f"Owner synced to tenant database",
            extra={
                "tenant_id": tenant_id,
                "user_id": str(owner_user.id),
                "email": owner_email
            }
        )
        
    except Exception as e:
        logger.error(
            "Error handling organization.created event",
            exc_info=True,
            extra={"data": data, "error": str(e)}
        )
        # Don't raise - event handlers should not break the main flow
        raise


async def handle_organization_updated(data: Dict[str, Any]):
    """
    Handle organization.updated event
    
    Args:
        data: Event data
    """
    logger.info("Organization updated", extra={"data": data})


async def handle_organization_deleted(data: Dict[str, Any]):
    """
    Handle organization.deleted event
    
    Args:
        data: Event data
    """
    logger.info("Organization deleted", extra={"data": data})


def register_handlers():
    """Register all event handlers"""
    from app.events.emitter import event_emitter
    
    event_emitter.on(EventType.ORGANIZATION_CREATED, handle_organization_created)
    event_emitter.on(EventType.ORGANIZATION_UPDATED, handle_organization_updated)
    event_emitter.on(EventType.ORGANIZATION_DELETED, handle_organization_deleted)
    
    logger.info("Event handlers registered")

