#!/usr/bin/env python3
"""Remove stale alembic_version rows for which no migration file exists.

This handles the case where a module (e.g. verifactu) was removed from
the codebase but its alembic_version row persists in the database. Without
this cleanup, ``alembic upgrade heads`` fails with an overlap error
because the orphaned revision is requested by the DB but has no file in
the DAG.

Usage:
    python scripts/clean_stale_migrations.py

Designed to be called from ``docker-entrypoint.sh`` before
``alembic upgrade heads``. Non-zero exit means the cleanup itself failed,
**not** that stale rows were found (that is expected and handled).
"""

import re
import subprocess
import sys
from pathlib import Path


def _get_valid_revisions() -> set[str]:
    """Return all revision IDs declared in migration files under /app."""
    revs: set[str] = set()
    pattern = re.compile(r'^revision\s*=\s*[\x27"]([^\x27"]+)[\x27"]', re.M)
    for f in Path("/app").rglob("migrations/versions/*.py"):
        m = pattern.search(f.read_text())
        if m:
            revs.add(m.group(1))
    return revs


def _get_db_revisions(db_url: str) -> set[str]:
    """Query alembic_version and return the set of applied revision IDs."""
    res = subprocess.run(
        ["psql", db_url, "-tA", "-c", "SELECT version_num FROM alembic_version"],
        capture_output=True, text=True,
    )
    if res.returncode != 0:
        print(f"[clean_stale_migrations] psql query failed: {res.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    return {r.strip() for r in res.stdout.strip().split("\n") if r.strip()}


def _delete_stale(rev: str, db_url: str) -> None:
    subprocess.run(
        ["psql", db_url, "-c", f"DELETE FROM alembic_version WHERE version_num = '{rev}'"],
        capture_output=True,
    )


def main() -> int:
    # Import settings inside main() so entrypoint can call this before
    # the full app is loaded.
    from app.config import settings  # noqa: F401

    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    valid = _get_valid_revisions()
    db_revs = _get_db_revisions(db_url)

    stale = db_revs - valid
    if not stale:
        return 0

    for rev in stale:
        _delete_stale(rev, db_url)
        print(f"[clean_stale_migrations] Removed stale alembic_version row: {rev}")

    # Re-query to verify all stale rows were cleaned
    remaining = _get_db_revisions(db_url)
    still_stale = remaining - valid
    if still_stale:
        print(
            f"[clean_stale_migrations] WARNING: could not remove: {still_stale}",
            file=sys.stderr,
        )
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
