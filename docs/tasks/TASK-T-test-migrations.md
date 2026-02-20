# Task T-test-migrations: Real Tests for Migration System

**Target file:** `tests/test_migrations.py` (replace placeholder)
**Recommended model:** GPT-4o-mini or Qwen2.5-Coder
**Effort:** Small (~45 min)
**Dependencies:** `vault/storage/migrations.py`, `vault/storage/models.py`

---

## Context

`tests/test_migrations.py` currently has a single `test_placeholder`. Replace
it with a real test suite for `vault.storage.migrations`.

## Files to Read First

- `vault/storage/migrations.py` — full file
- `vault/storage/models.py` — ORM models (to check tables exist after migration)

## Migrations API

```python
from vault.storage.migrations import apply_migrations, get_current_version, needs_migration

apply_migrations(engine) -> list[int]     # returns list of applied version numbers
get_current_version(engine) -> int        # returns current schema version (0 if no migrations)
needs_migration(engine) -> bool           # True if pending migrations exist
```

## Tests to Write

```python
import pytest
from sqlalchemy import create_engine, inspect
from vault.storage.migrations import apply_migrations, get_current_version, needs_migration

@pytest.fixture
def engine(tmp_path):
    return create_engine(f"sqlite:///{tmp_path}/test.db")

class TestMigrations:

    def test_needs_migration_on_fresh_db(self, engine):
        """A brand-new database always needs migration."""
        assert needs_migration(engine) is True

    def test_apply_migrations_returns_list(self, engine):
        applied = apply_migrations(engine)
        assert isinstance(applied, list)
        assert len(applied) > 0

    def test_apply_migrations_idempotent(self, engine):
        """Running apply_migrations twice should not raise."""
        apply_migrations(engine)
        apply_migrations(engine)   # should be a no-op

    def test_needs_migration_false_after_apply(self, engine):
        apply_migrations(engine)
        assert needs_migration(engine) is False

    def test_get_current_version_zero_before_apply(self, engine):
        assert get_current_version(engine) == 0

    def test_get_current_version_positive_after_apply(self, engine):
        apply_migrations(engine)
        assert get_current_version(engine) >= 1

    def test_conversations_table_exists(self, engine):
        apply_migrations(engine)
        inspector = inspect(engine)
        assert "conversations" in inspector.get_table_names()

    def test_messages_table_exists(self, engine):
        apply_migrations(engine)
        inspector = inspect(engine)
        assert "messages" in inspector.get_table_names()

    def test_schema_version_table_exists(self, engine):
        apply_migrations(engine)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        # The version tracking table may be named "schema_version" or similar
        assert any("version" in t.lower() or "migration" in t.lower() for t in tables)
```

## Conventions

- Use `pytest` and `tmp_path`.
- Use `sqlalchemy.create_engine` directly (no VaultDB wrapper).
- Remove `test_placeholder` entirely.
- Keep `TestMigrations` class name.

---

## Console Prompt

```
Read vault/storage/migrations.py in full.

Replace tests/test_migrations.py with a real test suite. Use pytest,
tmp_path, and sqlalchemy.create_engine directly. Cover: needs_migration
True on fresh db, apply_migrations returns a non-empty list, apply is
idempotent (no error on second call), needs_migration False after apply,
get_current_version returns 0 before and >=1 after apply, conversations
table exists after apply, messages table exists after apply, a version
tracking table exists after apply.

Remove test_placeholder. Keep TestMigrations class name.
```
