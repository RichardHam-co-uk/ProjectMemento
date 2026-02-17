#!/bin/bash

# This script creates all remaining task prompt files for Phase 1

# Day 2 tasks
cat > tasks/task_1.2.1_orm_models.txt << 'EOF'
# TASK 1.2.1: Define ORM Models

[Full RISEN prompt from Phase 1 plan - Task 1.2.1: Define ORM Models]
See PHASE1_DETAILED_PLAN.md section "Task 1.2.1: Define ORM Models" for complete prompt with:
- Role: Database architect expert in SQLAlchemy and security
- Instructions: Create 5 models (Conversation, Message, Artifact, PIIFinding, AuditEvent)
- Safety constraints: No plaintext sensitive content, foreign keys enabled
- Example code provided
- Acceptance criteria defined

Key deliverable: vault/storage/models.py with complete SQLAlchemy models
EOF

cat > tasks/task_1.2.2_migrations.txt << 'EOF'
# TASK 1.2.2: Create Migration System

[Full RISEN prompt from Phase 1 plan - Task 1.2.2: Create Migration System]
See PHASE1_DETAILED_PLAN.md section "Task 1.2.2: Create Migration System" for complete prompt.

Key deliverable: vault/storage/migrations.py with simple version tracking
EOF

# Day 3 tasks
cat > tasks/task_1.3.1_key_derivation.txt << 'EOF'
# TASK 1.3.1: Implement Key Derivation (SECURITY CRITICAL)

[Full RISEN prompt from Phase 1 plan - Task 1.3.1: Implement Key Derivation]
See PHASE1_DETAILED_PLAN.md section "Task 1.3.1: Implement Key Derivation" for complete prompt.

CRITICAL: This is security-critical code. Must use:
- Argon2id for passphrase hashing
- HKDF for key derivation
- Proper error handling (fail closed)
- No logging of keys/passphrases

Key deliverable: vault/security/crypto.py with KeyManager class
EOF

cat > tasks/task_1.3.2_blob_storage.txt << 'EOF'
# TASK 1.3.2: Implement Blob Storage (SECURITY CRITICAL)

[Full RISEN prompt from Phase 1 plan - Task 1.3.2: Implement Blob Storage]
See PHASE1_DETAILED_PLAN.md section "Task 1.3.2: Implement Blob Storage" for complete prompt.

CRITICAL: All content must be encrypted before disk write.

Key deliverable: vault/storage/blobs.py with BlobStore class
EOF

# Day 4 tasks  
cat > tasks/task_1.4.1_database_wrapper.txt << 'EOF'
# TASK 1.4.1: Implement Database Wrapper

[Full RISEN prompt from Phase 1 plan - Task 1.4.1: Implement Database Wrapper]
See PHASE1_DETAILED_PLAN.md section "Task 1.4.1: Implement Database Wrapper" for complete prompt.

Key deliverable: vault/storage/db.py with VaultDB class
EOF

cat > tasks/task_1.4.2_cli_init.txt << 'EOF'
# TASK 1.4.2: Implement `vault init` Command

[Full RISEN prompt from Phase 1 plan - Task 1.4.2: Implement `vault init` Command]
See PHASE1_DETAILED_PLAN.md section "Task 1.4.2: Implement `vault init` Command" for complete prompt.

Key deliverable: vault/cli/main.py with init command
EOF

# Day 5 tasks
cat > tasks/task_1.5.1_session_tokens.txt << 'EOF'
# TASK 1.5.1: Implement Session Token System (SECURITY CRITICAL)

[Full RISEN prompt from Phase 1 plan - Task 1.5.1: Implement Session Token System]
See PHASE1_DETAILED_PLAN.md section "Task 1.5.1: Implement Session Token System" for complete prompt.

CRITICAL: Session tokens must be cryptographically secure.

Key deliverable: vault/security/session.py with SessionManager class
EOF

cat > tasks/task_1.5.2_cli_session_integration.txt << 'EOF'
# TASK 1.5.2: Integrate Session into CLI

