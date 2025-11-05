import logging
from typing import Any

from app.events.emitter import EventEmitter, EventType, event_emitter

logger = logging.getLogger(__name__)


async def handle_organization_created(data: dict[str, Any]) -> None:
    logger.info("organization.created event received", extra={"data": data})


async def handle_organization_updated(data: dict[str, Any]) -> None:
    logger.info("organization.updated event received", extra={"data": data})


async def handle_organization_deleted(data: dict[str, Any]) -> None:
    logger.info("organization.deleted event received", extra={"data": data})


def register_handlers(emitter: EventEmitter | None = None) -> None:
    target = emitter or event_emitter
    target.on(EventType.ORGANIZATION_CREATED, handle_organization_created)
    target.on(EventType.ORGANIZATION_UPDATED, handle_organization_updated)
    target.on(EventType.ORGANIZATION_DELETED, handle_organization_deleted)
