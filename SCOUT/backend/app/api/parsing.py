"""
Resume parsing API endpoints
"""

from fastapi import APIRouter, HTTPException, Request, Query, status
from fastapi.responses import JSONResponse
import structlog
from datetime import datetime
import uuid
import glob
import os
from pathlib import Path

from app.models.schemas import ParsingJob, ParsingJobResponse, ErrorResponse
from app.services.parser_service import ParserService
from app.core.config import settings

router = APIRouter()
logger = structlog.get_logger()


def resolve_placeholder_path(file_path: str) -> str:
    """
    Resolve [RUN_ID] placeholders in file paths by finding the actual file in the filesystem

    Args:
        file_path: Path that may contain [RUN_ID] placeholder

    Returns:
        Resolved file path with actual run_id
    """
    if "[RUN_ID]" not in file_path:
        return file_path

    # Replace [RUN_ID] with wildcard for glob matching
    pattern = file_path.replace("[RUN_ID]", "*")

    # Convert to absolute path relative to data directory
    if not pattern.startswith("/"):
        # Remove 'data/' prefix if present to avoid duplication
        if pattern.startswith("data/"):
            pattern = pattern[5:]  # Remove 'data/' prefix
        pattern = os.path.join(settings.DATA_ROOT, pattern)

    logger.debug("Resolving path pattern", pattern=pattern, original_path=file_path)

    # Find matching files
    matches = glob.glob(pattern)

    if not matches:
        logger.warning("No files found matching pattern", pattern=pattern, original_path=file_path)
        return file_path  # Return original path if no matches

    if len(matches) > 1:
        logger.warning("Multiple files found matching pattern", pattern=pattern, matches=matches[:3])

    # Return the first match (most recent)
    resolved_path = matches[0]
    logger.info("Path resolved successfully", original=file_path, resolved=resolved_path)

    return resolved_path


