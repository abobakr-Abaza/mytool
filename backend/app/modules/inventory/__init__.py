from __future__ import annotations

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .models import InventoryCategory, InventoryItem, InventoryMovement
from .router import router


class InventoryModule(BaseModule):
    manifest = {
        "name": "inventory",
        "version": "0.1.0",
        "summary": "Supplies & stock management with low-stock alerts.",
        "author": "LaminarDent Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": [],
        "installable": True,
        "auto_install": True,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "dentist": ["read", "write"],
            "assistant": ["read", "write"],
            "receptionist": ["read"],
        },
        "frontend": {
            "layer_path": "frontend",
            "navigation": [
                {
                    "label": "nav.inventory",
                    "icon": "i-lucide-package",
                    "to": "/inventory",
                    "permission": "inventory.read",
                    "order": 60,
                },
            ],
        },
    }

    def get_models(self) -> list:
        return [InventoryCategory, InventoryItem, InventoryMovement]

    def get_router(self) -> APIRouter:
        return router

    def get_permissions(self) -> list[str]:
        return ["read", "write", "delete"]

    def get_event_handlers(self) -> dict:
        return {}

    def get_tools(self) -> list:
        from .tools import get_tools
        return get_tools()
