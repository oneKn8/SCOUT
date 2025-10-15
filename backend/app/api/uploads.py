"""
File upload endpoints
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Request, status
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime
import uuid

from app.models.schemas import UploadResponse, ErrorResponse, FileValidationError
from app.services.file_service import FileService
from app.core.config import settings
from app.core.database import db

router = APIRouter()
logger = structlog.get_logger()


@router.post("/resume", response_model=UploadResponse)
async def upload_resume(
    request: Request,
    file: UploadFile = File(..., description="Resume file (PDF or DOCX, max 10MB)")
):
    """
    Upload a resume file for processing

    - Validates file type (PDF, DOCX only)
    - Validates file size (max 10MB)
    - Stores file with versioned directory structure
    - Returns upload metadata and trace information
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    run_id = FileService.generate_run_id()

    logger.info(
        "Resume upload started",
        request_id=request_id,
        run_id=run_id,
        filename=file.filename,
        content_type=file.content_type,
    )

    try:
        # Validate filename exists
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "validation_error",
                    "message": "Filename is required",
                    "request_id": request_id,
                }
            )

        # Validate file type
        if not FileService.validate_file_type(file.filename):
            logger.warning(
                "File type validation failed",
                request_id=request_id,
                run_id=run_id,
                filename=file.filename,
                allowed_types=settings.allowed_extensions_list,
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_file_type",
                    "message": f"File type not supported. Allowed types: {', '.join(settings.allowed_extensions_list)}",
                    "request_id": request_id,
                    "filename": file.filename,
                }
            )

        # Read file content
        file_content = await file.read()
        file_size = len(file_content)

        # Validate file size
        if not FileService.validate_file_size(file_size):
            logger.warning(
                "File size validation failed",
                request_id=request_id,
                run_id=run_id,
                filename=file.filename,
                file_size=file_size,
                max_size=settings.MAX_FILE_SIZE,
                human_readable_size=FileService.format_file_size(file_size),
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail={
                    "error": "file_too_large",
                    "message": f"File size ({FileService.format_file_size(file_size)}) exceeds maximum allowed size ({FileService.format_file_size(settings.MAX_FILE_SIZE)})",
                    "request_id": request_id,
                    "filename": file.filename,
                }
            )

        # Store file and get metadata
        full_path, api_path, checksum = await FileService.store_file(
            file_content, file.filename, run_id
        )

        # Get MIME type
        mime_type = FileService.get_mime_type(file.filename)

        # Generate IDs
        resume_id = str(uuid.uuid4())
        artifact_id = str(uuid.uuid4())

        # Store in database
        try:
            # Get or create default admin user
            admin_user = await db.fetch_one(
                "SELECT id FROM users WHERE email = 'admin@scout.local' LIMIT 1"
            )
            if not admin_user:
                # Create admin user if doesn't exist
                admin_user_id = str(uuid.uuid4())
                await db.execute(
                    "INSERT INTO users (id, email, settings) VALUES ($1, $2, $3)",
                    admin_user_id,
                    "admin@scout.local",
                    '{"role": "admin", "created_by": "upload_endpoint"}'
                )
                admin_user = {"id": admin_user_id}

            # Create resume record
            await db.execute(
                """
                INSERT INTO resumes (id, user_id, title, content, metadata)
                VALUES ($1, $2, $3, $4, $5)
                """,
                resume_id,
                admin_user["id"],
                file.filename or "Untitled Resume",
                '{}',
                '{"source": "upload", "run_id": "' + run_id + '"}'
            )

            # Create artifact record
            await db.execute(
                """
                INSERT INTO artifacts (id, user_id, resume_id, file_path, file_name,
                                     file_size, mime_type, checksum)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                """,
                artifact_id,
                admin_user["id"],
                resume_id,
                str(full_path),  # Store full path for parser to find
                file.filename,
                file_size,
                mime_type,
                checksum
            )

            logger.info(
                "Database records created",
                request_id=request_id,
                resume_id=resume_id,
                artifact_id=artifact_id
            )

        except Exception as db_error:
            logger.warning(
                "Failed to store in database, continuing with file-only upload",
                request_id=request_id,
                error=str(db_error)
            )

        # Create response
        response = UploadResponse(
            resume_id=resume_id,
            run_id=run_id,
            file_hash=checksum,
            stored_path=api_path,
            file_name=file.filename,
            file_size=file_size,
            mime_type=mime_type,
            upload_timestamp=datetime.now(),
            status="uploaded"
        )

        logger.info(
            "Resume upload completed successfully",
            request_id=request_id,
            run_id=run_id,
            resume_id=response.resume_id,
            filename=file.filename,
            file_size=file_size,
            checksum=checksum,
            mime_type=mime_type,
            storage_path=api_path,
        )

        return response

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(
            "Resume upload failed with unexpected error",
            request_id=request_id,
            run_id=run_id,
            filename=getattr(file, 'filename', 'unknown'),
            error=str(e),
            error_type=type(e).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "upload_failed",
                "message": "Upload failed due to an internal error. Please try again.",
                "request_id": request_id,
            }
        )


@router.get("/health")
async def upload_health_check():
    """Health check for upload service"""
    return {
        "status": "healthy",
        "service": "upload",
        "max_file_size": FileService.format_file_size(settings.MAX_FILE_SIZE),
        "allowed_types": settings.allowed_extensions_list,
    }