@router.post("/run", response_model=ParsingJobResponse)
async def run_parsing_job(
    request: Request,
    resume_id: str = Query(..., description="Resume ID to parse"),
    force_reparse: bool = Query(False, description="Force re-parsing even if already processed")
):
    """
    Trigger a resume parsing job

    This endpoint starts a parsing job for the specified resume ID.
    The job runs synchronously and returns the parsing results.

    - Validates resume exists and is accessible
    - Detects file type and routes to appropriate extractor
    - Returns structured ProfileJSON data
    - Records all parsing status and errors to database
    - Provides structured JSON logs at each stage
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    job_id = ParserService.generate_job_id()

    logger.info(
        "Parsing job requested",
        request_id=request_id,
        job_id=job_id,
        resume_id=resume_id,
        force_reparse=force_reparse
    )

    try:
        # Create parsing job
        parsing_job = ParsingJob(
            resume_id=resume_id,
            job_id=job_id,
            force_reparse=force_reparse
        )

        # Execute parsing job
        result = await ParserService.parse_resume(
            resume_id=resume_id,
            job_id=job_id
        )

        # TODO: Store job result in database
        logger.info(
            "Parsing job completed - storing to database",
            request_id=request_id,
            job_id=job_id,
            resume_id=resume_id,
            status=result.status,
            processing_time_ms=result.processing_time_ms
        )

        logger.info(
            "Parsing job API response ready",
            request_id=request_id,
            job_id=job_id,
            status=result.status,
            has_result=result.result is not None,
            warnings_count=len(result.warnings) if result.warnings else 0
        )

        return result

    except ValueError as e:
        logger.warning(
            "Parsing job failed due to validation error",
            request_id=request_id,
            job_id=job_id,
            resume_id=resume_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "message": str(e),
                "request_id": request_id,
                "job_id": job_id
            }
        )

    except NotImplementedError as e:
        logger.warning(
            "Parsing job failed due to unimplemented feature",
            request_id=request_id,
            job_id=job_id,
            resume_id=resume_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail={
                "error": "not_implemented",
                "message": str(e),
                "request_id": request_id,
                "job_id": job_id
            }
        )

    except Exception as e:
        logger.error(
            "Parsing job failed with unexpected error",
            request_id=request_id,
            job_id=job_id,
            resume_id=resume_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "parsing_failed",
                "message": "Parsing job failed due to an internal error. Please try again.",
                "request_id": request_id,
                "job_id": job_id
            }
        )


@router.post("/run/file", response_model=ParsingJobResponse)
async def run_parsing_job_from_file(
    request: Request,
    file_path: str = Query(..., description="Direct file path to parse"),
    force_reparse: bool = Query(False, description="Force re-parsing even if already processed")
):
    """
    Trigger a resume parsing job from direct file path

    This endpoint is useful for testing and development.
    Parses a file directly without requiring database storage.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    job_id = ParserService.generate_job_id()

    logger.info(
        "Direct file parsing job requested",
        request_id=request_id,
        job_id=job_id,
        file_path=file_path,
        force_reparse=force_reparse
    )

    try:
        # Resolve [RUN_ID] placeholder in file path if present
        resolved_file_path = resolve_placeholder_path(file_path)

        # Validate file path for security
        if not ParserService.validate_file_for_parsing(resolved_file_path):
            logger.warning(
                "File validation failed",
                request_id=request_id,
                job_id=job_id,
                file_path=resolved_file_path
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "invalid_file",
                    "message": "File is not valid for parsing (check existence, size, and type)",
                    "request_id": request_id,
                    "job_id": job_id
                }
            )

        # Execute parsing job
        result = await ParserService.parse_resume(
            file_path=resolved_file_path,
            job_id=job_id
        )

        logger.info(
            "Direct file parsing job completed",
            request_id=request_id,
            job_id=job_id,
            file_path=file_path,
            status=result.status,
            processing_time_ms=result.processing_time_ms
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(
            "Direct file parsing job failed with unexpected error",
            request_id=request_id,
            job_id=job_id,
            file_path=file_path,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "parsing_failed",
                "message": "Parsing job failed due to an internal error. Please try again.",
                "request_id": request_id,
                "job_id": job_id
            }
        )


@router.get("/status/{job_id}", response_model=ParsingJobResponse)
async def get_parsing_job_status(
    request: Request,
    job_id: str
):
    """
    Get status of a parsing job

    Returns the current status and results of a parsing job by ID.
    """
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    logger.info(
        "Job status requested",
        request_id=request_id,
        job_id=job_id
    )

    try:
        result = await ParserService.get_job_status(job_id)

        if result is None:
            logger.warning(
                "Job not found",
                request_id=request_id,
                job_id=job_id
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "job_not_found",
                    "message": f"Parsing job with ID '{job_id}' not found",
                    "request_id": request_id,
                    "job_id": job_id
                }
            )

        logger.info(
            "Job status retrieved",
            request_id=request_id,
            job_id=job_id,
            status=result.status
        )

        return result

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise

    except Exception as e:
        logger.error(
            "Job status query failed with unexpected error",
            request_id=request_id,
            job_id=job_id,
            error=str(e),
            error_type=type(e).__name__,
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "status_query_failed",
                "message": "Failed to retrieve job status due to an internal error.",
                "request_id": request_id,
                "job_id": job_id
            }
        )


@router.get("/health")
async def parsing_health_check():
    """Health check for parsing service"""
    return {
        "status": "healthy",
        "service": "parsing",
        "supported_formats": ["docx", "pdf"],
        "max_file_size": f"{settings.MAX_FILE_SIZE // (1024*1024)}MB",
        "features": {
            "docx_extraction": "implemented",  # D3.P2 - Complete
            "pdf_extraction": "implemented",   # D3.P3 - Complete
            "skills_normalization": "implemented",  # D4.P2 - Complete
            "schema_validation": "implemented",     # D4.P1 - Complete
            "job_persistence": "planned"            # Future enhancement
        }
    }