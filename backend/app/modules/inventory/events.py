"""Event handlers for the inventory module.

Registered via :meth:`InventoryModule.get_event_handlers`.
"""

from app.core.events import EventType

__all__ = [
    "EVENT_HANDLERS",
]

EVENT_HANDLERS: dict[str, str] = {}
