from __future__ import annotations

import logging
from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.events import EventType, event_bus
from app.modules.inventory.models import InventoryCategory, InventoryItem, InventoryMovement

logger = logging.getLogger(__name__)


class InventoryCategoryService:

    @staticmethod
    async def list(db: AsyncSession, clinic_id: UUID) -> Sequence[InventoryCategory]:
        result = await db.execute(
            select(InventoryCategory)
            .where(InventoryCategory.clinic_id == clinic_id)
            .order_by(InventoryCategory.name)
        )
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, clinic_id: UUID, data: dict) -> InventoryCategory:
        cat = InventoryCategory(clinic_id=clinic_id, **data)
        db.add(cat)
        await db.flush()
        await db.refresh(cat)
        return cat

    @staticmethod
    async def get(db: AsyncSession, category_id: UUID, clinic_id: UUID) -> InventoryCategory | None:
        result = await db.execute(
            select(InventoryCategory).where(
                InventoryCategory.id == category_id,
                InventoryCategory.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, category: InventoryCategory, data: dict) -> InventoryCategory:
        for key, value in data.items():
            setattr(category, key, value)
        await db.flush()
        await db.refresh(category)
        return category

    @staticmethod
    async def delete(db: AsyncSession, category: InventoryCategory) -> None:
        await db.delete(category)
        await db.flush()


class InventoryItemService:

    @staticmethod
    async def list(
        db: AsyncSession, clinic_id: UUID, category_id: UUID | None = None, status: str | None = None
    ) -> Sequence[InventoryItem]:
        q = select(InventoryItem).where(InventoryItem.clinic_id == clinic_id)
        if category_id:
            q = q.where(InventoryItem.category_id == category_id)
        if status:
            q = q.where(InventoryItem.status == status)
        q = q.order_by(InventoryItem.name)
        result = await db.execute(q)
        return result.scalars().all()

    @staticmethod
    async def create(db: AsyncSession, clinic_id: UUID, data: dict) -> InventoryItem:
        item = InventoryItem(clinic_id=clinic_id, **data)
        db.add(item)
        await db.flush()
        await db.refresh(item)
        return item

    @staticmethod
    async def get(db: AsyncSession, item_id: UUID, clinic_id: UUID) -> InventoryItem | None:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.id == item_id,
                InventoryItem.clinic_id == clinic_id,
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update(db: AsyncSession, item: InventoryItem, data: dict) -> InventoryItem:
        if "quantity" in data:
            raise ValueError("Use record_movement to change quantity")
        for key, value in data.items():
            setattr(item, key, value)
        await db.flush()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete(db: AsyncSession, item: InventoryItem) -> None:
        await db.delete(item)
        await db.flush()

    @staticmethod
    async def get_low_stock_items(db: AsyncSession, clinic_id: UUID) -> Sequence[InventoryItem]:
        result = await db.execute(
            select(InventoryItem).where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.status == "active",
                InventoryItem.quantity < InventoryItem.min_stock,
            ).order_by(InventoryItem.quantity)
        )
        return result.scalars().all()

    @staticmethod
    async def get_dashboard(db: AsyncSession, clinic_id: UUID) -> dict:
        items_count = await db.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.status == "active",
            )
        )
        total_items = items_count.scalar() or 0

        low = await db.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.status == "active",
                InventoryItem.quantity < InventoryItem.min_stock,
            )
        )
        low_stock_count = low.scalar() or 0

        oos = await db.execute(
            select(func.count(InventoryItem.id)).where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.quantity <= 0,
            )
        )
        out_of_stock_count = oos.scalar() or 0

        cats = await db.execute(
            select(func.count(InventoryCategory.id)).where(
                InventoryCategory.clinic_id == clinic_id,
            )
        )
        total_categories = cats.scalar() or 0

        value_rows = await db.execute(
            select(func.sum(InventoryItem.unit_price * InventoryItem.quantity)).where(
                InventoryItem.clinic_id == clinic_id,
                InventoryItem.status == "active",
            )
        )
        total_value = float(value_rows.scalar() or 0)

        return {
            "total_items": total_items,
            "low_stock_count": low_stock_count,
            "out_of_stock_count": out_of_stock_count,
            "total_categories": total_categories,
            "total_value": total_value,
        }


class InventoryMovementService:

    @staticmethod
    async def record(
        db: AsyncSession,
        clinic_id: UUID,
        user_id: UUID,
        data: dict,
    ) -> InventoryMovement:
        item_id = data["item_id"]
        movement_type = data["movement_type"]
        qty = data["quantity"]

        if movement_type == "out":
            result = await db.execute(
                update(InventoryItem)
                .where(
                    InventoryItem.id == item_id,
                    InventoryItem.clinic_id == clinic_id,
                    InventoryItem.quantity >= qty,
                )
                .values(quantity=InventoryItem.quantity - qty)
                .returning(InventoryItem)
            )
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Insufficient stock or item not found")
        elif movement_type == "in":
            result = await db.execute(
                update(InventoryItem)
                .where(
                    InventoryItem.id == item_id,
                    InventoryItem.clinic_id == clinic_id,
                )
                .values(quantity=InventoryItem.quantity + qty)
                .returning(InventoryItem)
            )
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")
        elif movement_type == "adjustment":
            if qty < 0:
                raise ValueError("Adjustment quantity must be non-negative; use negative adjustment via service")
            result = await db.execute(
                update(InventoryItem)
                .where(
                    InventoryItem.id == item_id,
                    InventoryItem.clinic_id == clinic_id,
                )
                .values(quantity=qty)
                .returning(InventoryItem)
            )
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")
        elif movement_type == "return":
            result = await db.execute(
                update(InventoryItem)
                .where(
                    InventoryItem.id == item_id,
                    InventoryItem.clinic_id == clinic_id,
                )
                .values(quantity=InventoryItem.quantity + qty)
                .returning(InventoryItem)
            )
            item = result.scalar_one_or_none()
            if not item:
                raise ValueError("Item not found")
        else:
            raise ValueError(f"Unknown movement type: {movement_type}")

        movement = InventoryMovement(
            clinic_id=clinic_id,
            item_id=item_id,
            movement_type=movement_type,
            quantity=qty,
            reference=data.get("reference"),
            notes=data.get("notes"),
            moved_by=user_id,
        )
        db.add(movement)
        await db.flush()
        await db.refresh(movement)

        await event_bus.publish(EventType.INVENTORY_STOCK_CHANGED, {
            "item_id": str(item_id),
            "movement_type": movement_type,
            "quantity": qty,
            "new_quantity": item.quantity,
            "clinic_id": str(clinic_id),
        })

        if item.quantity < item.min_stock:
            await event_bus.publish(EventType.INVENTORY_LOW_STOCK, {
                "item_id": str(item_id),
                "item_name": item.name,
                "quantity": item.quantity,
                "min_stock": item.min_stock,
                "clinic_id": str(clinic_id),
            })

        return movement

    @staticmethod
    async def list(
        db: AsyncSession, clinic_id: UUID, item_id: UUID | None = None
    ) -> Sequence[InventoryMovement]:
        q = select(InventoryMovement).where(InventoryMovement.clinic_id == clinic_id)
        if item_id:
            q = q.where(InventoryMovement.item_id == item_id)
        q = q.order_by(InventoryMovement.moved_at.desc())
        result = await db.execute(q)
        return result.scalars().all()
