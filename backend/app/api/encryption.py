"""
SCOUT Encryption API Endpoints

Provides health checks and status information for the encryption service.
"""

from fastapi import APIRouter
from typing import Dict, Any
import structlog

from app.services.encryption_service import EncryptionService

logger = structlog.get_logger()
router = APIRouter(prefix="/api/encryption", tags=["encryption"])

@router.get("/health")
async def encryption_health() -> Dict[str, Any]:
    """
    Check encryption service health status
    """
    try:
        # Initialize encryption service to test functionality
        encryption_service = EncryptionService()

        # Test basic encryption/decryption
        test_data = b"health check test"
        encrypted = encryption_service.fernet.encrypt(test_data)
        decrypted = encryption_service.fernet.decrypt(encrypted)

        if decrypted == test_data:
            logger.info("Encryption health check passed")
            return {
                "status": "healthy",
                "message": "Encryption service operational",
                "encryption_available": True,
                "key_derivation": "PBKDF2-HMAC-SHA256",
                "algorithm": "Fernet (AES 128 CBC + HMAC SHA256)"
            }
        else:
            logger.error("Encryption health check failed - data corruption")
            return {
                "status": "unhealthy",
                "message": "Encryption test failed - data corruption detected",
                "encryption_available": False
            }

    except Exception as e:
        logger.error(
            "Encryption health check failed",
            error=str(e),
            error_type=type(e).__name__
        )
        return {
            "status": "unhealthy",
            "message": f"Encryption service error: {type(e).__name__}",
            "encryption_available": False,
            "error": str(e)
        }