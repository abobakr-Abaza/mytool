"""HTTP surface for staff management, sprint/tasks, finance, and chat.

Mounted at ``/api/v1/staff/*``. All endpoints are gated by staff RBAC roles
(SUPER_ADMIN / SENIOR_TECH / STAFF_EXECUTION) via ``require_staff_permission``.
"""

import json
from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from jose import JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.service import decode_token
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db, async_session_maker

from .dependencies import StaffContext, get_staff_context, require_staff_permission
from .schemas import (
    AuditLogResponse,
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatReadRequest,
    ExpenseCreate,
    ExpenseResponse,
    FinancialSummaryResponse,
    GrossRevenueCreate,
    GrossRevenueResponse,
    PayoutCreate,
    PayoutResponse,
    ProfitShareCreate,
    ProfitShareResponse,
    SprintCreate,
    SprintResponse,
    SprintUpdate,
    StaffEarningsResponse,
    StaffProfileCreate,
    StaffProfileResponse,
    StaffProfileUpdate,
    TaskCreate,
    TaskResponse,
    TaskStatusUpdate,
    TaskUpdate,
    VestingUpdate,
    WorkloadResponse,
)
from .service import (
    AuditService,
    ChatService,
    FinanceService,
    SprintService,
    StaffProfileService,
    TaskService,
    chat_manager,
)
from .models import StaffProfile

router = APIRouter()


# ==========================================================================
# Staff Profiles
# ==========================================================================


@router.get("/profiles", response_model=ApiResponse[list[StaffProfileResponse]])
async def list_staff_profiles(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[StaffProfileResponse]]:
    profiles = await StaffProfileService.list(db)
    return ApiResponse(data=[StaffProfileResponse.model_validate(p) for p in profiles])


