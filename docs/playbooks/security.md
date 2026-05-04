# Security Playbook

Operational guidelines for keeping ProjectMemento secure as it evolves from a local LLM conversation vault into a universal AI memory layer.

ProjectMemento will hold sensitive personal, project and client context. The security model must therefore assume that memory is valuable, long-lived and potentially more sensitive than the original prompts that created it.

## Security Principles

- **Local-first authority**: The canonical memory store runs on Richard-controlled infrastructure by default.
- **Fail closed**: If a policy, namespace or sensitivity level is unknown, deny access or stage for human review.
- **Governed writes**: Agents do not write directly to approved memory. They write to staging first.
- **Approved reads only**: Local models and agents retrieve approved records by default.
- **No cross-client leakage**: Lily's Kitchen, HelpDesQ, Ricambio and future clients must remain isolated.
- **Human visibility**: Obsidian export is useful, but must obey sensitivity and export policies.
- **Audit everything**: Every write, approval, rejection, export, retrieval and deletion should be auditable.
- **Minimise plaintext**: Store only necessary metadata in plaintext. Encrypt source/full content.

## Proactive Measures

- **Dependency Scanning**: Handled by Dependabot. Review PRs weekly.
- **Static Analysis**: CodeQL runs on every PR. Zero warnings allowed in `main`.
- **Secret Scanning**: GitHub Secret Scanning is enabled. Never commit `.env` files.
- **Pre-commit controls**: Ruff, Black, MyPy and secret scanning should run locally before commit.
- **Threat modelling**: Any new writer, retrieval endpoint, exporter or client namespace requires a short threat model.

## Data Security Model

- **Encryption at rest**: All message/source/full content stored as encrypted blobs.
- **Metadata minimisation**: Plaintext metadata should be limited to what is required for search, governance, audit and routing.
- **Key derivation**: Use Argon2id with strong parameters.
- **Per-record/per-conversation key strategy**: Use HKDF-derived keys to limit blast radius.
- **Session tokens**: Short-lived tokens gate sensitive operations.
- **No plaintext secrets**: Never log passphrases, keys, tokens or decrypted content.
- **Local embeddings for sensitive content**: Restricted/client-confidential content should be embedded locally unless explicitly approved otherwise.

## Namespace and Sensitivity Model

Every memory must have a namespace and sensitivity level.

### Initial namespaces

| Namespace | Purpose |
| --- | --- |
| `personal` | Richard's personal context, preferences, plans and private notes |
| `system` | Architecture, infrastructure and internal ProjectMemento/WorkOS knowledge |
| `public` | Content safe for publishing or general reuse |
| `client/lily` | Lily's Kitchen / Nestle Purina-related knowledge |
| `client/helpdesq` | HelpDesQ / Optimal Tech Group-related knowledge |
| `client/ricambio` | Ricambio-related knowledge |
| `client/<name>` | Future client-specific memory |

### Sensitivity levels

| Sensitivity | Meaning | Default export/read behaviour |
| --- | --- | --- |
| `public` | Safe to publish | Can be exported and retrieved broadly |
| `internal` | Richard/private internal use | Retrieve only for Richard-controlled agents |
| `client_confidential` | Client-specific confidential context | Only within matching namespace and approved tools |
| `restricted` | Highly sensitive, credentials, PII, legal, HR or regulated data | No export by default; human approval required for any use |

## Write Governance

All non-human writers should use this pattern:

```text
Agent output -> Write API -> policy check -> staged memory -> review -> approved/rejected/superseded
```

### Required write metadata

- writer identity: `claude`, `codex`, `chatgpt`, `perplexity`, `n8n`, `github`, `obsidian`, `manual`
- source URI or source reference
- namespace
- sensitivity
- proposed memory type
- confidence score
- tags
- retention policy
- created timestamp

### Write rules

- Unknown writer: reject or quarantine.
- Unknown namespace: reject or stage for admin classification.
- Missing sensitivity: default to `restricted`.
- Client namespace mismatch: reject.
- Potential PII detected: stage as `restricted` until reviewed.
- High-confidence duplicate: link to existing memory rather than create new one.
- Conflicting memory: stage as possible supersession, do not silently overwrite.

## Read Governance

Retrieval must be scoped by policy.

### Required read controls

- caller identity/profile
- allowed namespaces
- allowed sensitivity levels
- purpose/task description where possible
- retrieval audit event
- result limit and context-pack size limit

### Default policy

- Return approved memories only.
- Do not return `restricted` memories unless explicitly authorised.
- Do not cross client namespaces.
- Do not include raw source content unless the caller is authorised.
- Prefer summaries over full content for prompt/RAG context.

## Obsidian Export Policy

Obsidian is a human-visible mirror, not the canonical store.

### Export rules

- Export approved memories only.
- Export `public` and `internal` memories by default if enabled.
- Export `client_confidential` only to a clearly separated client folder and only if local vault security is acceptable.
- Never export `restricted` by default.
- Include front matter with `memento_id`, `namespace`, `sensitivity`, `status`, `source_system`, `created`, `updated`, and tags.
- Obsidian edits should not overwrite canonical memory directly. They should return through a staging workflow.

## PII and Confidentiality Controls

- Use Presidio and LLM Guard for pattern and NER-based detection.
- Treat names, email addresses, phone numbers, addresses, credentials, customer records, HR content, legal content and regulated data as sensitive.
- Redact before sending to any external LLM unless a human has approved the data flow.
- Keep raw client data out of public model prompts by default.
- Keep source documents encrypted and retrieve only distilled summaries where possible.

## Security-Critical Tasks

The following must be reviewed carefully before merge:

- Key derivation and encrypted blob storage
- Memory approval workflow
- Access control and namespace enforcement
- Writer authentication
- Retrieval filtering
- Obsidian exporter policy
- Deletion/forgetting/retention implementation
- Any cloud LLM write integration
- Any client-confidential ingestion path

## Incident Response

1. **Report**: Report vulnerabilities to the security email (see [SECURITY.md](../../SECURITY.md)).
2. **Contain**: Disable affected writer/retrieval/export integration if needed.
3. **Triage**: Confirm scope, affected namespaces, exposed records and audit trail.
4. **Fix**: Develop a patch in a private fork or branch.
5. **Review**: Security-critical fixes require explicit review.
6. **Release**: Merge fix to `main` and tag a new release.
7. **Disclose**: Publish a Security Advisory where appropriate.
8. **Remediate memory**: Supersede, expire, redact or delete affected memories as needed.

## Best Practices

- Use least privilege for CI tokens.
- Mask all secrets in CI logs.
- Regularly audit third-party actions used in workflows.
- Keep writer API tokens scoped and revocable.
- Rotate tokens after suspected exposure.
- Back up encrypted stores and test restore workflows.
- Keep a separate test namespace for synthetic data.
- Never test client-confidential flows with real data until policy enforcement is working.
