from collections.abc import Sequence

from pydantic import BaseModel

from app.core.agents import AgentContext, Tool, ToolCategory

from .models import InventoryItem
from .service import InventoryItemService


class NoArgs(BaseModel):
    pass


async def _list_low_stock(ctx: AgentContext, _params: NoArgs) -> dict:
    items: Sequence[InventoryItem] = await InventoryItemService.get_low_stock_items(ctx.db, ctx.clinic_id)
    return {
        "items": [
            {
                "id": str(i.id),
                "name": i.name,
                "category_id": str(i.category_id) if i.category_id else None,
                "quantity": i.quantity,
                "min_stock": i.min_stock,
                "unit": i.unit,
            }
            for i in items
        ],
        "total": len(items),
    }


async def _dashboard(ctx: AgentContext, _params: NoArgs) -> dict:
    return await InventoryItemService.get_dashboard(ctx.db, ctx.clinic_id)


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="list_low_stock_items",
            description="List all inventory items below their minimum stock threshold for the current clinic",
            parameters=NoArgs,
            handler=_list_low_stock,
            permissions=["inventory.read"],
            category=ToolCategory.READ,
        ),
        Tool(
            name="inventory_dashboard",
            description="Get inventory dashboard stats: total items, low-stock count, out-of-stock count, total value",
            parameters=NoArgs,
            handler=_dashboard,
            permissions=["inventory.read"],
            category=ToolCategory.READ,
        ),
    ]
