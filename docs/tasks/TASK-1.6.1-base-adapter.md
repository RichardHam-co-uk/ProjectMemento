# Task 1.6.1: Base Adapter Interface

**Target file:** `vault/ingestion/base.py`
**Recommended model:** Qwen2.5-Coder or DeepSeek-Coder (local)
**Effort:** Small (~30-45 min)
**Dependencies:** None (standalone interfaces)

---

## Context

The LLM Memory Vault imports conversations from multiple providers (ChatGPT, Claude, Perplexity). Each provider has its own export format. We need a common interface and shared data types that all adapters implement.

## Requirements

Create `vault/ingestion/base.py` with:

### 1. Data Classes (using `@dataclass`)

```python
@dataclass
class ParsedMessage:
    id: str
    actor: str  # "user", "assistant", or "system"
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ParsedConversation:
    title: str
    source: str  # e.g. "chatgpt", "claude"
    external_id: str | None
    created_at: datetime
    updated_at: datetime
    messages: list[ParsedMessage]
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ImportResult:
    imported: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)
```

### 2. BaseAdapter Protocol

```python
class BaseAdapter(Protocol):
    """Interface for LLM provider conversation importers."""

    @property
    def provider_name(self) -> str:
        """Provider identifier (e.g., 'chatgpt')."""
        ...

    def parse(self, file_path: Path) -> list[ParsedConversation]:
        """Parse provider export file into conversations."""
        ...

    def validate_format(self, file_path: Path) -> bool:
        """Check if file is valid format for this provider."""
        ...
```

### 3. Utility Functions

```python
def normalize_timestamp(raw: float | str | int | None) -> datetime:
    """Convert various timestamp formats to UTC datetime.

    Handles:
    - Unix epoch floats (e.g., 1234567890.123)
    - ISO format strings
    - Integer timestamps
    - None (returns datetime.now(UTC))
    """

def generate_conversation_hash(source: str, title: str, created_at: datetime) -> str:
    """Generate SHA-256 hash for conversation deduplication.

    Args:
        source: Provider name (e.g., "chatgpt")
        title: Conversation title
        created_at: Conversation creation timestamp

    Returns:
        64-character hex digest string
    """

def deduplicate_messages(messages: list[ParsedMessage]) -> list[ParsedMessage]:
    """Remove duplicate messages based on (actor, timestamp, content[:100]).

    Returns:
        Deduplicated list preserving original order.
    """
```

## Conventions
- Google-style docstrings on everything
- Full type hints (`from __future__ import annotations` at top)
- Use `from typing import Protocol, Any` and `from dataclasses import dataclass, field`
- Use `hashlib.sha256` for hashing
- Use `datetime.fromtimestamp(ts, tz=timezone.utc)` for Unix timestamps
- Use `datetime.fromisoformat()` for ISO strings

## Acceptance Criteria
- [ ] All 3 dataclasses defined with proper defaults
- [ ] BaseAdapter Protocol has all 3 methods
- [ ] `normalize_timestamp` handles float, str, int, None
- [ ] `generate_conversation_hash` returns consistent 64-char hex strings
- [ ] `deduplicate_messages` removes exact duplicates, preserves order
- [ ] File has no imports from other vault modules (fully standalone)

---

## Console Prompt

```
Create vault/ingestion/base.py — a standalone module defining the base adapter interface for the LLM Memory Vault. Include: ParsedMessage dataclass (id, actor, content, timestamp, metadata), ParsedConversation dataclass (title, source, external_id, created_at, updated_at, messages, metadata), ImportResult dataclass (imported, skipped, failed, errors), BaseAdapter Protocol (provider_name property, parse method, validate_format method), and utility functions normalize_timestamp (handles float/str/int/None to UTC datetime), generate_conversation_hash (SHA-256 of source:title:created_at), deduplicate_messages (by actor+timestamp+content[:100]). Use Google-style docstrings and full type hints. No imports from other vault modules.
```
