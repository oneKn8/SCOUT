"""
Profile JSON validator service for SCOUT resume parser
Provides validation functions to ensure parser outputs conform to schema
"""

import json
from typing import Dict, Any, List, Tuple, Optional
from pydantic import ValidationError
import structlog

from app.models.profile_schema import (
    ProfileJSONSchema,
    get_schema_version,
    is_schema_compatible,
    migrate_profile_schema,
    PROFILE_SCHEMA_VERSION
)

logger = structlog.get_logger()


class ProfileValidationResult:
    """Container for profile validation results"""

    def __init__(self, is_valid: bool, profile: Optional[ProfileJSONSchema] = None,
                 errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.profile = profile
        self.errors = errors or []
        self.warnings = warnings or []

    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "profile_valid": self.profile is not None,
            "schema_version": self.profile.schema_version if self.profile else None
        }


class ProfileValidator:
    """Service for validating profile JSON against schema"""

    @staticmethod
    def validate_profile(profile_data: Dict[str, Any],
                        strict: bool = True,
                        job_id: Optional[str] = None) -> ProfileValidationResult:
        """
        Validate a profile dictionary against the ProfileJSON schema

        Args:
            profile_data: Dictionary containing profile data
            strict: Whether to perform strict validation (default: True)
            job_id: Optional job ID for logging context

        Returns:
            ProfileValidationResult with validation details
        """
        logger.info(
            "Profile validation started",
            job_id=job_id,
            strict=strict,
            data_keys=list(profile_data.keys()) if profile_data else []
        )

        errors = []
        warnings = []

        try:
            # Check and migrate schema version if needed
            current_version = profile_data.get('schema_version')
            if not current_version:
                warnings.append(f"No schema version found, assuming {PROFILE_SCHEMA_VERSION}")
                profile_data['schema_version'] = PROFILE_SCHEMA_VERSION

            elif current_version != PROFILE_SCHEMA_VERSION:
                if is_schema_compatible(current_version, PROFILE_SCHEMA_VERSION):
                    profile_data = migrate_profile_schema(profile_data)
                    warnings.append(f"Migrated schema from {current_version} to {PROFILE_SCHEMA_VERSION}")
                else:
                    errors.append(f"Incompatible schema version: {current_version} (current: {PROFILE_SCHEMA_VERSION})")
                    if strict:
                        return ProfileValidationResult(False, errors=errors, warnings=warnings)

            # Validate against Pydantic model
            profile = ProfileJSONSchema(**profile_data)

            logger.info(
                "Profile validation completed successfully",
                job_id=job_id,
                schema_version=profile.schema_version,
                sections=len([s for s in [profile.contact, profile.summary] if s is not None]) +
                        len(profile.experience) + len(profile.education) + len(profile.skills),
                warnings_count=len(warnings)
            )

            return ProfileValidationResult(True, profile=profile, warnings=warnings)

        except ValidationError as e:
            # Parse Pydantic validation errors
            for error in e.errors():
                field_path = " -> ".join(str(x) for x in error['loc'])
                error_msg = f"Field '{field_path}': {error['msg']}"
                errors.append(error_msg)

            logger.warning(
                "Profile validation failed with Pydantic errors",
                job_id=job_id,
                error_count=len(errors),
                errors=errors[:3]  # Log first 3 errors
            )

            if not strict:
                # In non-strict mode, try to create a partial profile
                try:
                    # Remove problematic fields and retry
                    cleaned_data = ProfileValidator._clean_invalid_fields(profile_data, e.errors())
                    profile = ProfileJSONSchema(**cleaned_data)
                    warnings.extend([f"Removed invalid field: {err}" for err in errors])
                    errors = []  # Convert errors to warnings in non-strict mode

                    return ProfileValidationResult(True, profile=profile, warnings=warnings)
                except Exception as clean_error:
                    errors.append(f"Failed to clean invalid fields: {str(clean_error)}")

            return ProfileValidationResult(False, errors=errors, warnings=warnings)

        except Exception as e:
            error_msg = f"Unexpected validation error: {str(e)}"
            errors.append(error_msg)

            logger.error(
                "Profile validation failed with unexpected error",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )

            return ProfileValidationResult(False, errors=errors, warnings=warnings)

    @staticmethod
    def validate_profile_json(profile_json: str,
                            strict: bool = True,
                            job_id: Optional[str] = None) -> ProfileValidationResult:
        """
        Validate a profile JSON string

        Args:
            profile_json: JSON string containing profile data
            strict: Whether to perform strict validation
            job_id: Optional job ID for logging context

        Returns:
            ProfileValidationResult with validation details
        """
        try:
            profile_data = json.loads(profile_json)
            return ProfileValidator.validate_profile(profile_data, strict=strict, job_id=job_id)

        except json.JSONDecodeError as e:
            logger.warning(
                "Profile JSON parsing failed",
                job_id=job_id,
                error=str(e)
            )
            return ProfileValidationResult(False, errors=[f"Invalid JSON: {str(e)}"])

    @staticmethod
    def validate_parser_output(parser_result: Dict[str, Any],
                             job_id: Optional[str] = None) -> ProfileValidationResult:
        """
        Validate output from parser service against ProfileJSON schema

        Args:
            parser_result: Result dictionary from parser service
            job_id: Job ID for logging context

        Returns:
            ProfileValidationResult with validation details
        """
        logger.info(
            "Parser output validation started",
            job_id=job_id,
            has_result=parser_result is not None,
            result_keys=list(parser_result.keys()) if parser_result else []
        )

        if not parser_result:
            return ProfileValidationResult(False, errors=["Parser result is empty"])

        # Extract the actual profile data from parser result
        # Parser returns: {"extraction_method": ..., "sections": ..., "metadata": ...}
        # We need to transform this to ProfileJSON format
        try:
            profile_data = ProfileValidator._transform_parser_output(parser_result)
            return ProfileValidator.validate_profile(profile_data, strict=False, job_id=job_id)

        except Exception as e:
            logger.error(
                "Failed to transform parser output",
                job_id=job_id,
                error=str(e),
                exc_info=True
            )
            return ProfileValidationResult(False, errors=[f"Parser output transformation failed: {str(e)}"])

    @staticmethod
    def _transform_parser_output(parser_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform parser service output to ProfileJSON schema format

        Args:
            parser_result: Raw parser output

        Returns:
            Dictionary conforming to ProfileJSON schema
        """
        from datetime import datetime
        import os

        # Extract file name without path for privacy
        source_file = parser_result.get('file_path', 'unknown.docx')
        if source_file and '/' in source_file:
            source_file = os.path.basename(source_file)

        # Build ProfileJSON structure
        profile_data = {
            "schema_version": get_schema_version(),
            "generated_at": datetime.now(),
            "extraction_method": parser_result.get('extraction_method', 'unknown'),
            "source_file": source_file,

            # Transform sections
            "contact": ProfileValidator._extract_contact_section(
                parser_result.get('sections', {}).get('contact', {})
            ),
            "summary": ProfileValidator._extract_summary_section(
                parser_result.get('sections', {}).get('summary')
            ),
            "experience": ProfileValidator._extract_experience_section(
                parser_result.get('sections', {}).get('experience', [])
            ),
            "education": ProfileValidator._extract_education_section(
                parser_result.get('sections', {}).get('education', [])
            ),
            "skills": ProfileValidator._extract_skills_section(
                parser_result.get('sections', {}).get('skills', [])
            ),
            "projects": ProfileValidator._extract_projects_section(
                parser_result.get('sections', {}).get('projects', [])
            ),
            "achievements": ProfileValidator._extract_achievements_section(
                parser_result.get('sections', {}).get('achievements', [])
            ),

            # Metadata
            "metadata": {
                "extractor_version": parser_result.get('metadata', {}).get('extractor_version', '0.1.0'),
                "extraction_timestamp": datetime.now(),
                "confidence_score": parser_result.get('metadata', {}).get('confidence_score', 0.0),
                "source_file_hash": None,  # Not available from current parser
                "file_type": ProfileValidator._detect_file_type(source_file),
                "sections_detected": list(parser_result.get('sections', {}).keys())
            },

            "warnings": parser_result.get('warnings', []),
            "errors": []
        }

        return profile_data

    @staticmethod
    def _extract_contact_section(contact_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate contact section"""
        if not contact_data:
            return None

        return {
            "full_name": contact_data.get('name') or contact_data.get('full_name'),
            "email": contact_data.get('email'),
            "phone": contact_data.get('phone'),
            "location": contact_data.get('location'),
            "website": contact_data.get('website'),
            "linkedin": contact_data.get('linkedin'),
            "github": contact_data.get('github'),
            "address": contact_data.get('address'),
            "social_profiles": contact_data.get('social_profiles', {})
        }

    @staticmethod
    def _extract_summary_section(summary_data) -> Optional[Dict[str, Any]]:
        """Extract and validate summary section"""
        if not summary_data:
            return None

        # Handle string input (simple text summary)
        if isinstance(summary_data, str):
            return {
                "text": summary_data,
                "objective": None,
                "keywords": []
            }

        # Handle dictionary input (structured summary)
        if isinstance(summary_data, dict):
            return {
                "text": summary_data.get('text'),
                "objective": summary_data.get('objective'),
                "keywords": summary_data.get('keywords', [])
            }

        return None

    @staticmethod
    def _extract_experience_section(experience_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and validate experience section"""
        if not isinstance(experience_data, list):
            return []

        result = []
        for exp in experience_data:
            if isinstance(exp, dict):
                result.append({
                    "company": exp.get('company'),
                    "position": exp.get('position') or exp.get('title'),
                    "location": exp.get('location'),
                    "dates": ProfileValidator._extract_date_range(exp.get('dates')),
                    "description": exp.get('description'),
                    "responsibilities": exp.get('responsibilities', []),
                    "technologies": exp.get('technologies', []),
                    "confidence_score": exp.get('confidence_score', 0.0),
                    "warnings": exp.get('warnings', [])
                })

        return result

    @staticmethod
    def _extract_education_section(education_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and validate education section"""
        if not isinstance(education_data, list):
            return []

        result = []
        for edu in education_data:
            if isinstance(edu, dict):
                result.append({
                    "institution": edu.get('institution') or edu.get('school'),
                    "degree": edu.get('degree'),
                    "field_of_study": edu.get('field_of_study') or edu.get('major'),
                    "location": edu.get('location'),
                    "dates": ProfileValidator._extract_date_range(edu.get('dates')),
                    "gpa": edu.get('gpa'),
                    "honors": edu.get('honors', []),
                    "relevant_coursework": edu.get('relevant_coursework', []),
                    "confidence_score": edu.get('confidence_score', 0.0),
                    "warnings": edu.get('warnings', [])
                })

        return result

    @staticmethod
    def _extract_skills_section(skills_data: List[Any]) -> List[Dict[str, Any]]:
        """Extract and validate skills section"""
        if not isinstance(skills_data, list):
            return []

        result = []
        for skill in skills_data:
            if isinstance(skill, str):
                # Simple string skill
                result.append({
                    "name": skill,
                    "category": None,
                    "proficiency_level": None,
                    "confidence_score": 1.0
                })
            elif isinstance(skill, dict):
                # Structured skill object
                result.append({
                    "name": skill.get('name') or str(skill),
                    "category": skill.get('category'),
                    "proficiency_level": skill.get('proficiency_level'),
                    "years_experience": skill.get('years_experience'),
                    "canonical_name": skill.get('canonical_name'),
                    "aliases": skill.get('aliases', []),
                    "context": skill.get('context'),
                    "confidence_score": skill.get('confidence_score', 1.0)
                })

        return result

    @staticmethod
    def _extract_projects_section(projects_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and validate projects section"""
        if not isinstance(projects_data, list):
            return []

        result = []
        for project in projects_data:
            if isinstance(project, dict):
                result.append({
                    "name": project.get('name') or project.get('title', 'Unnamed Project'),
                    "description": project.get('description'),
                    "url": project.get('url') or project.get('link'),
                    "dates": ProfileValidator._extract_date_range(project.get('dates')),
                    "technologies": project.get('technologies', []),
                    "role": project.get('role'),
                    "team_size": project.get('team_size'),
                    "confidence_score": project.get('confidence_score', 0.0)
                })

        return result

    @staticmethod
    def _extract_achievements_section(achievements_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract and validate achievements section"""
        if not isinstance(achievements_data, list):
            return []

        result = []
        for achievement in achievements_data:
            if isinstance(achievement, dict):
                result.append({
                    "title": achievement.get('title') or achievement.get('name', 'Achievement'),
                    "organization": achievement.get('organization') or achievement.get('issuer'),
                    "date_received": achievement.get('date_received') or achievement.get('date'),
                    "description": achievement.get('description'),
                    "type": achievement.get('type'),
                    "expiration_date": achievement.get('expiration_date'),
                    "credential_id": achievement.get('credential_id'),
                    "verification_url": achievement.get('verification_url')
                })

        return result

    @staticmethod
    def _extract_date_range(date_data: Any) -> Optional[Dict[str, Any]]:
        """Extract and validate date range"""
        if not date_data:
            return None

        if isinstance(date_data, dict):
            return {
                "start_date": date_data.get('start_date') or date_data.get('start'),
                "end_date": date_data.get('end_date') or date_data.get('end'),
                "is_current": date_data.get('is_current', False),
                "raw_date_text": date_data.get('raw_date_text') or date_data.get('raw')
            }

        return None

    @staticmethod
    def _detect_file_type(filename: str) -> str:
        """Detect file type from filename"""
        if not filename:
            return 'unknown'

        extension = filename.lower().split('.')[-1] if '.' in filename else ''
        if extension in ['docx', 'doc']:
            return 'docx'
        elif extension == 'pdf':
            return 'pdf'
        elif extension in ['txt', 'text']:
            return 'txt'
        else:
            return 'unknown'

    @staticmethod
    def _clean_invalid_fields(profile_data: Dict[str, Any],
                            validation_errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove invalid fields from profile data for non-strict validation

        Args:
            profile_data: Original profile data
            validation_errors: List of Pydantic validation errors

        Returns:
            Cleaned profile data
        """
        cleaned_data = profile_data.copy()

        for error in validation_errors:
            field_path = error['loc']
            if len(field_path) == 1:
                # Top-level field
                field_name = field_path[0]
                if field_name in cleaned_data:
                    del cleaned_data[field_name]

        return cleaned_data


# Convenience functions for common validation scenarios

def validate_parser_output(parser_result: Dict[str, Any], job_id: Optional[str] = None) -> ProfileValidationResult:
    """Quick validation of parser output"""
    return ProfileValidator.validate_parser_output(parser_result, job_id=job_id)


def is_valid_profile(profile_data: Dict[str, Any]) -> bool:
    """Quick boolean check for profile validity"""
    result = ProfileValidator.validate_profile(profile_data, strict=False)
    return result.is_valid


def get_profile_errors(profile_data: Dict[str, Any]) -> List[str]:
    """Get list of validation errors for profile"""
    result = ProfileValidator.validate_profile(profile_data, strict=True)
    return result.errors