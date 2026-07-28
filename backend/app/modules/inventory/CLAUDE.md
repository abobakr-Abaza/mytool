# Inventory module

Supplies and stock management with low-stock alerts. **Optional, removable.**

## Public API

Routes mounted at `/api/v1/inventory/`.

- `GET    /categories`        — list; `inventory.read`
- `POST   /categories`        — create; `inventory.write`
- `PUT    /categories/{id}`   — update; `inventory.write`
- `DELETE /categories/{id}`   — delete; `inventory.delete`
- `GET    /items`             — list; `inventory.read`
- `POST   /items`             — create; `inventory.write`
- `GET    /items/{id}`        — detail; `inventory.read`
- `PUT    /items/{id}`        — update; `inventory.write`
- `DELETE /items/{id}`        — delete; `inventory.delete`
- `POST   /movements`         — record movement; `inventory.write`
- `GET    /movements`         — list movements; `inventory.read`
- `GET    /alerts`            — low-stock alerts; `inventory.read`
- `GET    /dashboard`         — dashboard stats; `inventory.read`

## Dependencies

`manifest.depends = []`. Standalone module.

## Permissions

`inventory.read`, `inventory.write`, `inventory.delete`.

## Events emitted

| Event | When | Payload keys |
|---|---|---|
| `inventory.stock_changed` | stock movement recorded | `item_id`, `movement_type`, `quantity`, `new_quantity`, `clinic_id` |
| `inventory.low_stock` | quantity drops below min_stock | `item_id`, `item_name`, `quantity`, `min_stock`, `clinic_id` |

## CHANGELOG

See `./CHANGELOG.md`.
