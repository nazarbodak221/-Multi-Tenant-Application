import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


class EventType:
    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"


class EventEmitter:
    def __init__(self) -> None:
        self._listeners: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_type: str, handler: EventHandler) -> None:
        self._listeners[event_type].append(handler)
        logger.debug("Registered handler", extra={"event": event_type, "handler": handler})

    def off(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._listeners and handler in self._listeners[event_type]:
            self._listeners[event_type].remove(handler)
            logger.debug("Unregistered handler", extra={"event": event_type, "handler": handler})

    async def emit(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        if event_type not in self._listeners:
            logger.debug("No handlers registered", extra={"event": event_type})
            return

        payload = data or {}
        handlers = list(self._listeners[event_type])

        logger.debug(
            "Emitting event",
            extra={"event": event_type, "handlers": len(handlers), "data": payload},
        )

        await asyncio.gather(
            *(self._safe_execute(handler, event_type, payload) for handler in handlers),
            return_exceptions=True,
        )

    async def _safe_execute(
        self, handler: EventHandler, event_type: str, data: dict[str, Any]
    ) -> None:
        try:
            await handler(data)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error(
                "Event handler raised exception",
                exc_info=True,
                extra={"event": event_type, "handler": handler, "error": str(exc)},
            )

    def get_listeners(self, event_type: str) -> list[EventHandler]:
        return list(self._listeners.get(event_type, []))


event_emitter = EventEmitter()
