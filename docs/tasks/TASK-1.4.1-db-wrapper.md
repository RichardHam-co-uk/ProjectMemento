# Task 1.4.1: Database Wrapper

**Target file:** `vault/storage/db.py`
**Recommended model:** Gemini or Claude Haiku
**Effort:** Medium (~1.5-2 hours)
**Dependencies:** `vault/storage/migrations.py` must exist first (Task 1.2.2)

---

## Context

The LLM Memory Vault uses SQLite via SQLAlchemy 2.x. We need a clean wrapper class that handles database initialization, session management, and common queries. The ORM models and migration system are already built.

## Files to Read First
- `vault/storage/models.py` — all ORM models (Conversation, Message, Artifact, PIIFinding, AuditEvent)
- `vault/storage/migrations.py` — the `apply_migrations(engine)` function
- `vault/config/models.py` — `DatabaseConfig` with `db_path` and `echo_sql` fields

## Requirements

Create `vault/storage/db.py` with a `VaultDB` class:

### 1. Constructor
```python
def __init__(self, db_path: Path, echo: bool = False):
```
- Create SQLAlchemy engine: `create_engine(f"sqlite:///{db_path}", echo=echo, connect_args={"check_same_thread": False})`
- Create `sessionmaker` bound to engine
- Set up SQLite pragmas on connection via event listener:
  ```python
  @event.listens_for(engine, "connect")
  def set_sqlite_pragma(dbapi_connection, connection_record):
      cursor = dbapi_connection.cursor()
      cursor.execute("PRAGMA journal_mode=WAL")
      cursor.execute("PRAGMA foreign_keys=ON")
      cursor.execute("PRAGMA synchronous=NORMAL")
      cursor.close()
  ```

### 2. Schema Initialization
```python
def init_schema(self) -> None:
    """Create tables and run migrations."""
    # Call apply_migrations(self.engine) from vault.storage.migrations
```

### 3. Session Context Manager
```python
@contextmanager
def get_session(self) -> Generator[Session, None, None]:
    """Provide a transactional session scope."""
    session = self.SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### 4. Convenience Query Methods

All methods should create their own session internally:

```python
def get_conversation(self, conv_id: str) -> Conversation | None:
    """Get a conversation by ID."""

def list_conversations(self, limit: int = 100, offset: int = 0, source: str | None = None) -> list[Conversation]:
    """List conversations with optional filtering."""
    # If source is provided, filter by it
    # Order by created_at descending

def count_conversations(self) -> int:
    """Return total number of conversations."""

def count_messages(self) -> int:
    """Return total number of messages."""

def get_messages_for_conversation(self, conv_id: str) -> list[Message]:
    """Get all messages for a conversation, ordered by timestamp."""

def add_conversation(self, conversation: Conversation) -> None:
    """Add a conversation to the database."""

def get_date_range(self) -> tuple[datetime | None, datetime | None]:
    """Get the oldest and newest conversation dates."""

def get_source_counts(self) -> dict[str, int]:
    """Get conversation counts grouped by source."""
    # Returns e.g. {"chatgpt": 120, "claude": 30}
```

## Imports Needed
```python
from pathlib import Path
from datetime import datetime
from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, event, func, select
from sqlalchemy.orm import Session, sessionmaker
from vault.storage.models import Conversation, Message
from vault.storage.migrations import apply_migrations
```

## Conventions
- Google-style docstrings on all public methods
- Full type hints
- `snake_case` for methods
- Use `select()` (SQLAlchemy 2.x style), NOT the legacy `session.query()` style

## Acceptance Criteria
- [ ] WAL mode enabled on connection
- [ ] Foreign keys enforced
- [ ] `init_schema()` creates all tables
- [ ] `get_session()` commits on success, rolls back on exception
- [ ] All convenience methods return correct types
- [ ] `list_conversations` supports limit, offset, source filter
- [ ] `get_source_counts` returns grouped counts

---

## Console Prompt

```
Read vault/storage/models.py and vault/storage/migrations.py first. Then create vault/storage/db.py — a database wrapper class VaultDB for SQLite via SQLAlchemy 2.x. It needs: constructor taking db_path and echo flag, SQLite pragma setup (WAL mode, foreign keys, synchronous=NORMAL) via event listener, init_schema() that calls apply_migrations(), a get_session() context manager with commit/rollback/close, and convenience methods: get_conversation, list_conversations (with limit/offset/source filter), count_conversations, count_messages, get_messages_for_conversation, add_conversation, get_date_range, get_source_counts. Use SQLAlchemy 2.x select() style, Google-style docstrings, and full type hints.
```
