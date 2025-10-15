"""
Encryption service for artifact storage with streaming support
Provides encryption at rest for original files and ProfileJSON data
"""

import os
import hashlib
import secrets
from pathlib import Path
from typing import BinaryIO, Iterator, Optional, Tuple, Union
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import structlog
from datetime import datetime
import base64

from app.core.config import settings

logger = structlog.get_logger()

# Chunk size for streaming encryption (1MB)
CHUNK_SIZE = 1024 * 1024


class EncryptionError(Exception):
    """Custom exception for encryption-related errors"""
    pass


class EncryptionService:
    """
    Service for encrypting and decrypting artifacts at rest
    Uses Fernet symmetric encryption with streaming support
    """

    def __init__(self):
        self._key = None
        self._fernet = None
        self._initialize_encryption()

    def _initialize_encryption(self) -> None:
        """Initialize encryption with key from environment"""
        try:
            encryption_key = settings.ENCRYPTION_KEY

            if not encryption_key or encryption_key == "change_me_32_chars_long_key_here":
                logger.warning(
                    "Using default encryption key - INSECURE for production",
                    key_source="default"
                )
                # Generate a deterministic key for development
                encryption_key = "dev_key_scout_local_not_for_prod_use"

            # Derive a proper Fernet key from the provided key
            key_bytes = encryption_key.encode('utf-8')
            salt = b'scout_salt_deterministic_dev'  # Fixed salt for dev consistency

            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )

            derived_key = base64.urlsafe_b64encode(kdf.derive(key_bytes))
            self._fernet = Fernet(derived_key)

            logger.info(
                "Encryption service initialized",
                key_length=len(encryption_key),
                algorithm="Fernet_PBKDF2_SHA256"
            )

        except Exception as e:
            logger.error(
                "Failed to initialize encryption",
                error=str(e),
                error_type=type(e).__name__
            )
            raise EncryptionError(f"Encryption initialization failed: {e}")

    def encrypt_file(self, source_path: Union[str, Path], target_path: Union[str, Path]) -> dict:
        """
        Encrypt a file and write to target location with streaming

        Args:
            source_path: Path to source file
            target_path: Path where encrypted file will be written

        Returns:
            dict: Encryption metadata
        """
        source_path = Path(source_path)
        target_path = Path(target_path)

        if not source_path.exists():
            raise EncryptionError(f"Source file not found: {source_path}")

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = datetime.now()
        original_size = source_path.stat().st_size

        logger.info(
            "Starting file encryption",
            source_path=str(source_path),
            target_path=str(target_path),
            original_size=original_size
        )

        try:
            with open(source_path, 'rb') as source_file:
                with open(target_path, 'wb') as target_file:
                    encrypted_size = self._encrypt_stream(source_file, target_file)

            # Calculate processing time
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            metadata = {
                'encrypted_at': datetime.now().isoformat(),
                'original_size': original_size,
                'encrypted_size': encrypted_size,
                'processing_time_ms': processing_time_ms,
                'algorithm': 'Fernet',
                'source_hash': self._calculate_file_hash(source_path)
            }

            logger.info(
                "File encryption completed",
                source_path=str(source_path),
                target_path=str(target_path),
                original_size=original_size,
                encrypted_size=encrypted_size,
                processing_time_ms=processing_time_ms
            )

            return metadata

        except Exception as e:
            # Clean up failed encryption attempt
            if target_path.exists():
                target_path.unlink()

            logger.error(
                "File encryption failed",
                source_path=str(source_path),
                target_path=str(target_path),
                error=str(e),
                error_type=type(e).__name__
            )
            raise EncryptionError(f"Encryption failed: {e}")

    def decrypt_file(self, source_path: Union[str, Path], target_path: Union[str, Path]) -> dict:
        """
        Decrypt a file and write to target location with streaming

        Args:
            source_path: Path to encrypted file
            target_path: Path where decrypted file will be written

        Returns:
            dict: Decryption metadata
        """
        source_path = Path(source_path)
        target_path = Path(target_path)

        if not source_path.exists():
            raise EncryptionError(f"Encrypted file not found: {source_path}")

        # Ensure target directory exists
        target_path.parent.mkdir(parents=True, exist_ok=True)

        start_time = datetime.now()
        encrypted_size = source_path.stat().st_size

        logger.info(
            "Starting file decryption",
            source_path=str(source_path),
            target_path=str(target_path),
            encrypted_size=encrypted_size
        )

        try:
            with open(source_path, 'rb') as source_file:
                with open(target_path, 'wb') as target_file:
                    decrypted_size = self._decrypt_stream(source_file, target_file)

            # Calculate processing time
            processing_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            metadata = {
                'decrypted_at': datetime.now().isoformat(),
                'encrypted_size': encrypted_size,
                'decrypted_size': decrypted_size,
                'processing_time_ms': processing_time_ms,
                'algorithm': 'Fernet'
            }

            logger.info(
                "File decryption completed",
                source_path=str(source_path),
                target_path=str(target_path),
                encrypted_size=encrypted_size,
                decrypted_size=decrypted_size,
                processing_time_ms=processing_time_ms
            )

            return metadata

        except Exception as e:
            # Clean up failed decryption attempt
            if target_path.exists():
                target_path.unlink()

            logger.error(
                "File decryption failed",
                source_path=str(source_path),
                target_path=str(target_path),
                error="Decryption error",  # Don't leak encryption details
                error_type="DecryptionError"
            )
            raise EncryptionError("Decryption failed - file may be corrupted or key mismatch")

    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt raw bytes data

        Args:
            data: Raw bytes to encrypt

        Returns:
            bytes: Encrypted data
        """
        try:
            return self._fernet.encrypt(data)
        except Exception as e:
            logger.error(
                "Data encryption failed",
                data_length=len(data),
                error="Encryption error"  # Don't leak data details
            )
            raise EncryptionError("Data encryption failed")

    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt raw bytes data

        Args:
            encrypted_data: Encrypted bytes to decrypt

        Returns:
            bytes: Decrypted data
        """
        try:
            return self._fernet.decrypt(encrypted_data)
        except Exception as e:
            logger.error(
                "Data decryption failed",
                encrypted_data_length=len(encrypted_data),
                error="Decryption error"  # Don't leak encrypted data details
            )
            raise EncryptionError("Data decryption failed - invalid data or key mismatch")

    def _encrypt_stream(self, source: BinaryIO, target: BinaryIO) -> int:
        """
        Stream encrypt from source to target file

        Returns:
            int: Total bytes written to target
        """
        total_written = 0

        while True:
            chunk = source.read(CHUNK_SIZE)
            if not chunk:
                break

            encrypted_chunk = self._fernet.encrypt(chunk)
            target.write(encrypted_chunk)
            total_written += len(encrypted_chunk)

        return total_written

    def _decrypt_stream(self, source: BinaryIO, target: BinaryIO) -> int:
        """
        Stream decrypt from source to target file

        Returns:
            int: Total bytes written to target
        """
        total_written = 0
        buffer = b''

        # Read entire encrypted file (Fernet doesn't support streaming)
        # For large files, this could be optimized with chunked Fernet tokens
        encrypted_data = source.read()
        decrypted_data = self._fernet.decrypt(encrypted_data)

        target.write(decrypted_data)
        total_written = len(decrypted_data)

        return total_written

    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)

        return hash_sha256.hexdigest()

    def verify_key_health(self) -> dict:
        """
        Verify encryption key is working properly

        Returns:
            dict: Key health status
        """
        try:
            # Test encrypt/decrypt cycle
            test_data = b"SCOUT_encryption_test_" + secrets.token_bytes(32)
            encrypted = self.encrypt_data(test_data)
            decrypted = self.decrypt_data(encrypted)

            success = test_data == decrypted

            result = {
                'healthy': success,
                'test_timestamp': datetime.now().isoformat(),
                'algorithm': 'Fernet'
            }

            if success:
                logger.info("Encryption key health check passed")
            else:
                logger.error("Encryption key health check failed")

            return result

        except Exception as e:
            logger.error(
                "Encryption key health check error",
                error="Health check failed"  # Don't leak key details
            )
            return {
                'healthy': False,
                'test_timestamp': datetime.now().isoformat(),
                'error': 'Health check failed'
            }


# Global encryption service instance
encryption_service = EncryptionService()