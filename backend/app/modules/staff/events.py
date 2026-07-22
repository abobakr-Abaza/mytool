"""Staff module event type constants.

These are NOT registered in the core EventType class. The staff module
is system-level and events are consumed within the module or by agent
tools only.
"""

STAFF_CREATED = "staff.created"
STAFF_ROLE_CHANGED = "staff.role_changed"
STAFF_STATUS_CHANGED = "staff.status_changed"

TASK_CREATED = "task.created"
TASK_STATUS_CHANGED = "task.status_changed"
TASK_ASSIGNED = "task.assigned"

SPRINT_CREATED = "sprint.created"
SPRINT_STATUS_CHANGED = "sprint.status_changed"

EXPENSE_CREATED = "expense.created"
REVENUE_CREATED = "revenue.created"
PROFIT_SHARE_CREATED = "profit_share.created"
PROFIT_SHARE_VESTED = "profit_share.vested"
PAYOUT_CREATED = "payout.created"
