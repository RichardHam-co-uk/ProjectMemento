# Task D0: Research Queries

**Tool:** Perplexity
**Effort:** Small (~10 min per query)
**Dependencies:** None — run all 3 in parallel

---

## Research Query 1: Argon2id Parameters

Paste this into Perplexity:

```
What are the recommended Argon2id parameters for a local desktop application in 2025/2026? I need specific values for: time_cost, memory_cost (in KB), parallelism, and hash_len for use with Python argon2-cffi library. Target: key derivation completes in under 2 seconds on a modern laptop. Also show how to use argon2.low_level.hash_secret_raw() (NOT PasswordHasher) to derive a 32-byte key from a passphrase and salt.
```

**Save the answer** — we'll use it to validate our crypto.py implementation.

---

## Research Query 2: ChatGPT Export Format

Paste this into Perplexity:

```
What is the exact JSON structure of a ChatGPT data export file (conversations.json) as of 2025-2026? I need: the top-level array structure, the mapping tree format with parent/children references, all possible content_type values (text, code, multimodal_text, image_asset_pointer, etc.), the author.role values, metadata fields including model_slug, and any recent format changes from OpenAI. Show a complete example of one conversation entry.
```

**Save the answer** — we'll use it to build the ChatGPT adapter and test fixtures.

---

## Research Query 3: HKDF + Fernet Key Conversion

Paste this into Perplexity:

```
In Python's cryptography library, how do I correctly combine HKDF-derived key material with Fernet encryption? Fernet requires a url-safe base64-encoded 32-byte key. Show the exact code: derive 32 bytes via HKDF (SHA-256), then convert to a Fernet-compatible key using base64.urlsafe_b64encode(). Is this the correct approach? What about the Fernet key format — does it need to be exactly 32 bytes before encoding, or 32 bytes after encoding?
```

**Save the answer** — critical for getting the key format right in crypto.py.

---

## Where to Save Results

Create a file `docs/tasks/RESEARCH-RESULTS.md` with the answers from all 3 queries. This will be referenced during implementation and code review.
