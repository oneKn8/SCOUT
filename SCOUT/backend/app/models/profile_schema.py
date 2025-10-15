"""
Comprehensive Profile JSON Schema for SCOUT Resume Parser
Defines the formal structure for parsed resume profiles with versioning and validation.
"""

from pydantic import BaseModel, Field, validator, model_validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime, date
from enum import Enum
import re

# Schema version for tracking compatibility
PROFILE_SCHEMA_VERSION = "1.0.0"


class ContactInfoSchema(BaseModel):
    """Contact information section"""

    full_name: Optional[str] = Field(None, description="Full name as extracted from resume", max_length=200)
    email: Optional[str] = Field(None, description="Primary email address", max_length=254)
    phone: Optional[str] = Field(None, description="Primary phone number", max_length=50)
    location: Optional[str] = Field(None, description="Current location (city, state/country)", max_length=200)
    website: Optional[str] = Field(None, description="Personal website or portfolio URL", max_length=500)
    linkedin: Optional[str] = Field(None, description="LinkedIn profile URL", max_length=500)
    github: Optional[str] = Field(None, description="GitHub profile URL", max_length=500)

    # Additional contact fields
    address: Optional[str] = Field(None, description="Full address if provided", max_length=500)
    social_profiles: Optional[Dict[str, str]] = Field(
        default_factory=dict,
        description="Other social media profiles (platform -> URL)"
    )

    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[^@]+@[^@]+\.[^@]+$', v):
            raise ValueError('Invalid email format')
        return v

    @validator('phone')
    def validate_phone(cls, v):
        if v:
            # Remove common phone formatting characters for validation
            cleaned = re.sub(r'[\s\-\(\)\+\.]', '', v)
            if not re.match(r'^\d{7,15}$', cleaned):
                raise ValueError('Invalid phone format')
        return v


class SummarySchema(BaseModel):
    """Professional summary or objective section"""

    text: Optional[str] = Field(None, description="Raw summary/objective text", max_length=2000)
    objective: Optional[str] = Field(None, description="Career objective if distinctly identified", max_length=1000)
    keywords: Optional[List[str]] = Field(
        default_factory=list,
        description="Key terms and skills mentioned in summary"
    )


class DateRangeSchema(BaseModel):
    """Flexible date range representation"""

    start_date: Optional[Union[date, str]] = Field(None, description="Start date (parsed or raw string)")
    end_date: Optional[Union[date, str]] = Field(None, description="End date (parsed or raw string)")
    is_current: bool = Field(False, description="Whether this position/education is current")
    raw_date_text: Optional[str] = Field(None, description="Original date text as extracted", max_length=200)

    @validator('start_date', 'end_date', pre=True)
    def parse_dates(cls, v):
        if isinstance(v, str) and v.strip():
            # Try to parse common date formats
            try:
                for fmt in ['%Y-%m-%d', '%Y-%m', '%Y', '%m/%Y', '%m/%d/%Y']:
                    try:
                        return datetime.strptime(v.strip(), fmt).date()
                    except ValueError:
                        continue
                # If parsing fails, keep as string
                return v.strip()
            except:
                return v
        return v


class ExperienceEntrySchema(BaseModel):
    """Single work experience entry"""

    company: Optional[str] = Field(None, description="Company/organization name", max_length=200)
    position: Optional[str] = Field(None, description="Job title/position", max_length=200)
    location: Optional[str] = Field(None, description="Work location", max_length=200)
    dates: Optional[DateRangeSchema] = Field(None, description="Employment date range")

    # Structured description content
    description: Optional[str] = Field(None, description="Raw job description text", max_length=5000)
    responsibilities: Optional[List[str]] = Field(
        default_factory=list,
        description="List of responsibilities and achievements"
    )
    technologies: Optional[List[str]] = Field(
        default_factory=list,
        description="Technologies and tools used"
    )

    # Metadata
    confidence_score: Optional[float] = Field(0.0, description="Extraction confidence (0.0-1.0)")
    warnings: Optional[List[str]] = Field(default_factory=list, description="Extraction warnings for this entry")


