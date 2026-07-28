from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

MovementType = Literal["in", "out", "adjustment", "return"]
ItemStatus = Literal["active", "discontinued", "out_of_stock"]


class CategoryCreate(BaseModel):
    name: str = Field(..., max_length=120)
    description: str | None = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    clinic_id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


class ItemCreate(BaseModel):
    category_id: UUID | None = None
    name: str = Field(..., max_length=200)
    sku: str | None = Field(None, max_length=60)
    unit: str = "unit"
    quantity: int = Field(default=0, ge=0)
    min_stock: int = Field(default=5, ge=0)
    unit_price: float | None = None
    notes: str | None = None
    supplier: str | None = Field(None, max_length=200)


class ItemUpdate(BaseModel):
    category_id: UUID | None = None
    name: str | None = Field(None, max_length=200)
    sku: str | None = Field(None, max_length=60)
    unit: str | None = None
    quantity: int | None = None
    min_stock: int | None = None
    unit_price: float | None = None
    status: ItemStatus | None = None
    notes: str | None = None
    supplier: str | None = Field(None, max_length=200)


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    clinic_id: UUID
    category_id: UUID | None
    name: str
    sku: str | None
    unit: str
    quantity: int
    min_stock: int
    unit_price: float | None
    status: str
    notes: str | None
    supplier: str | None
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    is_low_stock: bool = False


class MovementCreate(BaseModel):
    item_id: UUID
    movement_type: MovementType
    quantity: int = Field(..., ge=1)
    reference: str | None = Field(None, max_length=120)
    notes: str | None = None


class MovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    clinic_id: UUID
    item_id: UUID
    movement_type: str
    quantity: int
    reference: str | None
    notes: str | None
    moved_by: UUID
    moved_at: datetime
    created_at: datetime
    updated_at: datetime


class AlertResponse(BaseModel):
    item_id: UUID
    item_name: str
    quantity: int
    min_stock: int
    category_name: str | None


class DashboardStats(BaseModel):
    total_items: int
    low_stock_count: int
    out_of_stock_count: int
    total_categories: int
    total_value: float
