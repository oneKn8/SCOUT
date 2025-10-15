"""
File processing and storage service
"""

import hashlib
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Tuple, Optional
import structlog

from app.core.config import settings
from app.services.encryption_service import encryption_service, EncryptionError

logger = structlog.get_logger()


class FileService:
    """Service for handling file operations"""

    @staticmethod
    def generate_run_id() -> str:
        """Generate a unique run ID for tracking uploads"""
        return str(uuid.uuid4())

    @staticmethod
    def calculate_checksum(file_content: bytes) -> str:
        """Calculate SHA-256 checksum of file content"""
        return hashlib.sha256(file_content).hexdigest()

    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """Validate file extension against allowed types"""
        if not filename:
            return False

        extension = "." + filename.lower().split(".")[-1]
        return extension in settings.allowed_extensions_list

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """Validate file size against maximum limit"""
        return 0 < file_size <= settings.MAX_FILE_SIZE

    @staticmethod
    def get_mime_type(filename: str) -> str:
        """Get MIME type based on file extension"""
        extension = filename.lower().split(".")[-1]
        mime_types = {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        }
        return mime_types.get(extension, "application/octet-stream")

    @staticmethod
    def create_storage_path(run_id: str, filename: str) -> Tuple[str, str]:
        """
        Create storage path following data/original/{year}/{month}/{run_id}/ structure

        Returns:
            Tuple of (full_path, redacted_path)
        """
        now = datetime.now()
        year = now.strftime("%Y")
        month = now.strftime("%m")

        # Create directory structure
        dir_path = os.path.join(settings.DATA_ROOT, "original", year, month, run_id)
        full_path = os.path.join(dir_path, filename)

        # Create path for API access (relative to app root)
        api_path = f"data/original/{year}/{month}/{run_id}/{filename}"

        return full_path, api_path

    @staticmethod
    async def store_file(
        file_content: bytes, filename: str, run_id: str
    ) -> Tuple[str, str, str]:
        """
        Store file to disk with encryption and return paths and checksum

        Returns:
            Tuple of (full_path, redacted_path, checksum)
        """
        try:
            # Calculate checksum of original content
            checksum = FileService.calculate_checksum(file_content)

            # Create storage paths
            full_path, redacted_path = FileService.create_storage_path(run_id, filename)
            temp_path = full_path + ".tmp"
            encrypted_path = full_path + ".enc"

            # Ensure directory exists
            Path(full_path).parent.mkdir(parents=True, exist_ok=True)

            # Write original file temporarily
            with open(temp_path, "wb") as f:
                f.write(file_content)

            # Encrypt the file
            try:
                encryption_metadata = encryption_service.encrypt_file(temp_path, encrypted_path)

                # Move encrypted file to final location
                Path(encrypted_path).rename(full_path)

                # Remove temporary file
                Path(temp_path).unlink()

                logger.info(
                    "File stored and encrypted successfully",
                    run_id=run_id,
                    filename=filename,
                    original_size=len(file_content),
                    encrypted_size=encryption_metadata.get('encrypted_size'),
                    encryption_time_ms=encryption_metadata.get('processing_time_ms')
                )

            except EncryptionError as e:
                # Fallback: store unencrypted if encryption fails
                logger.warning(
                    "Encryption failed, storing unencrypted file",
                    run_id=run_id,
                    filename=filename,
                    error="Encryption unavailable"
                )

                # Clean up
                if Path(encrypted_path).exists():
                    Path(encrypted_path).unlink()

                # Move temp to final (unencrypted)
                Path(temp_path).rename(full_path)

            logger.info(
                "File stored successfully",
                run_id=run_id,
                filename=filename,
                file_size=len(file_content),
                checksum=checksum,
                storage_path=redacted_path,
            )

            return full_path, redacted_path, checksum

        except Exception as e:
            logger.error(
                "File storage failed",
                run_id=run_id,
                filename=filename,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    @staticmethod
    def read_encrypted_file(file_path: str) -> bytes:
        """
        Read and decrypt a file from disk

        Args:
            file_path: Path to encrypted file

        Returns:
            bytes: Decrypted file content
        """
        try:
            file_path = Path(file_path)

            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")

            # Try to decrypt the file
            try:
                temp_decrypt_path = file_path.parent / f"{file_path.name}.decrypt_tmp"

                # Decrypt to temporary file
                decryption_metadata = encryption_service.decrypt_file(file_path, temp_decrypt_path)

                # Read decrypted content
                with open(temp_decrypt_path, 'rb') as f:
                    content = f.read()

                # Clean up temporary file
                temp_decrypt_path.unlink()

                logger.info(
                    "File decrypted and read successfully",
                    file_path=str(file_path),
                    decrypted_size=len(content),
                    decryption_time_ms=decryption_metadata.get('processing_time_ms')
                )

                return content

            except EncryptionError:
                # Fallback: try to read as unencrypted
                logger.info(
                    "File appears to be unencrypted, reading directly",
                    file_path=str(file_path)
                )

                with open(file_path, 'rb') as f:
                    return f.read()

        except Exception as e:
            logger.error(
                "Failed to read file",
                file_path=str(file_path),
                error="File read failed"  # Don't leak path details
            )
            raise

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.1f} {size_names[i]}"