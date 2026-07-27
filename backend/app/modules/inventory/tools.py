from app.core.tools import Tool

from .service import InventoryItemService


def get_tools() -> list[Tool]:
    return [
        Tool(
            name="list_low_stock_items",
            description="List all inventory items below their minimum stock threshold for the current clinic",
            category="READ",
            permissions=["inventory.read"],
            service_method=InventoryItemService.get_low_stock_items,
        ),
        Tool(
            name="inventory_dashboard",
            description="Get inventory dashboard stats: total items, low-stock count, out-of-stock count, total value",
            category="READ",
            permissions=["inventory.read"],
            service_method=InventoryItemService.get_dashboard,
        ),
    ]
