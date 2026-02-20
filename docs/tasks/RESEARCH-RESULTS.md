# Research Results (TASK-D0)

**Date compiled:** 2026-02-20
**Method:** Synthesised from cryptography documentation, OWASP guidelines, and
OpenAI export format analysis.

---

## Query 1 — Argon2id Parameters (2025/2026)

### Recommended Values

| Parameter | Our impl | OWASP minimum | Notes |
|-----------|----------|---------------|-------|
| `time_cost` | 4 | 1 | Higher = slower but stronger |
| `memory_cost` (KB) | 65 536 | 19 456 (19 MB) | 64 MB is a good desktop default |
| `parallelism` | 4 | 1 | Match physical CPU cores |
| `hash_len` | 32 | 16 | 256-bit output |

**Verdict:** The parameters already used in `vault/security/crypto.py` meet and
exceed OWASP 2023 recommendations. At `time_cost=4`, `memory_cost=65536 KB`
(64 MB), `parallelism=4` the derivation takes ≈0.5–1.5 s on a modern laptop —
within the <2 s target.

### Correct `hash_secret_raw` Usage

```python
import argon2.low_level

master_key: bytes = argon2.low_level.hash_secret_raw(
    secret=passphrase.encode("utf-8"),
    salt=salt,                        # 16 random bytes, persisted to disk
    time_cost=4,
    memory_cost=65_536,               # kilobytes
    parallelism=4,
    hash_len=32,                      # 256-bit output
    type=argon2.low_level.Type.ID,    # Argon2id
)
```

`hash_secret_raw` returns raw `bytes` (not an encoded string).  Do **not** use
`PasswordHasher` — that API is for password verification, not key derivation.

---

## Query 2 — ChatGPT Export Format (conversations.json)

### Top-Level Structure

```json
[
  {
    "title": "Conversation Title",
    "create_time": 1700000000.0,
    "update_time": 1700000100.0,
    "conversation_id": "uuid-string",
    "mapping": { ... }
  }
]
```

A JSON **array** of conversation objects.  Some exports use `"id"` instead of
`"conversation_id"` — robust parsers should check both.

### Mapping Tree

```json
"mapping": {
  "node-id": {
    "id": "node-id",
    "message": null,          // null for root/system nodes
    "parent": "parent-id",    // null for the root node
    "children": ["child-id"]
  },
  "msg-001": {
    "id": "msg-001",
    "message": {
      "id": "msg-001",
      "author": { "role": "user" },
      "content": {
        "content_type": "text",
        "parts": ["Hello!"]
      },
      "create_time": 1700000010.0,
      "metadata": {}
    },
    "parent": "node-id",
    "children": ["msg-002"]
  }
}
```

The tree must be traversed from the root (the node whose `parent` is `null`)
following `children` links to produce a linear message list.

### `author.role` Values

| Value | Meaning |
|-------|---------|
| `"user"` | Human turn |
| `"assistant"` | GPT response |
| `"system"` | System prompt / instructions |
| `"tool"` | Function/tool call result |

### `content_type` Values

| Value | Notes |
|-------|-------|
| `"text"` | Normal text; `parts` is `list[str]` |
| `"code"` | Code block; `parts` is `list[str]` |
| `"multimodal_text"` | Mixed text + images; `parts` may contain dicts |
| `"image_asset_pointer"` | Uploaded image; `parts[0]` is an asset pointer dict |
| `"execution_output"` | Code interpreter output |
| `"tether_browse_display"` | Web browsing result |
| `"tether_quote"` | Cited source block |
| `"system_error"` | Internal error node (skip during import) |

### Message `metadata` Fields

- `model_slug` — e.g. `"gpt-4"`, `"gpt-4o"`, `"o1-preview"`
- `finish_details` — `{"type": "stop"}` etc.
- `is_complete` — boolean
- `citations` — list of cited sources (browsing mode)
- `pad` — padding (ignore)

### Parsing Notes

1. Skip nodes where `message` is `null`.
2. Skip nodes where `content.parts` is empty or contains only whitespace.
3. Flatten the tree to linear order by BFS/DFS from the root node.
4. Use `create_time` on the message object for `ParsedMessage.timestamp`;
   fall back to `create_time` on the conversation if absent.

---

## Query 3 — HKDF + Fernet Key Conversion

### Key Facts

- Fernet requires a **URL-safe base64-encoded** key passed to `Fernet()`.
- The underlying raw key material must be **exactly 32 bytes** *before*
  encoding.
- After `base64.urlsafe_b64encode(32_bytes)` the result is **44 bytes**
  (characters) — this is what `Fernet()` receives.

### Correct Pattern

```python
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

hkdf = HKDF(
    algorithm=hashes.SHA256(),
    length=32,                              # 32 raw bytes of output
    salt=conversation_id.encode("utf-8"),   # per-conversation context
    info=b"vault-conversation-content",
)
raw_key: bytes = hkdf.derive(master_key)    # 32 bytes
fernet_key: bytes = base64.urlsafe_b64encode(raw_key)  # 44 chars
fernet = Fernet(fernet_key)
```

### Validation Against `crypto.py`

The existing implementation in `vault/security/crypto.py` is **correct**:

```python
hkdf = HKDF(
    algorithm=hashes.SHA256(),
    length=32,
    salt=conversation_id.encode("utf-8"),
    info=b"vault-conversation-content",
)
derived = hkdf.derive(master_key)
return base64.urlsafe_b64encode(derived)  # returned to Fernet()
```

✅ `length=32` → 32 raw bytes → `urlsafe_b64encode` → 44-char Fernet key.
✅ Using `conversation_id` as HKDF salt ensures per-conversation key isolation.
✅ `info=b"vault-conversation-content"` adds domain separation.

No changes required to `crypto.py`.

---

## Summary

All three implementation choices already in the codebase are validated:

| Area | Status |
|------|--------|
| Argon2id params (`crypto.py`) | ✅ Meets/exceeds OWASP 2023 |
| HKDF → Fernet key derivation (`crypto.py`) | ✅ Correct pattern |
| ChatGPT JSON format (`sample_chatgpt_export.json`) | ✅ Matches real export |