@router.post("/profiles", response_model=ApiResponse[StaffProfileResponse], status_code=201)
async def create_staff_profile(
    data: StaffProfileCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[StaffProfileResponse]:
    profile = await StaffProfileService.create(db, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=StaffProfileResponse.model_validate(profile))


@router.get("/profiles/{profile_id}", response_model=ApiResponse[StaffProfileResponse])
async def get_staff_profile(
    profile_id: UUID,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[StaffProfileResponse]:
    profile = await StaffProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    return ApiResponse(data=StaffProfileResponse.model_validate(profile))


@router.patch("/profiles/{profile_id}", response_model=ApiResponse[StaffProfileResponse])
async def update_staff_profile(
    profile_id: UUID,
    data: StaffProfileUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[StaffProfileResponse]:
    profile = await StaffProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    profile = await StaffProfileService.update(db, profile, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=StaffProfileResponse.model_validate(profile))


@router.patch("/profiles/{profile_id}/status", response_model=ApiResponse[StaffProfileResponse])
async def update_staff_status(
    profile_id: UUID,
    data: StaffProfileUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[StaffProfileResponse]:
    profile = await StaffProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    if not data.status:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="status is required")
    profile = await StaffProfileService.update_status(db, profile, data.status, ctx.staff_id)
    return ApiResponse(data=StaffProfileResponse.model_validate(profile))


@router.patch("/profiles/{profile_id}/role", response_model=ApiResponse[StaffProfileResponse])
async def update_staff_role(
    profile_id: UUID,
    data: StaffProfileUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[StaffProfileResponse]:
    profile = await StaffProfileService.get(db, profile_id)
    if not profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Staff profile not found")
    if not data.role:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="role is required")
    profile = await StaffProfileService.update_role(db, profile, data.role, ctx.staff_id)
    return ApiResponse(data=StaffProfileResponse.model_validate(profile))


# ==========================================================================
# My Profile (self-service for STAFF_EXECUTION)
# ==========================================================================


@router.get("/me/profile", response_model=ApiResponse[StaffProfileResponse])
async def get_my_profile(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[StaffProfileResponse]:
    return ApiResponse(data=StaffProfileResponse.model_validate(ctx.profile))


@router.get("/me/tasks", response_model=PaginatedApiResponse[TaskResponse])
async def get_my_tasks(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.own"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[TaskResponse]:
    tasks, total = await TaskService.list(db, assignee_id=ctx.staff_id, page=page, page_size=page_size)
    return PaginatedApiResponse(
        data=[TaskResponse.model_validate(t) for t in tasks],
        total=total, page=page, page_size=page_size,
    )


@router.get("/me/earnings", response_model=ApiResponse[StaffEarningsResponse])
async def get_my_earnings(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.own"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    period_start: datetime | None = Query(default=None),
    period_end: datetime | None = Query(default=None),
) -> ApiResponse[StaffEarningsResponse]:
    earnings = await FinanceService.get_staff_earnings(db, ctx.staff_id, period_start, period_end)
    return ApiResponse(data=StaffEarningsResponse(**earnings))


# ==========================================================================
# Sprints
# ==========================================================================


@router.get("/sprints", response_model=ApiResponse[list[SprintResponse]])
async def list_sprints(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[SprintResponse]]:
    sprints = await SprintService.list(db)
    return ApiResponse(data=[SprintResponse.model_validate(s) for s in sprints])


@router.post("/sprints", response_model=ApiResponse[SprintResponse], status_code=201)
async def create_sprint(
    data: SprintCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SprintResponse]:
    sprint = await SprintService.create(db, data.model_dump(exclude_unset=True))
    return ApiResponse(data=SprintResponse.model_validate(sprint))


@router.get("/sprints/{sprint_id}", response_model=ApiResponse[SprintResponse])
async def get_sprint(
    sprint_id: UUID,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SprintResponse]:
    sprint = await SprintService.get(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    return ApiResponse(data=SprintResponse.model_validate(sprint))


@router.patch("/sprints/{sprint_id}", response_model=ApiResponse[SprintResponse])
async def update_sprint(
    sprint_id: UUID,
    data: SprintUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[SprintResponse]:
    sprint = await SprintService.get(db, sprint_id)
    if not sprint:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sprint not found")
    sprint = await SprintService.update(db, sprint, data.model_dump(exclude_unset=True))
    return ApiResponse(data=SprintResponse.model_validate(sprint))


# ==========================================================================
# Tasks
# ==========================================================================


@router.get("/tasks", response_model=PaginatedApiResponse[TaskResponse])
async def list_tasks(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    assignee_id: UUID | None = Query(default=None),
    sprint_id: UUID | None = Query(default=None),
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> PaginatedApiResponse[TaskResponse]:
    tasks, total = await TaskService.list(db, assignee_id, sprint_id, status, page, page_size)
    return PaginatedApiResponse(
        data=[TaskResponse.model_validate(t) for t in tasks],
        total=total, page=page, page_size=page_size,
    )


@router.post("/tasks", response_model=ApiResponse[TaskResponse], status_code=201)
async def create_task(
    data: TaskCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TaskResponse]:
    task = await TaskService.create(db, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=TaskResponse.model_validate(task))


@router.get("/tasks/{task_id}", response_model=ApiResponse[TaskResponse])
async def get_task(
    task_id: UUID,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TaskResponse]:
    task = await TaskService.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return ApiResponse(data=TaskResponse.model_validate(task))


@router.patch("/tasks/{task_id}", response_model=ApiResponse[TaskResponse])
async def update_task(
    task_id: UUID,
    data: TaskUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TaskResponse]:
    task = await TaskService.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await TaskService.update(db, task, data.model_dump(exclude_unset=True))
    return ApiResponse(data=TaskResponse.model_validate(task))


@router.patch("/tasks/{task_id}/status", response_model=ApiResponse[TaskResponse])
async def update_task_status(
    task_id: UUID,
    data: TaskStatusUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("tasks.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[TaskResponse]:
    task = await TaskService.get(db, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    task = await TaskService.update_status(db, task, data.status, ctx.staff_id)
    return ApiResponse(data=TaskResponse.model_validate(task))


@router.get("/tasks/workload", response_model=ApiResponse[list[WorkloadResponse]])
async def get_workload(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("staff.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[WorkloadResponse]]:
    metrics = await TaskService.get_workload(db)
    return ApiResponse(data=[WorkloadResponse(**m) for m in metrics])


# ==========================================================================
# Finance — Expenses
# ==========================================================================


@router.get("/finance/expenses", response_model=ApiResponse[list[ExpenseResponse]])
async def list_expenses(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[ExpenseResponse]]:
    expenses = await FinanceService.list_expenses(db)
    return ApiResponse(data=[ExpenseResponse.model_validate(e) for e in expenses])


@router.post("/finance/expenses", response_model=ApiResponse[ExpenseResponse], status_code=201)
async def create_expense(
    data: ExpenseCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ExpenseResponse]:
    expense = await FinanceService.create_expense(db, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=ExpenseResponse.model_validate(expense))


@router.delete("/finance/expenses/{expense_id}", status_code=204)
async def delete_expense(
    expense_id: UUID,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    expense = await FinanceService.get_expense(db, expense_id)
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    await FinanceService.delete_expense(db, expense, ctx.staff_id)


# ==========================================================================
# Finance — Gross Revenue
# ==========================================================================


@router.get("/finance/revenue", response_model=ApiResponse[list[GrossRevenueResponse]])
async def list_revenue(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[GrossRevenueResponse]]:
    revenues = await FinanceService.list_revenue(db)
    return ApiResponse(data=[GrossRevenueResponse.model_validate(r) for r in revenues])


@router.post("/finance/revenue", response_model=ApiResponse[GrossRevenueResponse], status_code=201)
async def create_revenue(
    data: GrossRevenueCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[GrossRevenueResponse]:
    revenue = await FinanceService.create_revenue(db, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=GrossRevenueResponse.model_validate(revenue))


# ==========================================================================
# Finance — Profit Shares
# ==========================================================================


@router.get("/finance/profit-shares", response_model=ApiResponse[list[ProfitShareResponse]])
async def list_profit_shares(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[ProfitShareResponse]]:
    shares = await FinanceService.list_profit_shares(db)
    return ApiResponse(data=[ProfitShareResponse.model_validate(s) for s in shares])


@router.post("/finance/profit-shares", response_model=ApiResponse[ProfitShareResponse], status_code=201)
async def create_profit_share(
    data: ProfitShareCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ProfitShareResponse]:
    ps = await FinanceService.create_profit_share(db, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=ProfitShareResponse.model_validate(ps))


@router.patch("/finance/profit-shares/{ps_id}/vest", response_model=ApiResponse[ProfitShareResponse])
async def update_vesting(
    ps_id: UUID,
    data: VestingUpdate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ProfitShareResponse]:
    ps = await FinanceService.get_profit_share(db, ps_id)
    if not ps:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profit share not found")
    ps = await FinanceService.update_vesting(db, ps, data.vesting_status, ctx.staff_id)
    return ApiResponse(data=ProfitShareResponse.model_validate(ps))


# ==========================================================================
# Finance — Payouts
# ==========================================================================


@router.get("/finance/payouts", response_model=ApiResponse[list[PayoutResponse]])
async def list_payouts(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[PayoutResponse]]:
    payouts = await FinanceService.list_payouts(db)
    return ApiResponse(data=[PayoutResponse.model_validate(p) for p in payouts])


@router.post("/finance/payouts", response_model=ApiResponse[PayoutResponse], status_code=201)
async def create_payout(
    data: PayoutCreate,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[PayoutResponse]:
    payout = await FinanceService.create_payout(db, data.model_dump(exclude_unset=True), ctx.staff_id)
    return ApiResponse(data=PayoutResponse.model_validate(payout))


# ==========================================================================
# Finance — Summary & Earnings
# ==========================================================================


@router.get("/finance/summary", response_model=ApiResponse[FinancialSummaryResponse])
async def get_financial_summary(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    period_start: datetime | None = Query(default=None),
    period_end: datetime | None = Query(default=None),
) -> ApiResponse[FinancialSummaryResponse]:
    summary = await FinanceService.get_summary(db, period_start, period_end)
    return ApiResponse(data=FinancialSummaryResponse(**summary))


@router.get("/finance/earnings/{staff_id}", response_model=ApiResponse[StaffEarningsResponse])
async def get_staff_earnings(
    staff_id: UUID,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("finance.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    period_start: datetime | None = Query(default=None),
    period_end: datetime | None = Query(default=None),
) -> ApiResponse[StaffEarningsResponse]:
    earnings = await FinanceService.get_staff_earnings(db, staff_id, period_start, period_end)
    return ApiResponse(data=StaffEarningsResponse(**earnings))


# ==========================================================================
# Audit Logs
# ==========================================================================


@router.get("/audit-logs", response_model=PaginatedApiResponse[AuditLogResponse])
async def list_audit_logs(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    _: Annotated[None, Depends(require_staff_permission("audit.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> PaginatedApiResponse[AuditLogResponse]:
    logs, total = await AuditService.list(db, page, page_size)
    return PaginatedApiResponse(
        data=[AuditLogResponse.model_validate(l) for l in logs],
        total=total, page=page, page_size=page_size,
    )


# ==========================================================================
# Chat — WebSocket
# ==========================================================================


@router.websocket("/ws/chat")
async def chat_websocket(websocket: WebSocket, token: str = Query(...)):
    """WebSocket endpoint for real-time chat.

    Authenticates via JWT ``token`` query param. Client sends JSON frames:
      ``{"type": "join", "room": "TASK:<uuid>"}``
      ``{"type": "leave", "room": "TASK:<uuid>"}``
      ``{"type": "message", "room": "GENERAL", "text": "...", "attachments": {...}}``

    Server broadcasts ``ChatMessageResponse`` JSON to room on each message.
    """
    profile: StaffProfile | None = None
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id or payload.get("type") != "access":
            await websocket.close(code=4001)
            return
        async with async_session_maker() as db:
            result = await db.execute(
                select(StaffProfile).where(StaffProfile.user_id == UUID(user_id))
            )
            profile = result.scalar_one_or_none()
            if not profile or profile.status not in ("ACTIVE", "PROBATION"):
                await websocket.close(code=4003)
                return
    except (JWTError, ValueError):
        await websocket.close(code=4001)
        return

    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            if msg_type == "join":
                room = data.get("room")
                if room:
                    chat_manager.join(room, websocket)

            elif msg_type == "leave":
                room = data.get("room")
                if room:
                    chat_manager.leave(room, websocket)

            elif msg_type == "message":
                room = data.get("room", "GENERAL")
                text = data.get("text", "")
                attachments = data.get("attachments")

                parts = room.split(":", 1)
                channel_type = parts[0]
                channel_id = parts[1] if len(parts) > 1 else ""

                async with async_session_maker() as db:
                    msg = await ChatService.save_message(
                        db, profile.id, channel_type, channel_id, text, attachments
                    )
                    await db.commit()
                    payload_json = ChatMessageResponse(
                        id=msg.id,
                        sender_id=msg.sender_id,
                        sender_name=profile.name,
                        channel_type=msg.channel_type,
                        channel_id=msg.channel_id,
                        message_text=msg.message_text,
                        attachments=msg.attachments,
                        created_at=msg.created_at,
                    ).model_dump_json()

                await chat_manager.broadcast(room, payload_json)
                await websocket.send_text(payload_json)

    except WebSocketDisconnect:
        chat_manager.leave_all(websocket)


# ==========================================================================
# Chat — REST Endpoints
# ==========================================================================


@router.get("/chat/history", response_model=ApiResponse[ChatHistoryResponse])
async def get_chat_history(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
    channel_type: str = Query(...),
    channel_id: str = Query(...),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
) -> ApiResponse[ChatHistoryResponse]:
    messages, total = await ChatService.get_history(db, channel_type, channel_id, page, page_size)
    return ApiResponse(data=ChatHistoryResponse(
        messages=[ChatMessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            sender_name=m.sender.name if m.sender else None,
            channel_type=m.channel_type,
            channel_id=m.channel_id,
            message_text=m.message_text,
            attachments=m.attachments,
            created_at=m.created_at,
        ) for m in messages],
        total=total,
        page=page,
        page_size=page_size,
    ))


@router.post("/chat/read", status_code=204)
async def mark_channel_read(
    data: ChatReadRequest,
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    await ChatService.mark_read(db, ctx.staff_id, data.channel_type, data.channel_id)


@router.get("/chat/unread", response_model=ApiResponse[list[dict]])
async def get_unread_counts(
    ctx: Annotated[StaffContext, Depends(get_staff_context)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[list[dict]]:
    counts = await ChatService.get_unread_counts(db, ctx.staff_id)
    return ApiResponse(data=counts)



