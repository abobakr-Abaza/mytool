# Staff module

Internal staff lifecycle, sprint/task management, and financial operations
(expenses, revenue, profit-share calculation, payout ledger, audit logging).

**System-level** — not per-clinic. Staff roles (SUPER_ADMIN / SENIOR_TECH /
STAFF_EXECUTION) are orthogonal to clinic membership roles.

## Public API

Routes mounted at `/api/v1/staff/`. All endpoints gated by
`require_staff_permission`.

### Staff Profiles

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/profiles` | `staff.read` | List all staff |
| POST | `/profiles` | `staff.write` | Create staff profile |
| GET | `/profiles/{id}` | `staff.read` | Get staff profile |
| PATCH | `/profiles/{id}` | `staff.write` | Update staff fields |
| PATCH | `/profiles/{id}/status` | `staff.write` | Toggle status |
| PATCH | `/profiles/{id}/role` | `staff.write` | Change role |
| GET | `/me/profile` | (own) | Own profile |
| GET | `/me/tasks` | `tasks.own` | Own tasks (paginated) |
| GET | `/me/earnings` | `finance.own` | Own earnings calc |

### Sprints

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/sprints` | `tasks.read` | List all sprints |
| POST | `/sprints` | `tasks.write` | Create sprint |
| GET | `/sprints/{id}` | `tasks.read` | Get sprint |
| PATCH | `/sprints/{id}` | `tasks.write` | Update sprint |

### Tasks

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/tasks` | `tasks.read` | List tasks (paginated, filterable) |
| POST | `/tasks` | `tasks.write` | Create task |
| GET | `/tasks/{id}` | `tasks.read` | Get task + status logs |
| PATCH | `/tasks/{id}` | `tasks.write` | Update task fields |
| PATCH | `/tasks/{id}/status` | `tasks.write` | Transition status |
| GET | `/tasks/workload` | `staff.read` | Active-task counts per staff |

### Finance

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/finance/expenses` | `finance.read` | List expenses |
| POST | `/finance/expenses` | `finance.write` | Create expense |
| DELETE | `/finance/expenses/{id}` | `finance.write` | Delete expense |
| GET | `/finance/revenue` | `finance.read` | List gross revenue |
| POST | `/finance/revenue` | `finance.write` | Create revenue |
| GET | `/finance/profit-shares` | `finance.read` | List profit shares |
| POST | `/finance/profit-shares` | `finance.write` | Create profit share |
| PATCH | `/finance/profit-shares/{id}/vest` | `finance.write` | Toggle vesting |
| GET | `/finance/payouts` | `finance.read` | List payout ledger |
| POST | `/finance/payouts` | `finance.write` | Record payout |
| GET | `/finance/summary` | `finance.read` | Net profit calculation |
| GET | `/finance/earnings/{staff_id}` | `finance.read` | Staff earnings calc |

### Audit

| Method | Path | Permission | Description |
|--------|------|------------|-------------|
| GET | `/audit-logs` | `audit.read` | List audit log (paginated) |

## Dependencies

`manifest.depends = []`. Standalone module. References `users.id` via FK on
`staff_profiles.user_id` (core auth model), but does not depend on any other
module.

## Permissions

Unprefixed (registry adds `staff.` namespace):

- `staff.read`, `staff.write` — profile management
- `tasks.read`, `tasks.write` — sprint/task full access
- `tasks.own` — self-service task view
- `finance.read`, `finance.write` — financial management
- `finance.own` — self-service earnings view
- `audit.read` — audit log viewing

RBAC grants (in `dependencies.py`):

| Role | Grants |
|------|--------|
| SUPER_ADMIN | `*` (everything) |
| SENIOR_TECH | `staff.read`, `tasks.*`, `audit.read` |
| STAFF_EXECUTION | `tasks.own`, `finance.own` |

## Tools exposed

| Tool | Category | Permission | Description |
|------|----------|------------|-------------|
| `search_staff_profiles` | READ | `staff.read` | List all staff profiles |
| `get_staff_profile` | READ | `staff.read` | Get single profile |
| `list_tasks` | READ | `tasks.read` | List tasks with filters |
| `create_task` | WRITE | `tasks.write` | Create + assign task |
| `update_task_status` | WRITE | `tasks.write` | Transition task status |
| `get_financial_summary` | READ | `finance.read` | Net profit calc |
| `get_staff_earnings` | READ | `finance.read` | Staff earnings calc |

## Events emitted

| Event | When | Payload keys |
|-------|------|--------------|
| `staff.created` | Profile created | `profile_id`, `role` |
| `staff.role_changed` | Role updated | `profile_id`, `role` |
| `staff.status_changed` | Status changed | `profile_id`, `status` |
| `task.created` | Task created | `task_id`, `title` |
| `task.status_changed` | Status transition | `task_id`, `from`, `to` |
| `task.assigned` | Assignee set | `task_id`, `assignee_id` |
| `sprint.created` | Sprint created | `sprint_id`, `name` |
| `sprint.status_changed` | Sprint status | `sprint_id`, `status` |
| `expense.created` | Expense recorded | `expense_id`, `amount` |
| `revenue.created` | Revenue recorded | `revenue_id`, `amount` |
| `profit_share.created` | Profit share created | `profit_share_id`, `staff_id` |
| `profit_share.vested` | Vesting status changed | `profit_share_id`, `staff_id`, `status` |
| `payout.created` | Payout recorded | `payout_id`, `staff_id`, `amount` |

## Events consumed

None.

## Lifecycle

- `installable=True`, `auto_install=True`, `removable=False` —
  staff profiles and finance records must survive module cycles.

## Gotchas

- **System-level, not multi-tenant.** Staff profiles are not scoped to a
  clinic. The `get_staff_context()` dependency bypasses `ClinicContext`.
- **Separate RBAC from clinic roles.** Staff roles (SUPER_ADMIN etc.) are
  checked by `require_staff_permission()`, not `require_permission()`.
- **Task status transitions are enforced.** TODO → IN_PROGRESS → REVIEW → DONE.
  DONE is terminal. Invalid transitions return 422.
- **Financial calc engine.** Net profit = SUM(gross_revenue) - SUM(expenses).
  Staff earnings = net_profit × share_percentage / 100. Only profit shares
  with `vesting_status == "ACTIVE"` are included. `unpaid_balance` =
  gross_earnings - total_paid (all payouts ever, not period-scoped).
- **Audit trail.** Every sensitive admin action (role change, payout,
  expense creation) is logged to `staff_audit_logs`. Audit logs are
  append-only — no delete endpoint.
- **No clinic_id filtering.** All financial queries are global. Add
  clinic_id if staff/finance ever becomes per-tenant.

## Related ADRs

- `docs/adr/0001-modular-plugin-architecture.md`
- `docs/adr/0005-relative-permissions.md`

## CHANGELOG

See `./CHANGELOG.md`.