class EducationEntrySchema(BaseModel):
    """Single education entry"""

    institution: Optional[str] = Field(None, description="School/university name", max_length=200)
    degree: Optional[str] = Field(None, description="Degree type (Bachelor's, Master's, etc.)", max_length=200)
    field_of_study: Optional[str] = Field(None, description="Major/field of study", max_length=200)
    location: Optional[str] = Field(None, description="Institution location", max_length=200)
    dates: Optional[DateRangeSchema] = Field(None, description="Education date range")

    # Additional fields
    gpa: Optional[str] = Field(None, description="GPA if mentioned", max_length=20)
    honors: Optional[List[str]] = Field(default_factory=list, description="Academic honors and achievements")
    relevant_coursework: Optional[List[str]] = Field(
        default_factory=list,
        description="Relevant courses if listed"
    )

    # Metadata
    confidence_score: Optional[float] = Field(0.0, description="Extraction confidence (0.0-1.0)")
    warnings: Optional[List[str]] = Field(default_factory=list, description="Extraction warnings for this entry")


class SkillCategoryEnum(str, Enum):
    """Predefined skill categories for organization"""
    TECHNICAL = "technical"
    PROGRAMMING = "programming"
    FRAMEWORKS = "frameworks"
    DATABASES = "databases"
    CLOUD = "cloud"
    TOOLS = "tools"
    LANGUAGES = "languages"
    SOFT_SKILLS = "soft_skills"
    CERTIFICATIONS = "certifications"
    OTHER = "other"


class SkillEntrySchema(BaseModel):
    """Individual skill with metadata"""

    name: str = Field(..., description="Skill name as extracted", max_length=100)
    category: Optional[SkillCategoryEnum] = Field(None, description="Categorized skill type")
    proficiency_level: Optional[str] = Field(None, description="Proficiency level if mentioned", max_length=50)
    years_experience: Optional[int] = Field(None, description="Years of experience if mentioned")

    # Normalization fields (for D4.P2)
    canonical_name: Optional[str] = Field(None, description="Normalized/canonical skill name", max_length=100)
    aliases: Optional[List[str]] = Field(default_factory=list, description="Known aliases for this skill")

    # Context
    context: Optional[str] = Field(None, description="Context where skill was mentioned", max_length=500)
    confidence_score: Optional[float] = Field(1.0, description="Extraction confidence (0.0-1.0)")


class ProjectEntrySchema(BaseModel):
    """Project or portfolio entry"""

    name: str = Field(..., description="Project name", max_length=200)
    description: Optional[str] = Field(None, description="Project description", max_length=2000)
    url: Optional[str] = Field(None, description="Project URL (GitHub, demo, etc.)", max_length=500)
    dates: Optional[DateRangeSchema] = Field(None, description="Project timeline")

    technologies: Optional[List[str]] = Field(
        default_factory=list,
        description="Technologies used in project"
    )
    role: Optional[str] = Field(None, description="Role in project if specified", max_length=100)
    team_size: Optional[int] = Field(None, description="Team size if mentioned")

    # Metadata
    confidence_score: Optional[float] = Field(0.0, description="Extraction confidence (0.0-1.0)")


class AchievementEntrySchema(BaseModel):
    """Achievement, award, or certification entry"""

    title: str = Field(..., description="Achievement title", max_length=200)
    organization: Optional[str] = Field(None, description="Issuing organization", max_length=200)
    date_received: Optional[Union[date, str]] = Field(None, description="Date received")
    description: Optional[str] = Field(None, description="Achievement description", max_length=1000)

    # Type categorization
    type: Optional[str] = Field(None, description="Type: certification, award, publication, etc.", max_length=50)
    expiration_date: Optional[Union[date, str]] = Field(None, description="Expiration date for certifications")
    credential_id: Optional[str] = Field(None, description="Credential ID if applicable", max_length=100)
    verification_url: Optional[str] = Field(None, description="Verification URL", max_length=500)