[Full RISEN prompt from Phase 1 plan - Task 1.5.2: Integrate Session into CLI]
See PHASE1_DETAILED_PLAN.md section "Task 1.5.2: Integrate Session into CLI" for complete prompt.

Key deliverable: Updated vault/cli/main.py with session management
EOF

# Day 6-7 tasks
cat > tasks/task_1.6.1_base_adapter.txt << 'EOF'
# TASK 1.6.1: Implement Base Adapter Interface

[Full RISEN prompt from Phase 1 plan - Task 1.6.1: Implement Base Adapter Interface]
See PHASE1_DETAILED_PLAN.md section "Task 1.6.1: Implement Base Adapter Interface" for complete prompt.

Key deliverable: vault/ingestion/base.py with BaseAdapter protocol
EOF

cat > tasks/task_1.6.2_chatgpt_adapter.txt << 'EOF'
# TASK 1.6.2: Implement ChatGPT Adapter

[Full RISEN prompt from Phase 1 plan - Task 1.6.2: Implement ChatGPT Adapter]
See PHASE1_DETAILED_PLAN.md section "Task 1.6.2: Implement ChatGPT Adapter" for complete prompt.

Key deliverable: vault/ingestion/chatgpt.py with ChatGPTAdapter class
EOF

# Day 8 tasks
cat > tasks/task_1.8.1_import_pipeline.txt << 'EOF'
# TASK 1.8.1: Implement Import Pipeline

[Full RISEN prompt from Phase 1 plan - Task 1.8.1: Implement Import Pipeline]
See PHASE1_DETAILED_PLAN.md section "Task 1.8.1: Implement Import Pipeline" for complete prompt.

Key deliverable: vault/ingestion/pipeline.py with ImportPipeline class
EOF

cat > tasks/task_1.8.2_cli_import_command.txt << 'EOF'
# TASK 1.8.2: Implement `vault import` Command

[Full RISEN prompt from Phase 1 plan - Task 1.8.2: Implement `vault import` Command]
See PHASE1_DETAILED_PLAN.md section "Task 1.8.2: Implement `vault import` Command" for complete prompt.

Key deliverable: Updated vault/cli/main.py with import command
EOF

# Day 9-10 tasks
cat > tasks/task_1.9.1_cli_list.txt << 'EOF'
# TASK 1.9.1: Implement `vault list` Command

[Full RISEN prompt from Phase 1 plan - Task 1.9.1: Implement `vault list` Command]
See PHASE1_DETAILED_PLAN.md section "Task 1.9.1: Implement `vault list` Command" for complete prompt.

Key deliverable: vault/cli/main.py with list command
EOF

cat > tasks/task_1.9.2_cli_show.txt << 'EOF'
# TASK 1.9.2: Implement `vault show` Command

[Full RISEN prompt from Phase 1 plan - Task 1.9.2: Implement `vault show` Command]
See PHASE1_DETAILED_PLAN.md section "Task 1.9.2: Implement `vault show` Command" for complete prompt.

Key deliverable: vault/cli/main.py with show command
EOF

cat > tasks/task_1.9.3_cli_stats.txt << 'EOF'
# TASK 1.9.3: Implement `vault stats` Command

[Full RISEN prompt from Phase 1 plan - Task 1.9.3: Implement `vault stats` Command]
See PHASE1_DETAILED_PLAN.md section "Task 1.9.3: Implement `vault stats` Command" for complete prompt.

Key deliverable: vault/cli/main.py with stats command
EOF

cat > tasks/task_1.9.4_error_handling.txt << 'EOF'
# TASK 1.9.4: Add Error Handling & Help Text

[Full RISEN prompt from Phase 1 plan - Task 1.9.4: Add Error Handling & Help Text]
See PHASE1_DETAILED_PLAN.md section "Task 1.9.4: Add Error Handling & Help Text" for complete prompt.

Key deliverable: Polish all CLI commands with comprehensive error handling
EOF

echo "✓ All task prompt files created successfully"
