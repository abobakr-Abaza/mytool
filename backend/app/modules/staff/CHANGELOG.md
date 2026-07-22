# Changelog — Staff module

## Unreleased

### Added

- Staff profile lifecycle: CRUD, status toggling, role assignment
  (SUPER_ADMIN / SENIOR_TECH / STAFF_EXECUTION)
- Sprint tracking: create, list, update, status transitions
- Task management: create, assign, status lifecycle with timestamped logs,
  workload metrics
- Internal financial engine:
  - Expenses (SERVER, MARKETING, TOOLS, MISC categories)
  - Gross revenue tracking
  - Profit shares with LOCKED/ACTIVE vesting
  - Payout ledger with running balance tally
  - Net profit = gross revenue − total expenses
  - Staff earnings = net profit × share percentage (ACTIVE only)
- Audit log for sensitive admin actions (role changes, payouts, expenses)
- Staff RBAC enforcement at the server layer: 3 tiers with wildcard support
- Agent tools: 7 tools wrapping service methods
- 27 API endpoints under `/api/v1/staff/`
