"""
Encrypted blob storage for the Vault.

Stores conversation content as Fernet-encrypted files organized in a
sharded directory structure (first 2 hex chars of blob ID). All content
is encrypted before touching disk — plaintext never exists on the filesystem.

Security principles:
- Encrypt before any disk write
- Atomic writes (write to .tmp, then rename)
- Secure deletion (overwrite before unlink)
- Validate blob ID format
"""
from __future__ import annotations

import os
import platform
import uuid
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from vault.security.crypto import KeyManager


class BlobStore:
    """Manages encrypted blob storage on the local filesystem.

    Blobs are stored in a sharded directory structure to avoid too many
    files in a single directory:
        root/
          ab/
            abc12345-...-6789.enc
          cd/
            cdef0123-...-4567.enc

    All content is encrypted with per-conversation Fernet keys derived
    from the master key via KeyManager.

    Attributes:
        root: Root directory for blob storage.
        key_manager: KeyManager instance for key derivation.
    """

    def __init__(self, root_path: Path, key_manager: KeyManager) -> None:
        """Initialize the BlobStore.

        Args:
            root_path: Root directory for encrypted blob files.
            key_manager: KeyManager for deriving conversation encryption keys.
        """
        self.root = root_path
        self.key_manager = key_manager
        self.root.mkdir(parents=True, exist_ok=True)

    def store(
        self,
        content: bytes,
        master_key: bytes,
        conversation_id: str,
        blob_id: str | None = None,
    ) -> str:
        """Encrypt content and store as a blob file.

        Args:
            content: Plaintext content to encrypt and store.
            master_key: The 32-byte master key.
            conversation_id: Conversation this blob belongs to (used for key derivation).
            blob_id: Optional blob ID. If None, a UUID4 is generated.

        Returns:
            The blob ID (UUID string) that can be used to retrieve the blob.

        Raises:
            ValueError: If content is empty or blob_id format is invalid.
            OSError: If the file cannot be written.
        """
        if not content:
            raise ValueError("Content must not be empty")

        if blob_id is None:
            blob_id = str(uuid.uuid4())
        else:
            self._validate_blob_id(blob_id)

        fernet = self.key_manager.get_fernet(master_key, conversation_id)
        encrypted = fernet.encrypt(content)

        blob_path = self._blob_path(blob_id)
        blob_path.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp file, then rename
        tmp_path = blob_path.with_suffix(".tmp")
        try:
            tmp_path.write_bytes(encrypted)
            os.replace(str(tmp_path), str(blob_path))
        except Exception:
            # Clean up temp file on failure
            if tmp_path.exists():
                tmp_path.unlink()
            raise

        # Set file permissions (Unix only)
        if platform.system() != "Windows":
            os.chmod(str(blob_path), 0o600)

        return blob_id

    def retrieve(
        self, blob_id: str, master_key: bytes, conversation_id: str
    ) -> bytes:
        """Decrypt and return blob content.

        Args:
            blob_id: The blob ID returned by store().
            master_key: The 32-byte master key.
            conversation_id: Conversation this blob belongs to.

        Returns:
            Decrypted plaintext content.

        Raises:
            FileNotFoundError: If the blob file does not exist.
            ValueError: If decryption fails (wrong key or corrupted data).
        """
        self._validate_blob_id(blob_id)
        blob_path = self._blob_path(blob_id)

        if not blob_path.exists():
            raise FileNotFoundError(
                f"Blob not found: {blob_id} "
                f"(expected at {blob_path})"
            )

        encrypted = blob_path.read_bytes()
        fernet = self.key_manager.get_fernet(master_key, conversation_id)

        try:
            return fernet.decrypt(encrypted)
        except InvalidToken as e:
            raise ValueError(
                f"Decryption failed for blob {blob_id}. "
                "This may indicate a wrong passphrase or corrupted data."
            ) from e

    def delete(self, blob_id: str) -> bool:
        """Securely delete a blob file.

        Overwrites the file with random data before unlinking to prevent
        recovery of encrypted content from disk.

        Args:
            blob_id: The blob ID to delete.

        Returns:
            True if the blob was found and deleted, False if not found.
        """
        self._validate_blob_id(blob_id)
        blob_path = self._blob_path(blob_id)

        if not blob_path.exists():
            return False

        # Overwrite with random data before deletion
        file_size = blob_path.stat().st_size
        blob_path.write_bytes(os.urandom(file_size))
        blob_path.unlink()

        # Remove empty parent directory
        parent = blob_path.parent
        try:
            if parent != self.root and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass  # Directory not empty or permission issue — not critical

        return True

    def exists(self, blob_id: str) -> bool:
        """Check if a blob exists.

        Args:
            blob_id: The blob ID to check.

        Returns:
            True if the blob file exists on disk.
        """
        self._validate_blob_id(blob_id)
        return self._blob_path(blob_id).exists()

    def get_total_size(self) -> int:
        """Calculate total size of all encrypted blob files.

        Returns:
            Total size in bytes of all .enc files under the blob root.
        """
        total = 0
        for enc_file in self.root.rglob("*.enc"):
            total += enc_file.stat().st_size
        return total

    def _blob_path(self, blob_id: str) -> Path:
        """Compute the filesystem path for a blob.

        Blobs are sharded into subdirectories by the first 2 characters
        of their ID to avoid filesystem performance issues.

        Args:
            blob_id: The blob UUID string.

        Returns:
            Path to the .enc file for this blob.
        """
        return self.root / blob_id[:2] / f"{blob_id}.enc"

    @staticmethod
    def _validate_blob_id(blob_id: str) -> None:
        """Validate that a blob ID is a valid UUID4 string.

        Args:
            blob_id: The blob ID to validate.

        Raises:
            ValueError: If the blob ID is not a valid UUID format.
        """
        try:
            uuid.UUID(blob_id, version=4)
        except ValueError as e:
            raise ValueError(
                f"Invalid blob ID format: {blob_id!r}. "
                "Expected a UUID4 string."
            ) from e
