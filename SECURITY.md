# Security Policy

## Core Philosophy: Zero Trust & Local First

The LLM Memory Vault is designed with a "paranoid" security model. We assume that:
1. All input data may contain PII.
2. The storage medium could be inspected.
3. External APIs are untrusted for sensitive data.

## Data Classification

| Level | Description |
|-------|-------------|
| **PUBLIC** | Can be shared freely. |
| **INTERNAL** | Personal context, no external sharing. |
| **SENSITIVE** | Must be redacted before any processing. |
| **SECRET** | Purge immediately, never store. |

## PII Handling

- **Detection**: All inputs pass through PII detection (Presidio + LLM Guard).
- **Redaction**: Detected PII is masked or tokenised before storage.
- **Encryption**: All content blobs are encrypted at rest using AES-256 (Fernet).

## Supported Versions

| Version     | Supported               |
| ----------- | ----------------------- |
| 0.1.x (dev) | Active development |

> **Note:** Project Memento is in active development. No stable release has been published yet.

## Reporting a Vulnerability

If you discover a security vulnerability within this project, please send an e-mail to tbc@richardham.co.uk. All security vulnerabilities will be promptly addressed.

Please include the following in your report:
- Type of issue (e.g., key exposure, encryption bypass, PII leak, etc.)
- Location/path of the issue
- Steps to reproduce
- Potential impact

We will acknowledge receipt of your vulnerability report within 48 hours and will send you updates during our remediation process.

## Our Commitment
- We will not disclose the vulnerability to third parties without your consent.
- We will provide a fix in a timely manner.
- We will publicise the vulnerability (with your credit) once it is patched.
