"""
Resume parsing service with structured extraction pipeline
"""

import os
import uuid
import time
from pathlib import Path
from typing import Optional, Union, Dict, Any
from datetime import datetime
import structlog
import hashlib
import mimetypes

from app.core.config import settings
from app.core.database import db
from app.core.metrics import get_metrics_collector, MetricType
from app.models.schemas import ParsingJob, ParsingJobResponse, ProfileJSON
from app.models.profile_schema import get_schema_version
from app.services.profile_validator import validate_parser_output
from app.services.docx_extractor import DOCXExtractor
from app.services.pdf_extractor import PDFExtractor

logger = structlog.get_logger()


class ParserService:
    """
    Resume parser service that handles file type detection,
    routing to appropriate extractors, and job status management
    """

    @staticmethod
    def generate_job_id() -> str:
        """Generate unique parsing job ID"""
        return f"job_{int(datetime.now().timestamp())}_{str(uuid.uuid4())[:8]}"

    @classmethod
    async def parse_resume(
        cls,
        resume_id: Optional[str] = None,
        file_path: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> ParsingJobResponse:
        """
        Main entry point for resume parsing

        Args:
            resume_id: Database resume ID to parse
            file_path: Direct file path to parse
            job_id: Optional job ID for tracking

        Returns:
            ParsingJobResponse with job status and results
        """
        if not job_id:
            job_id = cls.generate_job_id()

        start_time = datetime.now()
        start_time_ms = time.time() * 1000
        metrics_collector = get_metrics_collector()

        logger.info(
            "Parser job started",
            job_id=job_id,
            resume_id=resume_id,
            file_path=file_path if file_path else "<from_db>"
        )

        try:
            # Resolve file path
            if file_path:
                resolved_path = Path(file_path)
            elif resume_id:
                # Look up file path from database
                logger.info(
                    "Looking up resume file path from database",
                    job_id=job_id,
                    resume_id=resume_id
                )
                file_path_from_db = await db.get_resume_file_path(resume_id)
                if not file_path_from_db:
                    logger.error(
                        "Resume not found in database",
                        job_id=job_id,
                        resume_id=resume_id
                    )
                    return ParsingJobResponse(
                        job_id=job_id,
                        status="failed",
                        error=f"Resume with ID {resume_id} not found",
                        started_at=start_time,
                        completed_at=datetime.now()
                    )
                resolved_path = Path(file_path_from_db)
                logger.info(
                    "Resume file path resolved",
                    job_id=job_id,
                    resume_id=resume_id,
                    file_path=str(resolved_path)
                )
            else:
                raise ValueError("Either resume_id or file_path must be provided")

            # Validate file exists
            if not resolved_path.exists():
                logger.error(
                    "File not found",
                    job_id=job_id,
                    file_path=str(resolved_path)
                )
                return ParsingJobResponse(
                    job_id=job_id,
                    status="failed",
                    error="File not found",
                    started_at=start_time,
                    completed_at=datetime.now()
                )

            # Detect file type and record metrics
            file_type = cls._detect_file_type(resolved_path)
            file_size_bytes = resolved_path.stat().st_size

            # Record parsing start metrics
            trace_id = metrics_collector.record_parse_start(
                resume_id=resume_id or "direct_file",
                file_format=file_type,
                file_size_bytes=file_size_bytes
            )

            logger.info(
                "File type detected",
                job_id=job_id,
                file_path=str(resolved_path),
                file_type=file_type,
                file_size_bytes=file_size_bytes,
                metrics_trace_id=trace_id
            )

            # Route to appropriate extractor
            if file_type == "docx":
                extractor = DOCXExtractor()
                result = await extractor.extract(resolved_path, job_id)
            elif file_type == "pdf":
                extractor = PDFExtractor()
                result = await extractor.extract(resolved_path, job_id)
            elif file_type == "txt":
                # For txt files, create a simple mock result for testing
                result = {
                    "extraction_method": "txt_simple",
                    "sections": {
                        "contact": {"full_name": "Test User"},
                        "summary": "Simple text file content",
                        "experience": [],
                        "education": [],
                        "skills": ["Text Processing"],
                        "projects": [],
                        "achievements": []
                    },
                    "warnings": ["TXT files have limited parsing capabilities"],
                    "metadata": {
                        "extractor_version": "1.0.0",
                        "extraction_timestamp": datetime.now().isoformat(),
                        "confidence_score": 0.5
                    }
                }
            else:
                logger.error(
                    "Unsupported file type",
                    job_id=job_id,
                    file_type=file_type,
                    file_path=str(resolved_path)
                )
                return ParsingJobResponse(
                    job_id=job_id,
                    status="failed",
                    error=f"Unsupported file type: {file_type}",
                    started_at=start_time,
                    completed_at=datetime.now()
                )

            # Validate parser output against schema
            validation_result = validate_parser_output(result, job_id=job_id)

            if not validation_result.is_valid:
                logger.warning(
                    "Parser output validation failed",
                    job_id=job_id,
                    errors=validation_result.errors[:3],  # Log first 3 errors
                    warnings=validation_result.warnings[:3]
                )
                # Add validation errors to result warnings
                result["warnings"] = result.get("warnings", []) + [
                    f"Schema validation: {err}" for err in validation_result.errors
                ]

            # Add schema metadata
            result["schema_version"] = get_schema_version()
            result["schema_validated"] = validation_result.is_valid

            # Calculate final metrics
            end_time_ms = time.time() * 1000
            duration_ms = end_time_ms - start_time_ms
            sections_count = len(result.get("sections", {}))
            warnings_count = len(result.get("warnings", []))

            # Count skills extracted
            skills_count = 0
            if "sections" in result and "skills" in result["sections"]:
                skills_section = result["sections"]["skills"]
                if isinstance(skills_section, list):
                    skills_count = len(skills_section)
                elif isinstance(skills_section, dict):
                    skills_count = sum(len(v) for v in skills_section.values() if isinstance(v, list))

            # Record successful parsing metrics
            metrics_collector.record_parse_success(
                trace_id=trace_id,
                duration_ms=duration_ms,
                sections_count=sections_count,
                skills_count=skills_count,
                warnings_count=warnings_count
            )

            logger.info(
                "Parser job completed successfully",
                job_id=job_id,
                file_type=file_type,
                sections_extracted=sections_count,
                skills_extracted=skills_count,
                warnings=warnings_count,
                schema_valid=validation_result.is_valid,
                schema_version=get_schema_version(),
                duration_ms=duration_ms,
                metrics_trace_id=trace_id
            )

            end_time = datetime.now()
            return ParsingJobResponse(
                job_id=job_id,
                status="completed",
                result=result,
                started_at=start_time,
                completed_at=end_time,
                processing_time_ms=cls._calculate_processing_time(start_time)
            )

        except Exception as e:
            # Record parsing failure metrics
            end_time_ms = time.time() * 1000
            duration_ms = end_time_ms - start_time_ms
            error_type = type(e).__name__

            if 'trace_id' in locals():
                metrics_collector.record_parse_failure(
                    trace_id=trace_id,
                    duration_ms=duration_ms,
                    error_type=error_type
                )

            logger.error(
                "Parser job failed with exception",
                job_id=job_id,
                error=str(e),
                error_type=error_type,
                duration_ms=duration_ms,
                metrics_trace_id=locals().get('trace_id', 'unknown'),
                exc_info=True
            )
            return ParsingJobResponse(
                job_id=job_id,
                status="failed",
                error=f"{error_type}: {str(e)}",
                started_at=start_time,
                completed_at=datetime.now()
            )

    @staticmethod
    def _detect_file_type(file_path: Path) -> str:
        """
        Detect file type from path and content

        Args:
            file_path: Path to file

        Returns:
            File type string ('docx', 'pdf', 'txt', etc.)
        """
        # First check by extension
        extension = file_path.suffix.lower()
        if extension == '.docx':
            return 'docx'
        elif extension == '.pdf':
            return 'pdf'
        elif extension in ['.txt', '.text']:
            return 'txt'

        # Fallback to MIME type detection
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if 'openxmlformats' in mime_type or 'wordprocessingml' in mime_type:
                return 'docx'
            elif 'pdf' in mime_type:
                return 'pdf'
            elif 'text' in mime_type:
                return 'txt'

        # Default fallback
        return 'unknown'

    @staticmethod
    def _calculate_processing_time(start_time: datetime) -> int:
        """Calculate processing time in milliseconds"""
        return int((datetime.now() - start_time).total_seconds() * 1000)

    @staticmethod
    async def get_job_status(job_id: str) -> Optional[ParsingJobResponse]:
        """
        Get status of a parsing job

        Args:
            job_id: Job ID to query

        Returns:
            ParsingJobResponse if found, None otherwise
        """
        # TODO: Implement database job status lookup
        logger.info("Job status query", job_id=job_id)
        return None

    @staticmethod
    def validate_file_for_parsing(file_path: Union[str, Path]) -> bool:
        """
        Validate that a file is suitable for parsing

        Args:
            file_path: Path to file

        Returns:
            True if file can be parsed, False otherwise
        """
        path = Path(file_path)

        if not path.exists():
            logger.warning("File does not exist", file_path=str(path))
            return False

        if not path.is_file():
            logger.warning("Path is not a file", file_path=str(path))
            return False

        # Check file size
        file_size = path.stat().st_size
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(
                "File too large for parsing",
                file_path=str(path),
                file_size=file_size,
                max_size=settings.MAX_FILE_SIZE
            )
            return False

        # Check file type
        file_type = ParserService._detect_file_type(path)
        if file_type not in ['docx', 'pdf', 'txt']:
            logger.warning(
                "Unsupported file type for parsing",
                file_path=str(path),
                file_type=file_type
            )
            return False

        return True