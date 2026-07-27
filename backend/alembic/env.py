"""Alembic environment configuration for async migrations.

Supports mixed Alembic layout:
* Main linear chain under backend/alembic/versions/
* Per-module branches under backend/app/modules/<name>/migrations/versions/
  discovered via discover_version_locations().
"""

import asyncio
import os
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from app.config import settings

# Import all models so Base.metadata is populated
from app.core.tenancy.models import TenantBranding  # noqa: F401
from app.core.agents.models import Agent, AgentApprovalQueue, AgentAuditLog, AgentSession  # noqa: F401
from app.core.auth.models import Clinic, ClinicMembership, User  # noqa: F401
from app.core.plugins.alembic_paths import discover_version_locations
from app.core.plugins.db_models import ExternalId, ModuleOperationLog, ModuleRecord  # noqa: F401
from app.database import Base
from app.modules.agenda.models import Appointment, AppointmentTreatment, Cabinet  # noqa: F401
from app.modules.billing.models import Invoice, InvoiceHistory, InvoiceItem, InvoicePayment, InvoiceSeries, InvoiceSeriesHistory  # noqa: F401
from app.modules.budget.models import Budget, BudgetHistory, BudgetItem, BudgetSignature  # noqa: F401
from app.modules.catalog.models import TreatmentCatalogItem, TreatmentCategory, TreatmentOdontogramMapping, VatType  # noqa: F401
from app.modules.media.models import Document, MediaAttachment  # noqa: F401
from app.modules.notifications.models import ClinicChannelSettings, ClinicNotificationSettings, ClinicSmtpSettings, CommunicationMessage, NotificationPreference, NotificationTemplate  # noqa: F401
from app.modules.odontogram.models import OdontogramHistory, ToothRecord, Treatment, TreatmentTooth  # noqa: F401
from app.modules.patient_timeline.models import PatientTimeline  # noqa: F401
from app.modules.patients.models import Patient  # noqa: F401
from app.modules.patients_clinical.models import Allergy, EmergencyContact, LegalGuardian, MedicalContext, Medication, SurgicalHistory, SystemicDisease  # noqa: F401
from app.modules.payments.models import PatientEarnedEntry, Payment, PaymentAllocation, PaymentHistory, Refund  # noqa: F401
from app.modules.recalls.models import Recall, RecallContactAttempt, RecallSettings  # noqa: F401
from app.modules.schedules.models import ClinicOverride, ClinicWeeklySchedule, ProfessionalOverride, ProfessionalWeeklySchedule, ScheduleShift  # noqa: F401
from app.modules.treatment_plan.models import PlannedTreatmentItem, TreatmentPlan  # noqa: F401
from app.modules.whatsapp_kapso.models import WhatsappKapsoSettings, WhatsappKapsoTemplate  # noqa: F401
from app.modules.staff.models import AuditLog, ChatMessage, ChatUnreadStatus, Expense, Sprint, StaffProfile, Task, TaskStatusLog  # noqa: F401

ALEMBIC_DIR = Path(__file__).parent
BACKEND_ROOT = ALEMBIC_DIR.parent
MAIN_LINEAR = ALEMBIC_DIR / "versions"
MODULES_ROOT = BACKEND_ROOT / "app" / "modules"

config = context.config

DATABASE_URL = os.getenv("DATABASE_URL") or getattr(settings, "DATABASE_URL", None) or ""
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set — export it or add it to .env")
config.set_main_option("sqlalchemy.url", DATABASE_URL)

# Register version locations across all modules
config.set_main_option(
    "version_locations",
    os.pathsep.join(discover_version_locations(MAIN_LINEAR, MODULES_ROOT)),
)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# PgBouncer-compatible connect args for Supabase pooler (port 6543)
CONNECT_ARGS = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    cfg_section = dict(config.get_section(config.config_ini_section, {}))
    cfg_section.setdefault("sqlalchemy.url", DATABASE_URL)
    connectable = async_engine_from_config(
        cfg_section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=CONNECT_ARGS,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
