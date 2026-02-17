# LLM Memory Vault - Phase 1 Detailed Implementation Plan

## Phase 1 Overview: Foundation & ChatGPT Import

**Duration:** 2 weeks (10 working days)  
**Goal:** Working development environment with ChatGPT conversation import capability  
**Team:** Tiered LLM allocation based on task complexity  
**Final Deliverable:** Successfully import 100+ ChatGPT conversations into encrypted local storage

---

## Team Structure & Capabilities

### Tier 1: Local LLMs (Llama3b, DeepSeek-Coder, Qwen)
**Capabilities:**
- Boilerplate code generation
- Format conversion (JSON → Python objects)
- Simple CRUD operations
- Template population
- Basic validation logic

**Limitations:**
- May hallucinate on complex logic
- Requires clear examples
- Best for deterministic tasks

**Cost:** $0 (local compute only)

---

### Tier 2: Budget Cloud (GPT-4o-mini, Claude Haiku 4.5)
**Capabilities:**
- Documentation generation
- Test case creation
- Code review for simple bugs
- Configuration file creation
- Error handling implementation

**Limitations:**
- Limited context for complex systems
- May miss edge cases

**Cost:** ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens

---

### Tier 3: Advanced (Claude Sonnet 4.5, GPT-4o)
**Capabilities:**
- Architecture decisions
- Complex logic implementation
- Security-critical code
- Integration between components
- Debugging complex issues

**Cost:** ~$3 per 1M input tokens, ~$15 per 1M output tokens

---

### Tier 4: Expert (Claude Opus 4.5, Perplexity)
**Capabilities:**
- Security architecture review
- Performance optimization
- Research on best practices
- Complex refactoring

**Cost:** ~$15 per 1M input tokens, ~$75 per 1M output tokens  
**Usage:** Reserve for critical decisions only in Phase 1

---

## Milestone Breakdown

### 🎯 Milestone 1.1: Project Scaffolding (Days 1-2)
**Objective:** Complete project structure with all skeleton files  
**Success Criteria:**
- ✅ All directories and `__init__.py` files created
- ✅ `pyproject.toml` with all dependencies
- ✅ `poetry install` completes successfully
- ✅ `vault --help` shows command structure (even if empty)
- ✅ Pre-commit hooks configured

---

### 🎯 Milestone 1.2: Core Infrastructure (Days 3-5)
**Objective:** Database schema, encryption, and blob storage working  
**Success Criteria:**
- ✅ SQLite database created with all tables
- ✅ Encrypted blob storage functional
- ✅ Master key derivation from passphrase working
- ✅ `vault init` command creates new vault
- ✅ Can store and retrieve encrypted blobs
- ✅ All operations require valid passphrase

---

### 🎯 Milestone 1.3: ChatGPT Ingestion (Days 6-8)
**Objective:** Parse and import ChatGPT JSON exports  
**Success Criteria:**
- ✅ ChatGPT JSON format fully parsed
- ✅ Conversations normalized to internal schema
- ✅ Deduplication via content hashing works
- ✅ `vault import chatgpt <file>` command functional
- ✅ Can import 100+ conversations in <2 minutes
- ✅ All message content encrypted in blob storage

---

### 🎯 Milestone 1.4: Basic CLI & Retrieval (Days 9-10)
**Objective:** User can view imported conversations  
**Success Criteria:**
- ✅ `vault list` shows all conversations
- ✅ `vault show <id>` displays conversation details
- ✅ `vault stats` shows import statistics
- ✅ Session token management working (30min expiry)
- ✅ Rich formatting for terminal output
- ✅ Error handling for invalid inputs

---

## Detailed Task Breakdown

---

## DAY 1: Project Setup & Scaffolding

### Task 1.1.1: Create Repository Structure
**Assigned to:** Tier 1 (DeepSeek-Coder)  
**Estimated Time:** 1 hour  
**Dependencies:** None

**Deliverables:**
```
llm_memory_vault/
├── README.md
├── LICENSE (MIT)
├── .gitignore
├── .editorconfig
├── pyproject.toml
├── vault/
│   ├── __init__.py
│   ├── config/
│   ├── ingestion/
│   ├── classification/
│   ├── sanitization/
│   ├── distillation/
│   ├── storage/
│   ├── retrieval/
│   ├── api/
│   ├── cli/
│   └── security/
├── tests/
│   └── fixtures/
└── config_examples/
```

**CARE Prompt for DeepSeek-Coder:**
```
Context: Creating LLM Memory Vault project structure
Action: Generate complete directory tree with all __init__.py files
Result: Working Python package structure
Example: See best-practice-repo-template structure

Execute:
1. Create all directories
2. Add __init__.py to each package
3. Add proper module docstrings
4. Include .gitignore (ignore *.db, *.key, vault_data/)
```

**Acceptance Criteria:**
- [ ] All directories exist
- [ ] All packages have `__init__.py`
- [ ] Can import `vault` package
- [ ] `.gitignore` excludes sensitive files

---

### Task 1.1.2: Configure Dependencies (pyproject.toml)
**Assigned to:** Tier 2 (Claude Haiku 4.5)  
**Estimated Time:** 30 minutes  
**Dependencies:** Task 1.1.1

**Deliverable:** Complete `pyproject.toml` with Poetry configuration

