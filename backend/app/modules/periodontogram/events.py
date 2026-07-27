"""Event handlers consumed by the periodontogram module.

Opens its own ``async_session_maker`` session because these are
called from the event bus outside the request lifecycle.
"""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from sqlalchemy import select

from app.database import async_session_maker

from .constants import PERIO_TEETH
from .models import PeriodontogramTooth
from .service import PeriodontogramService

logger = logging.getLogger(__name__)


async def on_odontogram_treatment_performed(data: dict[str, Any]) -> None:
    """Refresh active draft's is_present/is_implant flags.

    When an odontogram treatment that changes the physical state of a
    tooth (extraction, implant) is performed, update the corresponding
    flags on any active periodontogram draft for that patient.
    """
    patient_id = data.get("patient_id")
    tooth_number = data.get("tooth_number")
    treatment_type = data.get("treatment_type")
    clinic_id = data.get("clinic_id")

    if not all([patient_id, tooth_number, treatment_type, clinic_id]):
        logger.warning("periodontogram: incomplete treatment.performed payload: %s", data)
        return

    if tooth_number not in PERIO_TEETH:
        return

    async with async_session_maker() as db:
        draft = await PeriodontogramService.get_active_draft(
            db, UUID(clinic_id), UUID(patient_id)
        )
        if not draft:
            return

        perio_tooth = (
            await db.execute(
                select(PeriodontogramTooth).where(
                    PeriodontogramTooth.snapshot_id == draft.id,
                    PeriodontogramTooth.tooth_number == tooth_number,
                )
            )
        ).scalar_one_or_none()

        if not perio_tooth:
            return

        if treatment_type == "extraction":
            perio_tooth.is_present = False
            perio_tooth.is_implant = False
        elif treatment_type == "implant":
            perio_tooth.is_implant = True

        await db.flush()
        logger.info(
            "periodontogram: refreshed tooth %s flags (present=%s, implant=%s) for draft %s",
            tooth_number, perio_tooth.is_present, perio_tooth.is_implant, draft.id,
        )


async def on_patient_archived(data: dict[str, Any]) -> None:
    """Discard any active draft when its patient is archived."""
    patient_id = data.get("patient_id")
    clinic_id = data.get("clinic_id")

    if not all([patient_id, clinic_id]):
        return

    async with async_session_maker() as db:
        draft = await PeriodontogramService.get_active_draft(
            db, UUID(clinic_id), UUID(patient_id)
        )
        if not draft:
            return

        await db.delete(draft)
        await db.flush()
        logger.info(
            "periodontogram: discarded draft %s for archived patient %s",
            draft.id, patient_id,
        )
