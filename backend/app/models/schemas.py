"""
Pydantic schemas for API request/response models
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class UploadResponse(BaseModel):
    """Response model for file upload"""

    resume_id: str = Field(..., description="Unique resume identifier")
    run_id: str = Field(..., description="Upload run identifier for tracing")
    file_hash: str = Field(..., description="SHA-256 checksum of uploaded file")
    stored_path: str = Field(..., description="Redacted storage path")
    file_name: str = Field(..., description="Original filename")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="MIME type of uploaded file")
    upload_timestamp: datetime = Field(..., description="Upload completion time")
    status: str = Field(default="uploaded", description="Upload status")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ErrorResponse(BaseModel):
    """Standard error response model"""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Human-readable error message")
    request_id: str = Field(..., description="Request ID for tracking")
    details: Optional[dict] = Field(None, description="Additional error details")


class FileValidationError(BaseModel):
    """File validation error details"""

    field: str = Field(..., description="Field that failed validation")
    message: str = Field(..., description="Validation error message")
    received_value: Optional[str] = Field(None, description="Value that was received")
    expected: Optional[str] = Field(None, description="Expected value or format")


# Parsing-related schemas

class ParsingJob(BaseModel):
    """Request model for parsing job"""

    resume_id: Optional[str] = Field(None, description="Resume ID from database")
    file_path: Optional[str] = Field(None, description="Direct file path to parse")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")
    force_reparse: bool = Field(False, description="Force re-parsing even if already processed")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class ParsingJobResponse(BaseModel):
    """Response model for parsing job"""

    job_id: str = Field(..., description="Unique job identifier")
    status: str = Field(..., description="Job status: pending, processing, completed, failed")
    result: Optional[Dict[str, Any]] = Field(None, description="Parsed profile data (ProfileJSON)")
    error: Optional[str] = Field(None, description="Error message if failed")
    started_at: datetime = Field(..., description="Job start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Job completion timestamp")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    warnings: Optional[List[str]] = Field(None, description="Non-fatal warnings during processing")

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# Import the comprehensive ProfileJSON schema
from app.models.profile_schema import ProfileJSONSchema

# Backward compatibility alias
ProfileJSON = ProfileJSONSchema