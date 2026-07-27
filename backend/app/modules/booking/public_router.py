from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, time, timedelta
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.models import Clinic
from app.core.schemas import ApiResponse
from app.database import get_db

logger = logging.getLogger(__name__)

public_router = APIRouter(prefix="/public/booking", tags=["public"])

SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{0,118}$")


class ClinicSlotResponse(BaseModel):
    professional_id: str
    professional_name: str
    date: str
    start_time: str
    end_time: str


class ClinicProfessionalResponse(BaseModel):
    id: str
    name: str
    specialty: str | None


class BookingRequest(BaseModel):
    clinic_slug: str = Field(..., max_length=120)
    professional_id: str = Field(..., max_length=36)
    date: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    patient_name: str = Field(..., max_length=200, min_length=1)
    patient_phone: str = Field(..., max_length=30, min_length=5)
    patient_email: str | None = Field(None, max_length=200)
    notes: str | None = Field(None, max_length=500)


class BookingResponse(BaseModel):
    appointment_id: str
    date: str
    start_time: str
    end_time: str
    professional_name: str


async def _resolve_clinic(db: AsyncSession, slug: str) -> Clinic:
    if not SLUG_PATTERN.match(slug):
        raise HTTPException(status_code=400, detail="Invalid clinic slug")
    result = await db.execute(select(Clinic).where(Clinic.slug == slug))
    clinic = result.scalar_one_or_none()
    if not clinic:
        raise HTTPException(status_code=404, detail="Clinic not found")
    return clinic


