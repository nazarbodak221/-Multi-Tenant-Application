"""
Event emitter for application events
Simple event bus implementation for async event handling
"""

import asyncio
import logging
from enum import Enum
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Event types"""

    ORGANIZATION_CREATED = "organization.created"
    ORGANIZATION_UPDATED = "organization.updated"
    ORGANIZATION_DELETED = "organization.deleted"
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"


class EventEmitter:
    """
    Simple async event emitter
    Supports multiple listeners per event type
    """

    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def on(self, event_type: str, handler: Callable):
        """
        Register event handler

        Args:
            event_type: Event type string
            handler: Async function to handle event
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []

        self._listeners[event_type].append(handler)
        logger.debug(f"Registered handler for event: {event_type}")

    def off(self, event_type: str, handler: Callable):
        """
        Unregister event handler

        Args:
            event_type: Event type string
            handler: Handler to remove
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(handler)
                logger.debug(f"Unregistered handler for event: {event_type}")
            except ValueError:
                pass

    async def emit(self, event_type: str, data: Dict[str, Any] = None):
        """
        Emit event to all registered handlers

        Args:
            event_type: Event type string
            data: Event data dictionary
        """
        if data is None:
            data = {}

        if event_type not in self._listeners:
            logger.debug(f"No handlers for event: {event_type}")
            return

        logger.info(
            f"Emitting event: {event_type}",
            extra={"event_type": event_type, "data": data},
        )

        # Execute all handlers concurrently
        handlers = self._listeners[event_type]
        tasks = []

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    tasks.append(handler(data))
                else:
                    # Sync handler - run in executor
                    tasks.append(asyncio.to_thread(handler, data))
            except Exception as e:
                logger.error(
                    f"Error creating task for handler: {handler.__name__}",
                    exc_info=True,
                    extra={"event_type": event_type, "error": str(e)},
                )

        # Wait for all handlers to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Log any errors from handlers
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        f"Handler {handlers[i].__name__} raised exception",
                        exc_info=result,
                        extra={"event_type": event_type},
                    )

    def get_listeners(self, event_type: str) -> List[Callable]:
        """Get all listeners for event type"""
        return self._listeners.get(event_type, [])


event_emitter = EventEmitter()
