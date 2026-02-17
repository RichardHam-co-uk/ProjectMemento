"""
Session token management for the Vault.

Provides time-limited session tokens that cache the encrypted master key
on disk, so users don't need to re-enter their passphrase for every command.

Security principles:
- Raw token never stored on disk — only its SHA-256 hash
- Master key encrypted before disk write using a key derived from the token
- Session files have restricted permissions (0600 on Unix)
- Automatic expiry after configurable timeout
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import platform
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class SessionManager:
    """Manages session tokens for passphrase-free vault access.

    A session token is a random hex string held in process memory (or an
    environment variable). The corresponding master key is encrypted and
    stored on disk in the .session file. To recover the master key, the
    token is required — without it, the on-disk data is useless.

    Token lifecycle:
        1. User enters passphrase, master key is derived.
        2. create_session() generates a token, encrypts master key, writes to disk.
        3. Subsequent commands call validate_token() with the token.
        4. After timeout_minutes, the session expires and the user must re-authenticate.
        5. vault lock calls clear_session() to destroy the session immediately.

    Attributes:
        session_file: Path to the .session file.
        timeout_minutes: Session duration before expiry.
    """

    def __init__(
        self, vault_root: Path, timeout_minutes: int = 30
    ) -> None:
        """Initialize the SessionManager.

        Args:
            vault_root: Path to the vault root directory.
            timeout_minutes: Session validity duration in minutes.
        """
        self.session_file = vault_root / ".session"
        self.timeout_minutes = timeout_minutes

    def create_session(self, master_key: bytes) -> str:
        """Create a new session token and cache the master key.

        Generates a cryptographically random token, derives a session
        encryption key from it, encrypts the master key, and writes the
        session data to disk.

        Args:
            master_key: The 32-byte master key to cache.

        Returns:
            The raw session token (hex string). The caller must keep this
            in memory or an environment variable.

        Raises:
            ValueError: If master_key is not 32 bytes.
            OSError: If the session file cannot be written.
        """
        if len(master_key) != 32:
            raise ValueError(f"Master key must be 32 bytes, got {len(master_key)}")

        token = secrets.token_hex(32)
        token_hash = self._hash_token(token)
        session_key = self._derive_session_key(token)

        fernet = Fernet(session_key)
        encrypted_master_key = fernet.encrypt(master_key)

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self.timeout_minutes)

        session_data = {
            "token_hash": token_hash,
            "encrypted_master_key": base64.b64encode(encrypted_master_key).decode("ascii"),
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        self.session_file.write_text(
            json.dumps(session_data, indent=2), encoding="utf-8"
        )

        if platform.system() != "Windows":
            os.chmod(str(self.session_file), 0o600)

        return token

    def validate_token(self, token: str) -> bytes | None:
        """Validate a session token and return the cached master key.

        Checks that the token matches the stored hash, the session has not
        expired, and the master key can be successfully decrypted.

        Args:
            token: The raw session token to validate.

        Returns:
            The decrypted 32-byte master key if valid, or None if the
            token is invalid, expired, or the session file is missing.
        """
        if not self.session_file.exists():
            return None

        try:
            session_data = json.loads(
                self.session_file.read_text(encoding="utf-8")
            )
        except (json.JSONDecodeError, OSError):
            self.clear_session()
            return None

        # Constant-time comparison of token hashes to prevent timing attacks
        token_hash = self._hash_token(token)
        stored_hash = session_data.get("token_hash", "")
        if not secrets.compare_digest(token_hash, stored_hash):
            return None

        # Check expiry
        try:
            expires_at = datetime.fromisoformat(session_data["expires_at"])
        except (KeyError, ValueError):
            self.clear_session()
            return None

        if datetime.now(timezone.utc) > expires_at:
            self.clear_session()
            return None

        # Decrypt master key
        try:
            encrypted = base64.b64decode(session_data["encrypted_master_key"])
            session_key = self._derive_session_key(token)
            fernet = Fernet(session_key)
            master_key = fernet.decrypt(encrypted)
            return master_key
        except (KeyError, InvalidToken, Exception):
            self.clear_session()
            return None

    def clear_session(self) -> None:
        """Destroy the current session.

        Overwrites the session file with random data before deletion
        to prevent recovery of the encrypted master key.
        """
        if not self.session_file.exists():
            return

        # Overwrite before deletion
        try:
            file_size = self.session_file.stat().st_size
            self.session_file.write_bytes(os.urandom(max(file_size, 64)))
        except OSError:
            pass

        try:
            self.session_file.unlink()
        except OSError:
            pass

    def is_active(self) -> bool:
        """Check if a session file exists and is not expired.

        This check does NOT require the token — it only verifies that
        a non-expired session file exists on disk.

        Returns:
            True if a session file exists with a future expiry time.
        """
        if not self.session_file.exists():
            return False

        try:
            session_data = json.loads(
                self.session_file.read_text(encoding="utf-8")
            )
            expires_at = datetime.fromisoformat(session_data["expires_at"])
            return datetime.now(timezone.utc) <= expires_at
        except (json.JSONDecodeError, KeyError, ValueError, OSError):
            return False

    @staticmethod
    def _hash_token(token: str) -> str:
        """Compute SHA-256 hash of a token.

        Args:
            token: The raw token string.

        Returns:
            Hex-encoded SHA-256 hash.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _derive_session_key(token: str) -> bytes:
        """Derive a Fernet-compatible encryption key from a session token.

        Uses HKDF-SHA256 to derive a 32-byte key from the token, then
        base64url-encodes it for Fernet compatibility.

        Args:
            token: The raw session token.

        Returns:
            URL-safe base64-encoded 32-byte key for Fernet.
        """
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"vault-session-salt",
            info=b"vault-session-key",
        )
        derived = hkdf.derive(token.encode("utf-8"))
        return base64.urlsafe_b64encode(derived)
