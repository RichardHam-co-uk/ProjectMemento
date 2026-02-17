# Task 1.2.2: Migration System

**Target file:** `vault/storage/migrations.py`
**Recommended model:** Gemini or Claude Haiku
**Effort:** Small-Medium (~1 hour)
**Dependencies:** `vault/storage/models.py` (already exists — read it first)

---

## Context

The LLM Memory Vault needs a lightweight database schema versioning system. We are NOT using Alembic — this is a simple version-tracking mechanism for SQLite.

The ORM models are already defined in `vault/storage/models.py`. Read that file to understand the `Base` class and all table definitions.

## Requirements

Create `vault/storage/migrations.py` with:

### 1. Schema Version Table (raw SQL, not ORM)
```sql
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL,
    description TEXT NOT NULL
);
```

### 2. Migration Dataclass
```python
@dataclass
class Migration:
    version: int
    description: str
    up: Callable[[Engine], None]
    down: Callable[[Engine], None]
```

### 3. MIGRATIONS Registry
A list containing at minimum:
- `Migration(version=1, description="Initial schema")` where:
  - `up` calls `Base.metadata.create_all(engine)` and inserts the version record
  - `down` calls `Base.metadata.drop_all(engine)`

### 4. Functions
- `get_current_version(engine: Engine) -> int` — Returns 0 if schema_version table doesn't exist
- `apply_migrations(engine: Engine) -> list[int]` — Applies all unapplied migrations in order, returns list of versions applied
- `needs_migration(engine: Engine) -> bool` — True if current version < latest migration version

### 5. Imports Required
```python
from vault.storage.models import Base
```

## Conventions
- Google-style docstrings on all public functions and classes
- Type hints on all parameters and return types
- `snake_case` for functions, `PascalCase` for classes
- Use `from datetime import datetime, timezone` for timestamps
- Use `sqlalchemy.text()` for raw SQL queries

## Acceptance Criteria
- [ ] `get_current_version()` returns 0 on fresh database
- [ ] `apply_migrations()` creates all tables from models.py
- [ ] `get_current_version()` returns 1 after migration
- [ ] Running `apply_migrations()` twice is idempotent (no errors)
- [ ] `needs_migration()` returns False after all migrations applied

## Files to Read First
- `vault/storage/models.py` — the ORM models and Base class
- `vault/config/models.py` — the DatabaseConfig for reference

---

## Console Prompt

Paste this into Continue to start the task:

```
Read the file vault/storage/models.py to understand the existing ORM models and Base class. Then create vault/storage/migrations.py — a lightweight database migration system (NOT Alembic). It needs: a schema_version table tracked via raw SQL, a Migration dataclass with up/down callables, a MIGRATIONS list with version 1 that calls Base.metadata.create_all(), and functions get_current_version(), apply_migrations(), needs_migration(). Use Google-style docstrings and full type hints. Import Base from vault.storage.models.
```
