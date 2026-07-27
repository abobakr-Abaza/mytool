from app.core.agents.tools import Tool

from .service import PeriodontogramService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="periodontogram_get_latest_snapshot",
            description="Get the latest closed periodontogram snapshot for a patient with full tooth and site data",
            category="READ",
            exposes_free_text=True,
            permissions=["periodontogram.read"],
            service_method=PeriodontogramService.get_snapshot,
        ),
        Tool(
            name="periodontogram_get_indices",
            description="Get computed SEPA indices (BoP%, PI%, mean CAL, deep pockets) for a periodontogram snapshot",
            category="READ",
            permissions=["periodontogram.read"],
            service_method=PeriodontogramService.get_snapshot,
        ),
    ]