class ExtractionMetadataSchema(BaseModel):
    """Metadata about the extraction process"""

    extractor_version: str = Field(..., description="Version of the extraction engine used")
    extraction_timestamp: datetime = Field(..., description="When the extraction was performed")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")
    confidence_score: float = Field(0.0, description="Overall extraction confidence (0.0-1.0)")

    # File information
    source_file_hash: Optional[str] = Field(None, description="SHA-256 hash of source file")
    file_size_bytes: Optional[int] = Field(None, description="Source file size in bytes")
    file_type: Optional[str] = Field(None, description="Detected file type")

    # Processing details
    sections_detected: Optional[List[str]] = Field(
        default_factory=list,
        description="Resume sections that were identified"
    )
    language_detected: Optional[str] = Field(None, description="Primary language detected", max_length=10)
    character_count: Optional[int] = Field(None, description="Total character count extracted")

    # Quality indicators
    structure_score: Optional[float] = Field(None, description="Document structure quality (0.0-1.0)")
    completeness_score: Optional[float] = Field(None, description="Information completeness (0.0-1.0)")


class ProfileJSONSchema(BaseModel):
    """
    Complete Profile JSON Schema for parsed resume data
    This is the authoritative structure for all resume parsing outputs.
    """

    # Schema metadata
    schema_version: str = Field(
        PROFILE_SCHEMA_VERSION,
        description="Profile schema version for compatibility tracking"
    )
    generated_at: datetime = Field(
        default_factory=datetime.now,
        description="Timestamp when this profile was generated"
    )

    # Source information
    extraction_method: str = Field(..., description="Extraction method used (docx_deterministic, pdf_heuristic, etc.)")
    source_file: str = Field(..., description="Original filename (no path for privacy)")

    # Core resume sections
    contact: Optional[ContactInfoSchema] = Field(None, description="Contact information section")
    summary: Optional[SummarySchema] = Field(None, description="Professional summary section")
    experience: List[ExperienceEntrySchema] = Field(
        default_factory=list,
        description="Work experience entries"
    )
    education: List[EducationEntrySchema] = Field(
        default_factory=list,
        description="Education entries"
    )
    skills: List[SkillEntrySchema] = Field(
        default_factory=list,
        description="Skills and competencies"
    )
    projects: List[ProjectEntrySchema] = Field(
        default_factory=list,
        description="Projects and portfolio items"
    )
    achievements: List[AchievementEntrySchema] = Field(
        default_factory=list,
        description="Achievements, certifications, and awards"
    )

    # Additional sections (flexible)
    additional_sections: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Other sections not covered by standard schema"
    )

    # Extraction metadata and quality
    metadata: ExtractionMetadataSchema = Field(..., description="Extraction process metadata")
    warnings: List[str] = Field(default_factory=list, description="Processing warnings")
    errors: List[str] = Field(default_factory=list, description="Non-fatal processing errors")

    # Privacy compliance
    @model_validator(mode='after')
    def privacy_compliance_check(self):
        """Ensure no derived PII beyond resume content"""

        # Check that we don't have any computed demographic information
        prohibited_fields = ['age', 'gender', 'race', 'nationality', 'marital_status']

        def check_dict_for_prohibited(d: dict, path: str = ""):
            for key, value in d.items():
                full_path = f"{path}.{key}" if path else key
                if key.lower() in prohibited_fields:
                    raise ValueError(f"Prohibited derived PII field detected: {full_path}")
                if isinstance(value, dict):
                    check_dict_for_prohibited(value, full_path)

        # Check additional_sections for prohibited content
        additional_sections = self.additional_sections or {}
        if additional_sections:
            check_dict_for_prohibited(additional_sections, "additional_sections")

        return self

    # Schema validation
    @validator('schema_version')
    def validate_schema_version(cls, v):
        """Ensure schema version follows semver format"""
        if not re.match(r'^\d+\.\d+\.\d+$', v):
            raise ValueError('Schema version must follow semantic versioning (x.y.z)')
        return v

    @validator('contact')
    def validate_contact_privacy(cls, v):
        """Ensure contact info doesn't contain inferred data"""
        if v and hasattr(v, 'dict'):
            contact_dict = v.dict() if hasattr(v, 'dict') else v
            # Only allow data that would be directly on a resume
            allowed_contact_fields = {
                'full_name', 'email', 'phone', 'location', 'website',
                'linkedin', 'github', 'address', 'social_profiles'
            }
            for field in contact_dict.keys():
                if field not in allowed_contact_fields:
                    raise ValueError(f"Contact field '{field}' not allowed - may contain inferred PII")
        return v

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            date: lambda v: v.isoformat() if v else None
        }
        schema_extra = {
            "example": {
                "schema_version": "1.0.0",
                "generated_at": "2025-09-24T06:15:00.000Z",
                "extraction_method": "docx_deterministic",
                "source_file": "john_doe_resume.docx",
                "contact": {
                    "full_name": "John Doe",
                    "email": "john.doe@email.com",
                    "phone": "(555) 123-4567",
                    "location": "San Francisco, CA",
                    "linkedin": "https://linkedin.com/in/johndoe"
                },
                "summary": {
                    "text": "Experienced software engineer with 5+ years in full-stack development",
                    "keywords": ["software engineer", "full-stack", "development"]
                },
                "experience": [
                    {
                        "company": "Tech Corp",
                        "position": "Senior Software Engineer",
                        "dates": {
                            "start_date": "2022-01-01",
                            "end_date": "2024-12-01",
                            "is_current": False
                        },
                        "responsibilities": [
                            "Led development of microservices architecture",
                            "Mentored junior developers"
                        ],
                        "technologies": ["Python", "React", "PostgreSQL"]
                    }
                ],
                "skills": [
                    {
                        "name": "Python",
                        "category": "programming",
                        "proficiency_level": "Expert"
                    }
                ],
                "metadata": {
                    "extractor_version": "1.0.0",
                    "extraction_timestamp": "2025-09-24T06:15:00.000Z",
                    "confidence_score": 0.95
                }
            }
        }


