from __future__ import annotations

from fastapi import APIRouter

from app.core.plugins import BaseModule

from .public_router import public_router


class BookingModule(BaseModule):
    manifest = {
        "name": "booking",
        "version": "0.1.0",
        "summary": "Public online appointment booking.",
        "author": "LaminarDent Core Team",
        "license": "BSL-1.1",
        "category": "official",
        "depends": ["agenda", "patients", "schedules"],
        "installable": True,
        "auto_install": True,
        "removable": True,
        "role_permissions": {
            "admin": ["*"],
            "receptionist": ["manage"],
        },
        "frontend": {
            "layer_path": "frontend",
        },
    }

    def get_models(self) -> list:
        return []

    def get_router(self) -> APIRouter:
        return public_router

    def get_permissions(self) -> list[str]:
        return ["manage"]

    def get_event_handlers(self) -> dict:
        return {}

    def get_tools(self) -> list:
        return []