**RISEN Prompt:**
```
Role: Python packaging expert
Instructions:
1. Create pyproject.toml for Poetry
2. Add all dependencies from tech stack
3. Configure dev dependencies (pytest, black, mypy, ruff)
4. Set Python version constraint (>=3.11)
5. Add CLI entry point: vault = "vault.cli.main:app"

Safety:
- Pin major versions for stability
- Use compatible release (~=) for minor updates
- Include security-focused dependencies

Example dependencies:
- fastapi = "^0.109.0"
- typer = "^0.9.0"
- cryptography = "^42.0.0"
- sqlalchemy = "^2.0.25"
- qdrant-client = "^1.7.0"
- pydantic = "^2.5.0"

Next: `poetry install` completes without errors
```

**Acceptance Criteria:**
- [ ] `poetry install` successful
- [ ] All core dependencies installed
- [ ] Dev tools configured (black, ruff, mypy)
- [ ] CLI entry point registered

---

### Task 1.1.3: Create Configuration Models
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 1 hour  
**Dependencies:** Task 1.1.2

**Deliverable:** `vault/config/models.py` with Pydantic models

**RISEN Prompt:**
```
Role: Configuration architect
Instructions:
1. Create Pydantic models for all config sections
2. Include validation and defaults
3. Support environment variable overrides
4. Add docstrings for each field

Models needed:
- VaultConfig (main config)
- DatabaseConfig (SQLite settings)
- BlobConfig (encryption settings)
- VectorConfig (Qdrant settings)
- SecurityConfig (policies)

Safety:
- No hardcoded secrets
- Validate file paths exist or can be created
- Secure defaults (e.g., 256-bit keys)

Example:
```python
from pydantic import BaseModel, Field
from pathlib import Path

class VaultConfig(BaseModel):
    vault_root: Path = Field(
        default=Path("vault_data"),
        description="Root directory for vault storage"
    )
    db_path: Path = Field(
        default=Path("vault_data/vault.db"),
        description="SQLite database file"
    )
```

Next: Can load config from YAML and environment variables
```

**Acceptance Criteria:**
- [ ] All config models defined
- [ ] Environment variable support working
- [ ] Validation catches invalid configs
- [ ] Type hints complete

---

### Task 1.1.4: Setup Pre-commit Hooks
**Assigned to:** Tier 1 (Llama3b)  
**Estimated Time:** 30 minutes  
**Dependencies:** Task 1.1.2

**Deliverable:** `.pre-commit-config.yaml`

**CARE Prompt:**
```
Context: Need code quality checks before commits
Action: Create pre-commit configuration
Result: Automated linting and formatting
Example: Standard Python pre-commit setup

Include hooks:
- black (code formatting)
- ruff (linting)
- mypy (type checking)
- check-yaml
- check-json
- detect-private-key (security)
```

**Acceptance Criteria:**
- [ ] Pre-commit hooks install successfully
- [ ] Hooks run on `git commit`
- [ ] All hooks pass on initial codebase

---

## DAY 2: Core Data Models

### Task 1.2.1: Define ORM Models
**Assigned to:** Tier 3 (Claude Sonnet 4.5)  
**Estimated Time:** 2 hours  
**Dependencies:** Task 1.1.3

**Deliverable:** `vault/storage/models.py` with SQLAlchemy models

**RISEN Prompt:**
```
Role: Database architect expert in SQLAlchemy and security
Context: Need ORM models for conversations, messages, artifacts

Instructions:
1. Create SQLAlchemy models for:
   - Conversation
   - Message
   - Artifact
   - PIIFinding
   - AuditEvent

2. Each model should have:
   - Primary key (UUID or SHA256 hash)
   - Timestamps (created_at, updated_at)
   - Foreign key relationships
   - Appropriate indexes
   - JSON fields for flexible metadata

3. Add table-level constraints:
   - NOT NULL for required fields
   - CHECK constraints for enums
   - UNIQUE constraints where needed

4. Use enums for:
   - SensitivityLevel (PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED)
   - ActorType (USER, ASSISTANT, SYSTEM)
   - ArtifactType (SHORT_SUMMARY, LONG_SUMMARY, KEY_POINTS, etc.)
   - PIIType (EMAIL, PHONE, SSN, etc.)

Safety:
- Never store plaintext sensitive content
- All content via blob_uuid references
- Enable foreign key constraints
- Use WAL mode for SQLite

Example:
```python
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import enum

Base = declarative_base()

