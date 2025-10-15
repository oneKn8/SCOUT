"""
PII-aware logging and redaction filters
Automatically redacts sensitive information from logs before output
"""

import re
import hashlib
import structlog
from typing import Any, Dict, List, Union, Optional
from datetime import datetime


class PIIRedactor:
    """
    Service for detecting and redacting PII from log messages
    Uses pattern matching and hashing for secure log correlation
    """

    # PII Detection Patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', re.IGNORECASE)
    PHONE_PATTERN = re.compile(r'[\+]?[1-9]?[\d\s\-\(\)\.]{7,15}\d', re.MULTILINE)
    NAME_PATTERN = re.compile(r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b')  # Simple first+last name
    URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+', re.IGNORECASE)
    ADDRESS_PATTERN = re.compile(r'\b\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Drive|Dr|Lane|Ln|Boulevard|Blvd)\b', re.IGNORECASE)

    # Social Security Number (US)
    SSN_PATTERN = re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b')

    # Credit Card Numbers (basic pattern)
    CREDIT_CARD_PATTERN = re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b')

    # File paths that might contain user data
    FILEPATH_PATTERN = re.compile(r'[/\\](?:home|Users)[/\\]([^/\\]+)', re.IGNORECASE)

    # Common PII field names in structured data
    PII_FIELD_NAMES = {
        'email', 'mail', 'e_mail', 'email_address',
        'phone', 'telephone', 'mobile', 'cell', 'phone_number',
        'name', 'full_name', 'first_name', 'last_name', 'username',
        'address', 'street', 'home_address', 'billing_address',
        'ssn', 'social_security', 'passport', 'license',
        'password', 'passwd', 'secret', 'key', 'token',
        'ip', 'ip_address', 'ipv4', 'ipv6'
    }

    def __init__(self):
        self.logger = structlog.get_logger(__name__)

    def redact_text(self, text: str) -> str:
        """
        Redact PII from a text string

        Args:
            text: Input text to redact

        Returns:
            str: Text with PII replaced by hashed placeholders
        """
        if not text or not isinstance(text, str):
            return text

        original_text = text

        # Email addresses
        text = self._redact_pattern(text, self.EMAIL_PATTERN, 'email')

        # Phone numbers
        text = self._redact_pattern(text, self.PHONE_PATTERN, 'phone')

        # URLs
        text = self._redact_pattern(text, self.URL_PATTERN, 'url')

        # Names (conservative pattern)
        text = self._redact_pattern(text, self.NAME_PATTERN, 'name')

        # Addresses
        text = self._redact_pattern(text, self.ADDRESS_PATTERN, 'address')

        # SSN
        text = self._redact_pattern(text, self.SSN_PATTERN, 'ssn')

        # Credit cards
        text = self._redact_pattern(text, self.CREDIT_CARD_PATTERN, 'creditcard')

        # File paths with usernames
        text = self._redact_filepath_usernames(text)

        return text

    def redact_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact PII from dictionary/structured data

        Args:
            data: Dictionary to redact

        Returns:
            Dict: Dictionary with PII values redacted
        """
        if not isinstance(data, dict):
            return data

        redacted = {}

        for key, value in data.items():
            key_lower = key.lower()

            # Check if key indicates PII field
            if any(pii_field in key_lower for pii_field in self.PII_FIELD_NAMES):
                redacted[key] = self._redact_value(value, key_lower)
            elif isinstance(value, str):
                # Redact text values
                redacted[key] = self.redact_text(value)
            elif isinstance(value, dict):
                # Recursively process nested dictionaries
                redacted[key] = self.redact_dict(value)
            elif isinstance(value, list):
                # Process list values
                redacted[key] = self._redact_list(value)
            else:
                # Keep non-string values as-is
                redacted[key] = value

        return redacted

    def _redact_list(self, data: List[Any]) -> List[Any]:
        """Redact PII from list items"""
        redacted = []

        for item in data:
            if isinstance(item, str):
                redacted.append(self.redact_text(item))
            elif isinstance(item, dict):
                redacted.append(self.redact_dict(item))
            elif isinstance(item, list):
                redacted.append(self._redact_list(item))
            else:
                redacted.append(item)

        return redacted

    def _redact_pattern(self, text: str, pattern: re.Pattern, label: str) -> str:
        """
        Replace matches of a pattern with hashed placeholders

        Args:
            text: Text to process
            pattern: Regex pattern to match
            label: Label for the placeholder (e.g., 'email', 'phone')

        Returns:
            str: Text with matches replaced
        """
        def replacement(match):
            original = match.group(0)
            hash_suffix = self._hash_value(original)[:8]
            return f"{label}_[{hash_suffix}]"

        return pattern.sub(replacement, text)

    def _redact_filepath_usernames(self, text: str) -> str:
        """Redact usernames from file paths"""
        def replacement(match):
            username = match.group(1)
            hash_suffix = self._hash_value(username)[:8]
            return match.group(0).replace(username, f"user_[{hash_suffix}]")

        return self.FILEPATH_PATTERN.sub(replacement, text)

    def _redact_value(self, value: Any, field_name: str) -> str:
        """
        Redact a value based on its field name

        Args:
            value: Value to redact
            field_name: Name of the field (lowercase)

        Returns:
            str: Redacted value
        """
        if not value:
            return value

        value_str = str(value)
        hash_suffix = self._hash_value(value_str)[:8]

        # Determine appropriate label based on field name
        if 'email' in field_name or 'mail' in field_name:
            return f"email_[{hash_suffix}]"
        elif 'phone' in field_name or 'mobile' in field_name:
            return f"phone_[{hash_suffix}]"
        elif 'name' in field_name:
            return f"name_[{hash_suffix}]"
        elif 'address' in field_name:
            return f"address_[{hash_suffix}]"
        elif 'password' in field_name or 'secret' in field_name:
            return f"secret_[{hash_suffix}]"
        elif 'ip' in field_name:
            return f"ip_[{hash_suffix}]"
        else:
            return f"pii_[{hash_suffix}]"

    def _hash_value(self, value: str) -> str:
        """
        Create a SHA256 hash of a value for correlation

        Args:
            value: Value to hash

        Returns:
            str: Hex digest of hash
        """
        return hashlib.sha256(value.encode('utf-8')).hexdigest()

    def test_redaction(self) -> Dict[str, Any]:
        """
        Test the redaction system with sample data

        Returns:
            Dict: Test results showing before/after
        """
        test_cases = [
            "Contact John Doe at john.doe@example.com or call (555) 123-4567",
            "Visit https://github.com/user/repo for more info",
            "Lives at 123 Main Street, Anytown USA",
            "SSN: 123-45-6789, Card: 4111-1111-1111-1111",
            "/home/johndoe/documents/resume.pdf"
        ]

        test_dict = {
            "email": "test@example.com",
            "phone": "(555) 987-6543",
            "full_name": "Jane Smith",
            "password": "secret123",
            "normal_field": "This is normal data"
        }

        results = {
            "text_redaction": [],
            "dict_redaction": {
                "original": test_dict,
                "redacted": self.redact_dict(test_dict)
            },
            "test_timestamp": datetime.now().isoformat()
        }

        for test_text in test_cases:
            results["text_redaction"].append({
                "original": test_text,
                "redacted": self.redact_text(test_text)
            })

        return results


# Global PII redactor instance
pii_redactor = PIIRedactor()


# Structlog processor for automatic PII redaction
def redact_pii_processor(logger, method_name, event_dict):
    """
    Structlog processor that automatically redacts PII from log events

    Args:
        logger: Logger instance
        method_name: Logging method name
        event_dict: Event dictionary to process

    Returns:
        Dict: Processed event dictionary with PII redacted
    """
    try:
        # Redact the main event message
        if 'event' in event_dict and isinstance(event_dict['event'], str):
            event_dict['event'] = pii_redactor.redact_text(event_dict['event'])

        # Redact structured fields
        redacted_dict = pii_redactor.redact_dict(event_dict)

        # Mark as redacted for audit trail
        redacted_dict['_pii_redacted'] = True

        return redacted_dict

    except Exception as e:
        # If redaction fails, log the error but don't block logging
        # Add error info without potentially exposing the original data
        event_dict['_redaction_error'] = 'PII redaction failed'
        event_dict['_pii_redacted'] = False
        return event_dict