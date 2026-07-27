from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import ClinicContext, get_clinic_context, require_permission
from app.core.schemas import ApiResponse, PaginatedApiResponse
from app.database import get_db

from .schemas import (
    AlertResponse,
    CategoryCreate,
    CategoryResponse,
    DashboardStats,
    ItemCreate,
    ItemResponse,
    ItemUpdate,
    MovementCreate,
    MovementResponse,
)
from .service import InventoryCategoryService, InventoryItemService, InventoryMovementService

router = APIRouter()


# --- Categories ----------------------------------------------------------------

@router.get("/categories", response_model=PaginatedApiResponse[CategoryResponse])
async def list_categories(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaginatedApiResponse[CategoryResponse]:
    items = await InventoryCategoryService.list(db, ctx.clinic_id)
    return PaginatedApiResponse(
        data=[CategoryResponse.model_validate(i) for i in items],
        total=len(items), page=1, page_size=len(items) or 1,
    )


@router.post("/categories", response_model=ApiResponse[CategoryResponse], status_code=201)
async def create_category(
    data: CategoryCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[CategoryResponse]:
    cat = await InventoryCategoryService.create(db, ctx.clinic_id, data.model_dump())
    return ApiResponse(data=CategoryResponse.model_validate(cat))


@router.put("/categories/{category_id}", response_model=ApiResponse[CategoryResponse])
async def update_category(
    category_id: UUID,
    data: CategoryCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[CategoryResponse]:
    cat = await InventoryCategoryService.get(db, category_id, ctx.clinic_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    cat = await InventoryCategoryService.update(db, cat, data.model_dump())
    return ApiResponse(data=CategoryResponse.model_validate(cat))


@router.delete("/categories/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    cat = await InventoryCategoryService.get(db, category_id, ctx.clinic_id)
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    await InventoryCategoryService.delete(db, cat)


# --- Items ---------------------------------------------------------------------

@router.get("/items", response_model=PaginatedApiResponse[ItemResponse])
async def list_items(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    category_id: UUID | None = Query(None),
    status: str | None = Query(None),
) -> PaginatedApiResponse[ItemResponse]:
    raw_items = await InventoryItemService.list(db, ctx.clinic_id, category_id, status)
    cats = {c.id: c.name for c in await InventoryCategoryService.list(db, ctx.clinic_id)}
    data = []
    for i in raw_items:
        r = ItemResponse.model_validate(i)
        r.category_name = cats.get(i.category_id) if i.category_id else None
        r.is_low_stock = i.quantity < i.min_stock if i.status == "active" else False
        data.append(r)
    return PaginatedApiResponse(
        data=data, total=len(data), page=1, page_size=len(data) or 1,
    )


@router.post("/items", response_model=ApiResponse[ItemResponse], status_code=201)
async def create_item(
    data: ItemCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ItemResponse]:
    item = await InventoryItemService.create(db, ctx.clinic_id, data.model_dump(exclude_none=True))
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.get("/items/{item_id}", response_model=ApiResponse[ItemResponse])
async def get_item(
    item_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ItemResponse]:
    item = await InventoryItemService.get(db, item_id, ctx.clinic_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    r = ItemResponse.model_validate(item)
    r.is_low_stock = item.quantity < item.min_stock if item.status == "active" else False
    return ApiResponse(data=r)


@router.put("/items/{item_id}", response_model=ApiResponse[ItemResponse])
async def update_item(
    item_id: UUID,
    data: ItemUpdate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[ItemResponse]:
    item = await InventoryItemService.get(db, item_id, ctx.clinic_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    payload = data.model_dump(exclude_none=True)
    item = await InventoryItemService.update(db, item, payload)
    return ApiResponse(data=ItemResponse.model_validate(item))


@router.delete("/items/{item_id}", status_code=204)
async def delete_item(
    item_id: UUID,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.delete"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    item = await InventoryItemService.get(db, item_id, ctx.clinic_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await InventoryItemService.delete(db, item)


# --- Movements -----------------------------------------------------------------

@router.post("/movements", response_model=ApiResponse[MovementResponse], status_code=201)
async def record_movement(
    data: MovementCreate,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.write"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[MovementResponse]:
    try:
        movement = await InventoryMovementService.record(
            db, ctx.clinic_id, ctx.user_id, data.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ApiResponse(data=MovementResponse.model_validate(movement))


@router.get("/movements", response_model=PaginatedApiResponse[MovementResponse])
async def list_movements(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
    item_id: UUID | None = Query(None),
) -> PaginatedApiResponse[MovementResponse]:
    items = await InventoryMovementService.list(db, ctx.clinic_id, item_id)
    return PaginatedApiResponse(
        data=[MovementResponse.model_validate(i) for i in items],
        total=len(items), page=1, page_size=len(items) or 1,
    )


# --- Alerts & Dashboard --------------------------------------------------------

@router.get("/alerts", response_model=PaginatedApiResponse[AlertResponse])
async def get_alerts(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PaginatedApiResponse[AlertResponse]:
    items = await InventoryItemService.get_low_stock_items(db, ctx.clinic_id)
    cats = {c.id: c.name for c in await InventoryCategoryService.list(db, ctx.clinic_id)}
    data = [
        AlertResponse(
            item_id=i.id, item_name=i.name, quantity=i.quantity,
            min_stock=i.min_stock, category_name=cats.get(i.category_id),
        ) for i in items
    ]
    return PaginatedApiResponse(
        data=data, total=len(data), page=1, page_size=len(data) or 1,
    )


@router.get("/dashboard", response_model=ApiResponse[DashboardStats])
async def get_dashboard(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context)],
    _: Annotated[None, Depends(require_permission("inventory.read"))],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[DashboardStats]:
    stats = await InventoryItemService.get_dashboard(db, ctx.clinic_id)
    return ApiResponse(data=DashboardStats(**stats))
