"""
Cryptographic key management for the Vault.

Provides master key derivation from passphrases using Argon2id,
per-conversation key derivation using HKDF, and Fernet encryption helpers.

Security principles:
- Fail closed: any error in derivation raises, never returns partial keys
- No logging of keys, passphrases, or decrypted content
- All randomness via the secrets module
- Salt persisted to disk; keys exist only in memory
"""
from __future__ import annotations

import base64
import hashlib
import secrets
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


# Argon2 is imported conditionally to provide a clear error if missing
try:
    import argon2.low_level
except ImportError as e:
    raise ImportError(
        "argon2-cffi is required for key derivation. "
        "Install it with: pip install argon2-cffi"
    ) from e


# Argon2id parameters — tuned for <2s on modern hardware
_ARGON2_TIME_COST = 4
_ARGON2_MEMORY_COST = 65536  # 64 MB
_ARGON2_PARALLELISM = 4
_ARGON2_HASH_LEN = 32  # 256-bit key
_ARGON2_SALT_LEN = 16  # 128-bit salt

_MIN_PASSPHRASE_LENGTH = 12


class KeyManager:
    """Manages cryptographic key derivation and caching for the Vault.

    Derives a master key from a user passphrase using Argon2id, then derives
    per-conversation keys using HKDF-SHA256. Conversation keys are formatted
    for use with Fernet symmetric encryption.

    Attributes:
        vault_root: Root directory of the vault (contains .salt file).
    """

    def __init__(self, vault_root: Path) -> None:
        """Initialize the KeyManager.

        Args:
            vault_root: Path to the vault root directory. The .salt file
                will be stored here.
        """
        self.vault_root = vault_root
        self.salt_file = vault_root / ".salt"
        self._master_key: Optional[bytes] = None

    def derive_master_key(self, passphrase: str) -> bytes:
        """Derive a 256-bit master key from a passphrase using Argon2id.

        On first call, generates and persists a random salt. Subsequent calls
        use the existing salt to produce the same key for the same passphrase.

        Args:
            passphrase: User-provided passphrase (must be >= 12 characters).

        Returns:
            32-byte master key.

        Raises:
            ValueError: If passphrase is too short.
            OSError: If salt file cannot be read or written.
        """
        valid, message = self.validate_passphrase(passphrase)
        if not valid:
            raise ValueError(message)

        salt = self._load_or_create_salt()

        master_key = argon2.low_level.hash_secret_raw(
            secret=passphrase.encode("utf-8"),
            salt=salt,
            time_cost=_ARGON2_TIME_COST,
            memory_cost=_ARGON2_MEMORY_COST,
            parallelism=_ARGON2_PARALLELISM,
            hash_len=_ARGON2_HASH_LEN,
            type=argon2.low_level.Type.ID,
        )

        return master_key

    def derive_conversation_key(
        self, master_key: bytes, conversation_id: str
    ) -> bytes:
        """Derive a Fernet-compatible key for a specific conversation.

        Uses HKDF-SHA256 to derive a per-conversation key from the master key.
        The returned key is base64url-encoded and ready for use with Fernet.

        Args:
            master_key: The 32-byte master key from derive_master_key().
            conversation_id: Unique identifier for the conversation.

        Returns:
            URL-safe base64-encoded 32-byte key suitable for Fernet.

        Raises:
            ValueError: If master_key is not 32 bytes or conversation_id is empty.
        """
        if len(master_key) != _ARGON2_HASH_LEN:
            raise ValueError(
                f"Master key must be {_ARGON2_HASH_LEN} bytes, "
                f"got {len(master_key)}"
            )
        if not conversation_id:
            raise ValueError("conversation_id must not be empty")

        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=conversation_id.encode("utf-8"),
            info=b"vault-conversation-content",
        )
        derived = hkdf.derive(master_key)

        # Fernet requires a 32-byte key encoded as url-safe base64
        return base64.urlsafe_b64encode(derived)

    def get_fernet(self, master_key: bytes, conversation_id: str) -> Fernet:
        """Get a Fernet instance keyed for a specific conversation.

        Convenience method that derives the conversation key and returns
        a ready-to-use Fernet object.

        Args:
            master_key: The 32-byte master key.
            conversation_id: Unique identifier for the conversation.

        Returns:
            Fernet instance for encrypting/decrypting conversation content.
        """
        conv_key = self.derive_conversation_key(master_key, conversation_id)
        return Fernet(conv_key)

    def cache_master_key(self, key: bytes) -> None:
        """Cache the master key in memory for the current session.

        Args:
            key: The 32-byte master key to cache.

        Raises:
            ValueError: If key is not 32 bytes.
        """
        if len(key) != _ARGON2_HASH_LEN:
            raise ValueError(
                f"Master key must be {_ARGON2_HASH_LEN} bytes, "
                f"got {len(key)}"
            )
        self._master_key = key

    def get_cached_key(self) -> Optional[bytes]:
        """Retrieve the cached master key.

        Returns:
            The cached 32-byte master key, or None if not cached.
        """
        return self._master_key

    def clear_cached_key(self) -> None:
        """Clear the cached master key from memory."""
        self._master_key = None

    def validate_passphrase(self, passphrase: str) -> tuple[bool, str]:
        """Validate passphrase strength.

        Args:
            passphrase: The passphrase to validate.

        Returns:
            Tuple of (is_valid, message). If invalid, message describes why.
        """
        if len(passphrase) < _MIN_PASSPHRASE_LENGTH:
            return (
                False,
                f"Passphrase must be at least {_MIN_PASSPHRASE_LENGTH} "
                f"characters (got {len(passphrase)})",
            )
        return (True, "Passphrase meets minimum requirements")

    def verify_passphrase(self, passphrase: str) -> bool:
        """Verify a passphrase against the stored salt by attempting derivation.

        This is used to check if a passphrase is correct by deriving a key
        and verifying it can decrypt a known marker. For v1, we simply check
        that derivation succeeds without error.

        Args:
            passphrase: The passphrase to verify.

        Returns:
            True if derivation succeeds, False otherwise.
        """
        try:
            self.derive_master_key(passphrase)
            return True
        except (ValueError, OSError):
            return False

    def _load_or_create_salt(self) -> bytes:
        """Load existing salt from disk, or generate and save a new one.

        Returns:
            16-byte salt.

        Raises:
            OSError: If the salt file cannot be read or written.
        """
        if self.salt_file.exists():
            salt = self.salt_file.read_bytes()
            if len(salt) != _ARGON2_SALT_LEN:
                raise ValueError(
                    f"Corrupt salt file: expected {_ARGON2_SALT_LEN} bytes, "
                    f"got {len(salt)}"
                )
            return salt

        salt = secrets.token_bytes(_ARGON2_SALT_LEN)
        self.salt_file.parent.mkdir(parents=True, exist_ok=True)
        self.salt_file.write_bytes(salt)
        return salt

    def get_master_key_hash(self, master_key: bytes) -> str:
        """Get a SHA-256 hash of the master key for identity comparison.

        This is used to verify that two keys are the same without exposing
        the key material. Never log or display the actual key.

        Args:
            master_key: The 32-byte master key.

        Returns:
            Hex-encoded SHA-256 hash of the key.
        """
        return hashlib.sha256(master_key).hexdigest()
