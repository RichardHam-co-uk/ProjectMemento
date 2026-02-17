# Security Playbook

Operational guidelines for keeping the project secure.

## Proactive Measures
- **Dependency Scanning**: Handled by Dependabot. Review PRs weekly.
- **Static Analysis**: CodeQL runs on every PR. Zero warnings allowed in `main`.
- **Secret Scanning**: GitHub Secret Scanning is enabled. Never commit `.env` files.

## Data Security Model
- **Encryption at rest**: All message content stored as encrypted blobs.
- **Key derivation**: Use Argon2id with strong parameters.
- **Session tokens**: Short-lived tokens gate sensitive operations.
- **No plaintext secrets**: Never log passphrases, keys, or decrypted content.

## Security-Critical Tasks
- Key derivation and blob storage must be reviewed by a Tier 3 model.
- Session management and access control require explicit tests.

## Incident Response
1. **Report**: Report vulnerabilities to the security email (see [SECURITY.md](../../SECURITY.md)).
2. **Triage**: Maintainers will confirm the bug within 24 hours.
3. **Fix**: Develop a patch in a private fork or branch.
4. **Release**: Merge fix to `main` and tag a new release.
5. **Disclose**: Publish a Security Advisory.

## Best Practices
- Use least privilege for CI tokens.
- Mask all secrets in CI logs.
- Regularly audit third-party actions used in workflows.
