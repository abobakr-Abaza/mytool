from uuid import UUID

from pydantic import BaseModel, Field

from app.core.agents import AgentContext, Tool, ToolCategory

from .service import PeriodontogramService


class SnapshotArgs(BaseModel):
    patient_id: UUID = Field(description="UUID of the patient whose snapshot to retrieve")


class SnapshotIdArgs(BaseModel):
    snapshot_id: UUID = Field(description="UUID of the periodontogram snapshot")


async def _get_snapshot(ctx: AgentContext, params: SnapshotArgs) -> dict:
    return await PeriodontogramService.get_snapshot(ctx.db, ctx.clinic_id, params.patient_id)


async def _get_indices(ctx: AgentContext, params: SnapshotIdArgs) -> dict:
    snapshot = await PeriodontogramService.get_snapshot(ctx.db, ctx.clinic_id, params.snapshot_id)
    return snapshot.get("indices", {}) if isinstance(snapshot, dict) else {}


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="periodontogram_get_latest_snapshot",
            description="Get the latest closed periodontogram snapshot for a patient with full tooth and site data",
            parameters=SnapshotArgs,
            handler=_get_snapshot,
            category=ToolCategory.READ,
            exposes_free_text=True,
            permissions=["periodontogram.read"],
        ),
        Tool(
            name="periodontogram_get_indices",
            description="Get computed SEPA indices (BoP%, PI%, mean CAL, deep pockets) for a periodontogram snapshot",
            parameters=SnapshotIdArgs,
            handler=_get_indices,
            category=ToolCategory.READ,
            permissions=["periodontogram.read"],
        ),
    ]
