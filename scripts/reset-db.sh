#!/bin/bash
# Reset database and run migrations
# Usage: ./scripts/reset-db.sh
#
# Note: This only resets the schema. To seed demo data, run:
#   ./scripts/seed-demo.sh

set -e

echo "Resetting database..."

# Drop the entire public schema and recreate it — this removes tables,
# composite types, enums, and sequences atomically (avoids the
# pg_type_typname_nsp_index collision that can occur with per-table drops).
docker compose exec -T db psql -U dental -d dental_clinic -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" 2>/dev/null || true

# Run migrations
docker compose exec -T backend alembic upgrade heads

# Restart the backend so the module registry reconciles against the
# fresh schema. Without this, `core_module` stays empty until the next
# manual restart — which makes `/api/v1/modules/-/active` return no
# installed modules and the sidebar collapses to host-shell-only nav.
echo ""
echo "Restarting backend to reconcile module registry..."
docker compose restart backend >/dev/null
# Wait for FastAPI to finish lifespan startup (which runs the module
# registry reconcile) before we return — early callers would race it.
for i in {1..30}; do
  count=$(docker compose exec -T db psql -U dental -d dental_clinic -tA -c \
    "SELECT COUNT(*) FROM core_module WHERE state='installed';" 2>/dev/null | tr -d '[:space:]')
  if [ -n "$count" ] && [ "$count" -gt 0 ]; then
    echo "  registry reconciled ($count modules installed)"
    break
  fi
  sleep 1
done

echo ""
echo "Database reset complete!"
echo "Run ./scripts/seed-demo.sh to create demo data."