class SensitivityLevel(enum.Enum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"

class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(String, primary_key=True)  # SHA256 hash
    source = Column(String, nullable=False, index=True)
    external_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    sensitivity = Column(Enum(SensitivityLevel), nullable=False, default=SensitivityLevel.INTERNAL)
    domain_tags = Column(JSON, nullable=True)  # List of tags
    message_count = Column(Integer, default=0)
    hash = Column(String, nullable=False, unique=True)
```

Next: Can create tables, insert records, query with relationships
```

**Acceptance Criteria:**
- [ ] All 5 models defined
- [ ] Relationships work (conversation.messages)
- [ ] Enums properly constrained
- [ ] Can create/migrate schema
- [ ] Indexes created

---

### Task 1.2.2: Create Migration System
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 1 hour  
**Dependencies:** Task 1.2.1

**Deliverable:** `vault/storage/migrations.py`

**CARE Prompt:**
```
Context: Need database schema versioning
Action: Create simple migration system (not Alembic)
Result: Can upgrade/downgrade schema versions
Example: Simple version table + upgrade scripts

Implement:
1. SchemaVersion table (version number, applied_at)
2. Migration class with up/down methods
3. apply_migrations() function
4. current_version() function

Keep it simple for v1 - just track version number
```

**Acceptance Criteria:**
- [ ] Can track schema version
- [ ] Initial migration creates all tables
- [ ] `vault init` runs migrations
- [ ] Version increments correctly

---

## DAY 3: Encryption & Blob Storage

### Task 1.3.1: Implement Key Derivation
**Assigned to:** Tier 3 (Claude Sonnet 4.5) - Security Critical  
**Estimated Time:** 2 hours  
**Dependencies:** None

**Deliverable:** `vault/security/crypto.py`

**RISEN Prompt:**
```
Role: Cryptographic security engineer, expert in key derivation and encryption
Context: Need secure passphrase-based key derivation for blob encryption

Instructions:
1. Implement KeyManager class:
   ```python
   class KeyManager:
       def __init__(self, vault_root: Path):
           self.vault_root = vault_root
           self.salt_file = vault_root / ".salt"
       
       def derive_master_key(self, passphrase: str) -> bytes:
           """Derive 256-bit master key from passphrase using Argon2."""
           # Load or generate salt
           # Use Argon2id with strong parameters
           # Return 32-byte key
       
       def derive_conversation_key(
           self, 
           master_key: bytes, 
           conversation_id: str
       ) -> bytes:
           """Derive per-conversation key using HKDF."""
           # HKDF(master_key, salt=conversation_id, info=b"content")
   ```

2. Use cryptography library:
   - Argon2 for passphrase → master key
   - HKDF for master key → conversation keys
   - Fernet for symmetric encryption

3. Parameters:
   - Argon2: time_cost=4, memory_cost=65536, parallelism=4
   - Salt: 16 bytes random, stored in .salt file
   - Output: 256-bit keys

Safety:
- Never log keys or passphrases
- Secure memory handling (no string copies)
- Validate key strength
- Fail closed on any error
- Use secrets module for randomness

Example usage:
```python
km = KeyManager(Path("vault_data"))
master_key = km.derive_master_key("my-secure-passphrase")
conv_key = km.derive_conversation_key(master_key, "conv-abc123")
```

Next: Can derive keys deterministically, same passphrase → same key
```

**Acceptance Criteria:**
- [ ] Argon2 key derivation working
- [ ] HKDF conversation keys working
- [ ] Salt persistence working
- [ ] Same passphrase produces same key
- [ ] Different passphrases produce different keys
- [ ] Security review passed

---

### Task 1.3.2: Implement Blob Storage
**Assigned to:** Tier 3 (Claude Sonnet 4.5) - Security Critical  
**Estimated Time:** 3 hours  
**Dependencies:** Task 1.3.1

**Deliverable:** `vault/storage/blobs.py`

**RISEN Prompt:**
```
Role: Secure storage engineer
Context: Need encrypted blob storage for conversation content

Instructions:
1. Implement BlobStore class:
   ```python
   class BlobStore:
       def __init__(self, root_path: Path, key_manager: KeyManager):
           self.root = root_path
           self.key_manager = key_manager
       
       def store(
           self, 
           content: bytes, 
           conversation_id: str,
           blob_id: str | None = None
       ) -> str:
           """Encrypt content and store, return blob UUID."""
           # 1. Generate blob_id (UUID4) if not provided
           # 2. Derive conversation key
           # 3. Encrypt with Fernet
           # 4. Write to root/blobs/{first_2_chars}/{blob_id}.enc
           # 5. Return blob_id
       
       def retrieve(
           self, 
           blob_id: str, 
           conversation_id: str
       ) -> bytes:
           """Decrypt and return blob content."""
           # 1. Derive conversation key
           # 2. Read encrypted file
           # 3. Decrypt with Fernet
           # 4. Return plaintext bytes
       
       def delete(self, blob_id: str) -> bool:
           """Securely delete blob file."""
           # 1. Find file
           # 2. Overwrite with random data (3 passes)
           # 3. Delete file
           # 4. Return success
   ```

2. File organization:
   - Split blobs into subdirectories by first 2 hex chars
   - Example: blob abc123... → blobs/ab/abc123.enc
   - Prevents too many files in one directory

3. Error handling:
   - FileNotFoundError → clear error message
   - DecryptionError → log + raise (wrong key or corrupted)
   - IOError → handle gracefully

Safety:
- Atomic writes (write to .tmp, rename)
- Validate blob_id format (UUID)
- Encrypt before any disk write
- Secure deletion for sensitive data
- File permissions: 0600 (user read/write only)

Example:
```python
km = KeyManager(Path("vault_data"))
master_key = km.derive_master_key("passphrase")
km.cache_master_key(master_key)  # Keep in memory for session

bs = BlobStore(Path("vault_data/blobs"), km)

# Store
blob_id = bs.store(
    content=b"Hello, this is secret",
    conversation_id="conv-123"
)
print(blob_id)  # "a3f2d8b1-..."

# Retrieve
content = bs.retrieve(blob_id, "conv-123")
print(content)  # b"Hello, this is secret"
```

Next: Can store/retrieve encrypted blobs, wrong key fails decryption
```

**Acceptance Criteria:**
- [ ] Can store encrypted blobs
- [ ] Can retrieve with correct key
- [ ] Decryption fails with wrong key
- [ ] File organization working (subdirectories)
- [ ] Atomic writes implemented
- [ ] Secure deletion working
- [ ] Performance: >1000 blobs/sec

---

## DAY 4: Database Setup & CLI Init

### Task 1.4.1: Implement Database Wrapper
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 2 hours  
**Dependencies:** Task 1.2.1, Task 1.2.2

**Deliverable:** `vault/storage/db.py`

**RISEN Prompt:**
```
Role: Database operations engineer
Context: Need clean wrapper around SQLAlchemy for vault operations

Instructions:
1. Create VaultDB class:
   ```python
   class VaultDB:
       def __init__(self, db_path: Path):
           self.engine = create_engine(
               f"sqlite:///{db_path}",
               connect_args={"check_same_thread": False}
           )
           self.SessionLocal = sessionmaker(bind=self.engine)
       
       def init_schema(self):
           """Create all tables and run migrations."""
       
       def get_session(self) -> Session:
           """Get database session (context manager)."""
       
       # Convenience methods
       def get_conversation(self, conv_id: str) -> Conversation | None:
       def list_conversations(
           self, 
           limit: int = 100, 
           offset: int = 0
       ) -> List[Conversation]:
       def count_conversations(self) -> int:
   ```

2. Enable SQLite optimizations:
   - WAL mode for better concurrency
   - Foreign keys enabled
   - Synchronous = NORMAL (faster, still safe)

3. Add helper methods for common queries

Safety:
- Always use parameterized queries (SQLAlchemy does this)
- Context managers for sessions
- Proper error handling

Example:
```python
db = VaultDB(Path("vault_data/vault.db"))
db.init_schema()

with db.get_session() as session:
    conv = Conversation(
        id="conv-123",
        source="chatgpt",
        title="Test"
    )
    session.add(conv)
    session.commit()

conversations = db.list_conversations(limit=10)
```

Next: Can create DB, insert/query conversations
```

**Acceptance Criteria:**
- [ ] Database creation working
- [ ] Migrations run automatically
- [ ] WAL mode enabled
- [ ] Foreign keys enforced
- [ ] Can insert and query data
- [ ] Concurrent access working

---

### Task 1.4.2: Implement `vault init` Command
**Assigned to:** Tier 3 (Claude Sonnet 4.5)  
**Estimated Time:** 2 hours  
**Dependencies:** Task 1.3.2, Task 1.4.1

**Deliverable:** `vault/cli/main.py` with `init` command

**RISEN Prompt:**
```
Role: CLI engineer, expert in Typer and secure password handling
Context: First user-facing command - initialize new vault

Instructions:
1. Create Typer application:
   ```python
   import typer
   from rich.console import Console
   from rich.prompt import Prompt
   
   app = typer.Typer()
   console = Console()
   
   @app.command()
   def init(
       vault_path: Path = typer.Option(
           Path("vault_data"),
           help="Path to vault directory"
       ),
       force: bool = typer.Option(
           False,
           help="Overwrite existing vault"
       )
   ):
       """Initialize a new LLM Memory Vault."""
       # 1. Check if vault already exists
       # 2. Prompt for passphrase (hidden input)
       # 3. Confirm passphrase
       # 4. Validate passphrase strength (min 12 chars)
       # 5. Create vault directory structure
       # 6. Initialize KeyManager (generates salt)
       # 7. Create database
       # 8. Run migrations
       # 9. Store config
       # 10. Display success message
   ```

2. Passphrase requirements:
   - Minimum 12 characters
   - Recommend 20+ with mixed case, numbers, symbols
   - Show strength indicator
   - Confirm with second entry

3. Directory structure created:
   ```
   vault_data/
   ├── .salt (random 16 bytes)
   ├── config.yaml
   ├── vault.db
   └── blobs/
   ```

4. Rich output:
   - Use panels for important messages
   - Progress spinner during init
   - Success message with next steps

Safety:
- Never echo passphrase
- Warn user to store securely
- Don't proceed if vault exists (unless --force)
- Validate all inputs

Example usage:
```bash
$ vault init
┌─────────────────────────────────────────┐
│ Initialize LLM Memory Vault             │
└─────────────────────────────────────────┘

Enter master passphrase: ********
Confirm passphrase: ********

✓ Passphrase strength: STRONG
✓ Vault directory created
✓ Encryption initialized
✓ Database schema created

Success! Vault initialized at: vault_data/

⚠ CRITICAL: Store your passphrase securely!
   Without it, your vault cannot be recovered.

Next steps:
  1. vault import chatgpt <export.json>
  2. vault list
```

Next: Can run `vault init` successfully, vault is functional
```

**Acceptance Criteria:**
- [ ] `vault init` command works
- [ ] Passphrase validation enforced
- [ ] Vault directory created correctly
- [ ] Database initialized
- [ ] Salt file created
- [ ] Cannot overwrite without `--force`
- [ ] Rich formatting looks good

---

## DAY 5: Session Management

### Task 1.5.1: Implement Session Token System
**Assigned to:** Tier 3 (Claude Sonnet 4.5) - Security Critical  
**Estimated Time:** 3 hours  
**Dependencies:** Task 1.3.1

**Deliverable:** `vault/security/session.py`

**RISEN Prompt:**
```
Role: Authentication security engineer
Context: Need session tokens to avoid re-entering passphrase

Instructions:
1. Create SessionManager class:
   ```python
   class SessionManager:
       def __init__(self, vault_root: Path):
           self.vault_root = vault_root
           self.token_file = vault_root / ".session"
           self.expiry_minutes = 30
       
       def create_session(self, master_key: bytes) -> str:
           """Create session token, cache master key."""
           # 1. Generate random token (32 bytes)
           # 2. Store encrypted master_key with expiry
           # 3. Write to .session file (0600 permissions)
           # 4. Return token
       
       def validate_token(self, token: str) -> bytes | None:
           """Validate token, return master key if valid."""
           # 1. Load .session file
           # 2. Check token match
           # 3. Check expiry
           # 4. Return cached master_key or None
       
       def clear_session(self):
           """Destroy session token."""
   ```

2. Session token format:
   ```python
   {
       "token": "hex-encoded-32-bytes",
       "created_at": "2025-02-16T10:30:00Z",
       "expires_at": "2025-02-16T11:00:00Z",
       "encrypted_master_key": "base64-encoded-fernet-encrypted-key"
   }
   ```

3. Token lifecycle:
   - Created on first successful passphrase entry
   - Cached in memory for current process
   - Stored encrypted on disk for other processes
   - Auto-expires after 30 minutes
   - Cleared on `vault lock` command

Safety:
- Token is cryptographically random
- Master key encrypted before caching
- .session file mode 0600
- Auto-cleanup expired sessions
- No token transmitted over network

Example:
```python
sm = SessionManager(Path("vault_data"))

# User enters passphrase once
km = KeyManager(Path("vault_data"))
master_key = km.derive_master_key("passphrase")
token = sm.create_session(master_key)

# Later commands use token
master_key = sm.validate_token(token)
if master_key is None:
    print("Session expired, re-enter passphrase")
```

Next: Can create session, use across commands, expires correctly
```

**Acceptance Criteria:**
- [ ] Session token creation working
- [ ] Token validation working
- [ ] Expiry enforced (30 minutes)
- [ ] Master key cached securely
- [ ] File permissions correct (0600)
- [ ] `vault lock` clears session

---

### Task 1.5.2: Integrate Session into CLI
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 1 hour  
**Dependencies:** Task 1.5.1

**Deliverable:** Update `vault/cli/main.py` with session support

**CARE Prompt:**
```
Context: CLI commands need session management
Action: Add session token handling to all commands
Result: User enters passphrase once per 30 minutes
Example: First command prompts, subsequent commands use token

Implement:
1. Common get_master_key() function:
   - Check for valid session token
   - If valid, return cached master key
   - If expired/missing, prompt for passphrase
   - Create new session after successful auth

2. Update all commands to use get_master_key()

3. Add `vault lock` command to clear session
```

**Acceptance Criteria:**
- [ ] First command prompts for passphrase
- [ ] Subsequent commands use session
- [ ] Session expires after 30 minutes
- [ ] `vault lock` clears session
- [ ] Error messages clear when session expired

---

## DAY 6-7: ChatGPT Ingestion

### Task 1.6.1: Implement Base Adapter Interface
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 1 hour  
**Dependencies:** Task 1.2.1

**Deliverable:** `vault/ingestion/base.py`

**RISEN Prompt:**
```
Role: Interface architect
Context: Need standard interface for all provider adapters

Instructions:
1. Create BaseAdapter protocol:
   ```python
   from typing import Protocol, List
   from pathlib import Path
   
   class BaseAdapter(Protocol):
       """Interface for LLM provider conversation importers."""
       
       @property
       def provider_name(self) -> str:
           """Provider identifier (e.g., 'chatgpt')."""
       
       def parse(self, file_path: Path) -> List[Conversation]:
           """
           Parse provider export file into Conversations.
           
           Returns:
               List of Conversation objects ready for storage.
           
           Raises:
               ValueError: Invalid file format
               FileNotFoundError: File doesn't exist
           """
       
       def validate_format(self, file_path: Path) -> bool:
           """Check if file is valid format for this provider."""
   ```

2. Add utility functions:
   - normalize_timestamp(raw: Any) -> datetime
   - generate_conversation_hash(source, title, first_msg_time) -> str
   - deduplicate_messages(messages: List) -> List

Next: Other adapters can implement this interface
```

**Acceptance Criteria:**
- [ ] BaseAdapter protocol defined
- [ ] Utility functions implemented
- [ ] Type hints complete
- [ ] Docstrings comprehensive

---

### Task 1.6.2: Implement ChatGPT Adapter
**Assigned to:** Tier 3 (Claude Sonnet 4.5)  
**Estimated Time:** 4 hours  
**Dependencies:** Task 1.6.1

**Deliverable:** `vault/ingestion/chatgpt.py`

**RISEN Prompt:**
```
Role: Data ingestion engineer, expert in ChatGPT export formats
Context: Need to parse OpenAI ChatGPT conversation exports

Instructions:
1. Study ChatGPT export JSON format:
   ```json
   [{
     "title": "Conversation Title",
     "create_time": 1234567890.123,
     "update_time": 1234567891.456,
     "mapping": {
       "message-uuid-1": {
         "id": "message-uuid-1",
         "message": {
           "id": "message-uuid-1",
           "author": {"role": "user"},
           "content": {
             "content_type": "text",
             "parts": ["Hello, how are you?"]
           },
           "create_time": 1234567890.5,
           "metadata": {
             "model_slug": "gpt-4"
           }
         },
         "parent": null,
         "children": ["message-uuid-2"]
       },
       "message-uuid-2": {
         "id": "message-uuid-2",
         "message": {
           "id": "message-uuid-2",
           "author": {"role": "assistant"},
           "content": {
             "content_type": "text",
             "parts": ["I'm doing well, thank you!"]
           },
           "create_time": 1234567891.0,
           "metadata": {
             "model_slug": "gpt-4"
           }
         },
         "parent": "message-uuid-1",
         "children": []
       }
     }
   }]
   ```

2. Implement ChatGPTAdapter:
   ```python
   class ChatGPTAdapter:
       def __init__(self):
           self.provider_name = "chatgpt"
       
       def parse(self, file_path: Path) -> List[Conversation]:
           # 1. Load JSON file
           # 2. Validate structure
           # 3. For each conversation in array:
           #    a. Extract title, timestamps
           #    b. Flatten mapping tree to linear messages
           #    c. Extract model metadata
           #    d. Generate conversation hash
           #    e. Create Conversation object
           #    f. Create Message objects
           # 4. Return list of Conversations
       
       def _flatten_message_tree(self, mapping: dict) -> List[dict]:
           """Convert tree structure to linear message list."""
           # Follow parent/children to get chronological order
       
       def _extract_content(self, message: dict) -> str:
           """Extract text content from message parts."""
           # Handle different content types
       
       def validate_format(self, file_path: Path) -> bool:
           # Check if JSON has expected structure
   ```

3. Handle edge cases:
   - Empty conversations (no messages)
   - Deleted messages (null in mapping)
   - System messages
   - Code interpreter outputs
   - Image content (skip in v1, just note presence)
   - Very long conversations (>1000 messages)

4. Metadata extraction:
   - Model used (gpt-3.5-turbo, gpt-4, etc.)
   - Plugin usage (if present)
   - Conversation mode

Safety:
- Validate JSON schema before processing
- Reject files >100MB
- Handle malformed JSON gracefully
- No eval() or exec()
- Sanitize all user data before logging
- Count stats only (no content in logs)

Example usage:
```python
adapter = ChatGPTAdapter()

if adapter.validate_format(Path("export.json")):
    conversations = adapter.parse(Path("export.json"))
    print(f"Parsed {len(conversations)} conversations")
    
    for conv in conversations:
        print(f"  {conv.title}: {len(conv.messages)} messages")
```

Next: Can parse real ChatGPT exports successfully
```

**Acceptance Criteria:**
- [ ] Parses ChatGPT JSON format correctly
- [ ] Handles all message types
- [ ] Extracts metadata properly
- [ ] Flattens tree to linear order
- [ ] Generates consistent hashes
- [ ] Handles edge cases gracefully
- [ ] Performance: >100 conversations/minute

---

## DAY 8: Import Integration

### Task 1.8.1: Implement Import Pipeline
**Assigned to:** Tier 3 (Claude Sonnet 4.5)  
**Estimated Time:** 3 hours  
**Dependencies:** Task 1.6.2, Task 1.4.1, Task 1.3.2

**Deliverable:** `vault/ingestion/pipeline.py`

**RISEN Prompt:**
```
Role: Data pipeline engineer
Context: Orchestrate full import workflow

Instructions:
1. Create ImportPipeline class:
   ```python
   class ImportPipeline:
       def __init__(
           self,
           db: VaultDB,
           blob_store: BlobStore,
           key_manager: KeyManager
       ):
           self.db = db
           self.blob_store = blob_store
           self.km = key_manager
       
       def import_conversations(
           self,
           adapter: BaseAdapter,
           file_path: Path
       ) -> ImportResult:
           """
           Import conversations from file.
           
           Returns:
               ImportResult with stats and errors
           """
           # 1. Parse file with adapter
           # 2. For each conversation:
           #    a. Check if already exists (by hash)
           #    b. If duplicate, skip
           #    c. Store conversation in DB
           #    d. For each message:
           #       - Store content as encrypted blob
           #       - Store message metadata in DB
           #    e. Commit transaction
           # 3. Return statistics
   ```

2. Implement deduplication:
   - Check conversation hash before import
   - Skip silently if already exists
   - Optionally update if timestamps changed

3. Add transaction management:
   - Import conversation atomically (all or nothing)
   - Rollback on any error
   - Continue with next conversation if one fails

4. Progress tracking:
   - Report progress every N conversations
   - Count: imported, skipped, failed

Safety:
- Validate before storing
- Encrypt all content before disk write
- Transaction per conversation (prevent partial imports)
- Limit batch size (prevent OOM)

Example:
```python
pipeline = ImportPipeline(db, blob_store, key_manager)

adapter = ChatGPTAdapter()
result = pipeline.import_conversations(
    adapter,
    Path("chatgpt_export.json")
)

print(f"Imported: {result.imported}")
print(f"Skipped (duplicates): {result.skipped}")
print(f"Failed: {result.failed}")
```

Next: Can import full ChatGPT export successfully
```

**Acceptance Criteria:**
- [ ] Import pipeline working
- [ ] Deduplication working
- [ ] Atomic transactions per conversation
- [ ] Progress reporting accurate
- [ ] Error handling comprehensive
- [ ] Can import 100+ conversations

---

### Task 1.8.2: Implement `vault import` Command
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 2 hours  
**Dependencies:** Task 1.8.1

**Deliverable:** Update `vault/cli/main.py` with `import` command

**RISEN Prompt:**
```
Role: CLI engineer
Context: User-facing import command

Instructions:
1. Add import command:
   ```python
   @app.command()
   def import_conversations(
       provider: str = typer.Argument(..., help="Provider (chatgpt, claude, etc)"),
       file_path: Path = typer.Argument(..., help="Path to export file"),
       vault_path: Path = typer.Option(Path("vault_data"))
   ):
       """Import conversations from LLM provider."""
       # 1. Authenticate (get master key)
       # 2. Load adapter for provider
       # 3. Initialize pipeline
       # 4. Run import with progress bar
       # 5. Display results
   ```

2. Add progress bar using Rich:
   ```python
   from rich.progress import Progress, SpinnerColumn, BarColumn
   
   with Progress(
       SpinnerColumn(),
       *Progress.get_default_columns(),
       BarColumn()
   ) as progress:
       task = progress.add_task(
           f"Importing from {provider}...",
           total=None  # Unknown total
       )
       # Import with progress updates
   ```

3. Display summary:
   - Table of results
   - Warnings for failures
   - Next steps

Example:
```bash
$ vault import chatgpt ~/Downloads/conversations.json

Enter passphrase: ********

Importing from chatgpt...
████████████████████████ 100% | 150/150 conversations

┌─────────────┬───────┐
│ Status      │ Count │
├─────────────┼───────┤
│ Imported    │ 142   │
│ Skipped     │ 8     │
│ Failed      │ 0     │
└─────────────┴───────┘

✓ Import complete! 142 conversations added to vault.

Next: vault list
```

Next: Command works end-to-end, good UX
```

**Acceptance Criteria:**
- [ ] `vault import chatgpt <file>` works
- [ ] Progress bar updates correctly
- [ ] Summary table displayed
- [ ] Errors handled gracefully
- [ ] Session management working

---

## DAY 9-10: Basic Retrieval & CLI Polish

### Task 1.9.1: Implement `vault list` Command
**Assigned to:** Tier 1 (Llama3b)  
**Estimated Time:** 1 hour  
**Dependencies:** Task 1.4.1

**DELIVERABLE:** Add `list` command to CLI

**CARE Prompt:**
```
Context: User needs to see imported conversations
Action: Create vault list command with Rich table
Result: Paginated list of conversations
Example: Show title, source, date, message count

Implementation:
```python
@app.command()
def list_conversations(
    limit: int = typer.Option(20, help="Conversations per page"),
    offset: int = typer.Option(0, help="Skip N conversations"),
    source: str = typer.Option(None, help="Filter by source")
):
    # Query conversations with filters
    # Display as Rich table
```

Format:
┌──────────────────┬──────────┬────────────┬──────┐
│ Title            │ Source   │ Date       │ Msgs │
```

**Acceptance Criteria:**
- [ ] Lists conversations correctly
- [ ] Pagination working
- [ ] Source filter working
- [ ] Table formatting nice

---

### Task 1.9.2: Implement `vault show` Command
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Estimated Time:** 2 hours  
**Dependencies:** Task 1.4.1, Task 1.3.2

**Deliverable:** Add `show` command

**RISEN Prompt:**
```
Role: CLI engineer
Instructions:
1. Add show command:
   ```python
   @app.command()
   def show(
       conversation_id: str = typer.Argument(...),
       view: str = typer.Option("raw", help="raw|metadata"),
       max_messages: int = typer.Option(100)
   ):
       # 1. Authenticate
       # 2. Load conversation from DB
       # 3. If view=raw, decrypt and display messages
       # 4. If view=metadata, show stats only
       # 5. Format with Rich panels
   ```

2. Display format (raw view):
   ```
   📄 Conversation: OAuth Implementation
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Source: chatgpt
   Date: 2025-02-10 15:30:00
   Messages: 12
   
   [USER] 2025-02-10 15:30:15
   How do I implement OAuth2?
   
   [ASSISTANT] 2025-02-10 15:30:30
   OAuth2 is an authorization framework...
   ```

Safety:
- Limit message display (prevent terminal spam)
- Syntax highlighting for code
- Warn before displaying CONFIDENTIAL

Next: Can view conversation details
```

**Acceptance Criteria:**
- [ ] `vault show <id>` works
- [ ] Raw view decrypts and displays
- [ ] Metadata view shows stats
- [ ] Rich formatting looks good
- [ ] Large conversations truncated

---

### Task 1.9.3: Implement `vault stats` Command
**Assigned to:** Tier 1 (Qwen)  
**Estimated Time:** 1 hour  
**Dependencies:** Task 1.4.1

**Deliverable:** Add `stats` command

**CARE Prompt:**
```
Context: User wants vault statistics
Action: Query DB and display summary
Result: Dashboard of vault metrics
Example:
  Total Conversations: 150
  Total Messages: 3,245
  Storage Used: 45.2 MB
  Sources: chatgpt (120), claude (30)
  Oldest: 2024-01-15
  Newest: 2025-02-16
```

**Acceptance Criteria:**
- [ ] Displays accurate statistics
- [ ] Shows storage size
- [ ] Breaks down by source
- [ ] Date range shown

---

### Task 1.9.4: Add Error Handling & Help Text
**Assigned to:** Tier 2 (Claude Haiku 4.5)  
**Estimated Time:** 2 hours  
**Dependencies:** All CLI tasks

**Deliverable:** Polish all CLI commands

**CARE Prompt:**
```
Context: CLI needs comprehensive error handling
Action: Add try/catch blocks and helpful error messages
Result: User gets actionable error messages
Example:
  ❌ Error: File not found: export.json
     Check the file path and try again.
  
  ❌ Error: Invalid passphrase
     The passphrase you entered is incorrect.
```

**Acceptance Criteria:**
- [ ] All errors caught and handled
- [ ] Error messages actionable
- [ ] Help text comprehensive
- [ ] Examples in help output

---

## Testing Strategy (Continuous Throughout Phase 1)

### Unit Tests
**Assigned to:** Tier 2 (GPT-4o-mini)  
**Time:** 30 minutes per module

**Test Coverage:**
- `test_crypto.py` - Key derivation, encryption
- `test_blobs.py` - Blob storage operations
- `test_models.py` - ORM models
- `test_chatgpt_adapter.py` - Parsing logic
- `test_import_pipeline.py` - Import workflow

**Acceptance Criteria:**
- [ ] >80% code coverage
- [ ] All core functions tested
- [ ] Edge cases covered

---

### Integration Tests
**Assigned to:** Tier 3 (Claude Sonnet 4.5)  
**Time:** 2 hours

**Test Scenarios:**
1. Full workflow: init → import → list → show
2. Session management: login → use → expire → re-auth
3. Error recovery: partial import failure
4. Deduplication: import same file twice

**Acceptance Criteria:**
- [ ] All workflows tested
- [ ] Cleanup after tests
- [ ] Run in CI pipeline

---

### Manual Testing
**Assigned to:** You (Rich)  
**Time:** 1 hour final validation

**Test Cases:**
1. Real ChatGPT export (100+ conversations)
2. Invalid file formats
3. Wrong passphrase
4. Session expiry
5. Large file (>10MB)

---

## Risk Management

### High-Risk Items

**Risk 1: Key Derivation Too Slow**
- **Probability:** Medium
- **Impact:** High (UX degradation)
- **Mitigation:** 
  - Benchmark Argon2 parameters on target hardware
  - Reduce time_cost if >2 seconds
  - Cache master key in session
- **Owner:** Task 1.3.1

**Risk 2: ChatGPT Format Changes**
- **Probability:** Medium
- **Impact:** Medium
- **Mitigation:**
  - Version detection in adapter
  - Comprehensive format validation
  - Graceful degradation
- **Owner:** Task 1.6.2

**Risk 3: Import Performance**
- **Probability:** Low
- **Impact:** Medium
- **Mitigation:**
  - Batch inserts
  - Transaction batching
  - Progress reporting
- **Owner:** Task 1.8.1

---

## Resource Allocation Summary

| Tier | Tasks Assigned | Est. Hours | Est. Cost |
|------|----------------|------------|-----------|
| Tier 1 (Local) | 4 | 3.5 | $0 |
| Tier 2 (Budget) | 8 | 12 | ~$2 |
| Tier 3 (Advanced) | 7 | 19 | ~$15 |
| Tier 4 (Expert) | 0 | 0 | $0 |
| **Total** | **19** | **34.5** | **~$17** |

---

## Success Criteria Checklist

### Milestone 1.1 ✅
- [ ] All directories created
- [ ] Dependencies installed
- [ ] `vault --help` works

### Milestone 1.2 ✅
- [ ] Database schema created
- [ ] Encryption working
- [ ] `vault init` functional

### Milestone 1.3 ✅
- [ ] ChatGPT adapter working
- [ ] Import pipeline functional
- [ ] Can import 100+ conversations

### Milestone 1.4 ✅
- [ ] `vault list` works
- [ ] `vault show` works
- [ ] `vault stats` works
- [ ] Session management working

### Phase 1 Complete ✅
- [ ] All unit tests passing
- [ ] Integration tests passing
- [ ] Manual test suite passed
- [ ] Documentation updated
- [ ] Ready for Phase 2

---

## Handoff to Phase 2

**Prerequisites:**
1. ✅ 100+ conversations imported successfully
2. ✅ All encryption working correctly
3. ✅ CLI polished and user-friendly
4. ✅ Test coverage >80%

**Phase 2 Focus:**
- Classification engine (PII detection)
- Sanitization/redaction
- Domain taxonomy
- Security policies

**Estimated Start:** Day 11  
**Estimated Duration:** 2 weeks

---

*Last Updated: February 16, 2026*  
*Phase 1 Status: READY TO START*  
*Estimated Completion: February 28, 2026*