# Schema versioning and compatibility utilities

def get_schema_version() -> str:
    """Get current profile schema version"""
    return PROFILE_SCHEMA_VERSION


def is_schema_compatible(profile_version: str, current_version: str = PROFILE_SCHEMA_VERSION) -> bool:
    """
    Check if profile schema version is compatible with current version
    Uses semantic versioning compatibility rules
    """
    try:
        profile_parts = [int(x) for x in profile_version.split('.')]
        current_parts = [int(x) for x in current_version.split('.')]

        # Major version must match
        if profile_parts[0] != current_parts[0]:
            return False

        # Minor version must be <= current
        if profile_parts[1] > current_parts[1]:
            return False

        return True
    except (ValueError, IndexError):
        return False


def migrate_profile_schema(profile_data: Dict[str, Any], target_version: str = PROFILE_SCHEMA_VERSION) -> Dict[str, Any]:
    """
    Migrate profile data between schema versions
    Currently only supports migration to current version
    """
    current_version = profile_data.get('schema_version')

    if not current_version:
        # Legacy profile without version - add current version
        profile_data['schema_version'] = target_version
        if 'generated_at' not in profile_data:
            profile_data['generated_at'] = datetime.now().isoformat()

    elif current_version != target_version:
        if not is_schema_compatible(current_version, target_version):
            raise ValueError(f"Cannot migrate from schema version {current_version} to {target_version}")

        # Update version
        profile_data['schema_version'] = target_version

    return profile_data