@public_router.get("/clinics/{slug}/professionals")
async def list_professionals(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    clinic = await _resolve_clinic(db, slug)

    from app.core.auth.models import ClinicMembership, User

    result = await db.execute(
        select(User)
        .join(ClinicMembership, ClinicMembership.user_id == User.id)
        .where(
            ClinicMembership.clinic_id == clinic.id,
            ClinicMembership.role.in_(["dentist", "hygienist"]),
            User.is_active == True,
        )
        .order_by(User.first_name, User.last_name)
    )
    users = result.scalars().all()

    return ApiResponse(data=[
        ClinicProfessionalResponse(
            id=str(u.id),
            name=u.full_name,
            specialty=getattr(u, "professional_id", None),
        ) for u in users
    ])


@public_router.get("/clinics/{slug}/slots")
async def get_available_slots(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    professional_id: UUID | None = Query(None),
    date_from: str | None = Query(None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    date_to: str | None = Query(None),
):
    from app.core.auth.models import ClinicMembership, User
    from app.modules.agenda.models import Appointment
    from app.modules.schedules.models import ScheduleOverride, WeeklySchedule

    clinic = await _resolve_clinic(db, slug)

    today = date.today()
    start = date.fromisoformat(date_from) if date_from else today
    end = date.fromisoformat(date_to) if date_to else min(start + timedelta(days=13), today + timedelta(days=60))

    if (end - start).days > 14:
        raise HTTPException(status_code=400, detail="Max 14-day range")

    q = select(User).join(ClinicMembership, ClinicMembership.user_id == User.id).where(
        ClinicMembership.clinic_id == clinic.id,
        ClinicMembership.role.in_(["dentist", "hygienist"]),
        User.is_active == True,
    )
    if professional_id:
        q = q.where(User.id == professional_id)
    result = await db.execute(q)
    users = result.scalars().all()

    prof_ids = [u.id for u in users]
    prof_names = {u.id: u.full_name for u in users}

    weekly = await db.execute(
        select(WeeklySchedule).where(
            WeeklySchedule.professional_id.in_(prof_ids),
            WeeklySchedule.is_active == True,
        )
    )
    weekly_map: dict[UUID, list] = {}
    for ws in weekly.scalars().all():
        weekly_map.setdefault(ws.professional_id, []).append(ws)

    overrides = await db.execute(
        select(ScheduleOverride).where(
            ScheduleOverride.professional_id.in_(prof_ids),
            ScheduleOverride.date.between(start, end),
        )
    )
    override_map: dict[UUID, list] = {}
    for ov in overrides.scalars().all():
        override_map.setdefault(ov.professional_id, []).append(ov)

    existing = await db.execute(
        select(Appointment).where(
            Appointment.professional_id.in_(prof_ids),
            Appointment.status.in_(["scheduled", "confirmed"]),
            Appointment.start_time.between(
                datetime.combine(start, time.min, tzinfo=UTC),
                datetime.combine(end, time.max, tzinfo=UTC),
            ),
        )
    )
    booked: dict[UUID, list] = {}
    for a in existing.scalars().all():
        booked.setdefault(a.professional_id, []).append(a)

    slots: list[dict] = []
    current = start
    while current <= end:
        for prof in users:
            day_name = current.strftime("%A").lower()

            day_overrides = override_map.get(prof.id, [])
            day_override = next(
                (o for o in day_overrides if o.date == current), None
            )
            if day_override and not day_override.is_available:
                continue

            day_schedules = weekly_map.get(prof.id, [])
            day_ws = [ws for ws in day_schedules if ws.day_of_week.lower() == day_name]

            if not day_ws and not day_override:
                continue

            if day_override and day_override.is_available and day_override.start_time:
                day_ws = [day_override]

            for ws in day_ws:
                ws_start = ws.start_time
                ws_end = ws.end_time
                if isinstance(ws_start, str):
                    ws_start = time.fromisoformat(ws_start)
                if isinstance(ws_end, str):
                    ws_end = time.fromisoformat(ws_end)

                booked_appts = booked.get(prof.id, [])
                for slot_start in _generate_slots(
                    current, ws_start, ws_end, booked_appts
                ):
                    dt_end = slot_start + timedelta(minutes=30)
                    slots.append(ClinicSlotResponse(
                        professional_id=str(prof.id),
                        professional_name=prof_names.get(prof.id, ""),
                        date=current.isoformat(),
                        start_time=slot_start.strftime("%H:%M"),
                        end_time=dt_end.strftime("%H:%M"),
                    ))
        current += timedelta(days=1)

    return ApiResponse(data=slots)


@public_router.post("/clinics/{slug}/book", status_code=201)
async def create_booking(
    slug: str,
    data: BookingRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    from app.core.auth.models import ClinicMembership, User
    from app.modules.agenda.models import Appointment
    from app.modules.agenda.service import AppointmentService
    from app.modules.patients.models import Patient

    clinic = await _resolve_clinic(db, slug)

    professional_id = UUID(data.professional_id)
    book_date = date.fromisoformat(data.date)
    start_time = time.fromisoformat(data.start_time)
    start_dt = datetime.combine(book_date, start_time, tzinfo=UTC)
    end_dt = start_dt + timedelta(minutes=30)

    # Atomic slot lock: SELECT ... FOR UPDATE prevents TOCTOU race
    existing = await db.execute(
        select(Appointment).where(
            Appointment.professional_id == professional_id,
            Appointment.status.in_(["scheduled", "confirmed"]),
            Appointment.start_time == start_dt,
        ).with_for_update()
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Slot already booked")

    prof_result = await db.execute(
        select(User).join(ClinicMembership, ClinicMembership.user_id == User.id).where(
            User.id == professional_id,
            ClinicMembership.clinic_id == clinic.id,
            ClinicMembership.role.in_(["dentist", "hygienist"]),
            User.is_active == True,
        )
    )
    prof = prof_result.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Professional not found")
    prof_name = prof.full_name

    patient_result = await db.execute(
        select(Patient).where(
            Patient.clinic_id == clinic.id,
            Patient.phone == data.patient_phone,
        )
    )
    patient = patient_result.scalar_one_or_none()

    if not patient:
        name_parts = data.patient_name.strip().split(" ", 1)
        patient = Patient(
            clinic_id=clinic.id,
            first_name=name_parts[0],
            last_name=name_parts[1] if len(name_parts) > 1 else ".",
            phone=data.patient_phone,
            email=data.patient_email,
            status="active",
        )
        db.add(patient)
        await db.flush()
        await db.refresh(patient)

    appointment = await AppointmentService.create(
        db,
        patient_id=patient.id,
        professional_id=professional_id,
        clinic_id=clinic.id,
        start_time=start_dt,
        end_time=end_dt,
        notes=data.notes or "",
        created_by=None,
    )

    return ApiResponse(data=BookingResponse(
        appointment_id=str(appointment.id),
        date=book_date.isoformat(),
        start_time=data.start_time,
        end_time=end_dt.strftime("%H:%M"),
        professional_name=prof_name,
    ))


def _generate_slots(
    day: date, start: time, end: time, booked_appts: list
) -> list[datetime]:
    from app.modules.agenda.models import Appointment

    slots: list[datetime] = []
    current = datetime.combine(day, start, tzinfo=UTC)
    end_dt = datetime.combine(day, end, tzinfo=UTC)

    booked_times = set()
    for a in booked_appts:
        if isinstance(a, Appointment):
            booked_times.add(a.start_time)

    while current < end_dt:
        if current not in booked_times:
            slots.append(current)
        current += timedelta(minutes=30)

    return slots
