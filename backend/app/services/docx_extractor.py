"""
DOCX Resume Extractor with Deterministic Rules
Implements section detection and content extraction for DOCX files
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dateutil import parser as date_parser
import structlog
import io

try:
    from docx import Document
    from docx.document import Document as DocumentType
    from docx.text.paragraph import Paragraph
except ImportError:
    Document = None
    DocumentType = None
    Paragraph = None

from app.services.file_service import FileService

logger = structlog.get_logger()


class DOCXExtractor:
    """
    DOCX resume parser using deterministic rules for section detection
    """

    # Section headers patterns (case-insensitive)
    SECTION_PATTERNS = {
        'contact': [
            r'\b(contact|personal\s+info|personal\s+information)\b',
        ],
        'summary': [
            r'\b(summary|objective|profile|overview|about)\b',
            r'\b(professional\s+summary|career\s+summary)\b',
            r'\b(executive\s+summary)\b'
        ],
        'experience': [
            r'\b(experience|employment|work\s+history|professional\s+experience)\b',
            r'\b(work\s+experience|career\s+history|employment\s+history)\b'
        ],
        'education': [
            r'\b(education|academic|qualifications|degrees)\b',
            r'\b(educational\s+background|academic\s+background)\b'
        ],
        'skills': [
            r'\b(skills|technical\s+skills|core\s+competencies)\b',
            r'\b(technologies|expertise|competencies|proficiencies)\b'
        ],
        'projects': [
            r'\b(projects|key\s+projects|notable\s+projects)\b',
            r'\b(project\s+experience|personal\s+projects)\b'
        ],
        'achievements': [
            r'\b(achievements|accomplishments|awards|honors)\b',
            r'\b(recognition|certifications)\b'
        ]
    }

    # Email and phone patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'[\+]?[1-9]?[\d\s\-\(\)\.]{8,15}\d')
    URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+')

    # Date patterns for experience
    DATE_PATTERNS = [
        r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4}\b',
        r'\b\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        r'\b\d{4}\s*[\-\–]\s*\d{4}\b',
        r'\b\d{4}\s*[\-\–]\s*(present|current)\b'
    ]

    def __init__(self):
        if Document is None:
            raise ImportError("python-docx is required for DOCX extraction")

    async def extract(self, file_path: Path, job_id: str) -> Dict[str, Any]:
        """
        Main extraction method for DOCX files

        Args:
            file_path: Path to DOCX file
            job_id: Job ID for logging

        Returns:
            ProfileJSON-compatible dictionary
        """
        logger.info(
            "Starting DOCX extraction",
            job_id=job_id,
            file_path=str(file_path)
        )

        try:
            # Read and decrypt file content
            file_content = FileService.read_encrypted_file(str(file_path))

            # Load DOCX document from decrypted content
            document = Document(io.BytesIO(file_content))

            # Extract all paragraphs with their styles
            paragraphs = self._extract_paragraphs(document)

            # Detect sections
            sections = self._detect_sections(paragraphs, job_id)

            # Extract content from each section
            extracted_data = await self._extract_content(sections, paragraphs, job_id)

            # Normalize and validate
            result = self._normalize_output(extracted_data, job_id)

            logger.info(
                "DOCX extraction completed",
                job_id=job_id,
                sections_found=len(result.get('sections', {})),
                warnings=len(result.get('warnings', []))
            )

            return result

        except Exception as e:
            logger.error(
                "DOCX extraction failed",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise

    def _extract_paragraphs(self, document: DocumentType) -> List[Dict[str, Any]]:
        """Extract all paragraphs with metadata"""
        paragraphs = []

        for i, paragraph in enumerate(document.paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue

            # Detect if paragraph is likely a header
            is_header = self._is_likely_header(paragraph)

            paragraphs.append({
                'index': i,
                'text': text,
                'is_header': is_header,
                'style': paragraph.style.name if paragraph.style else None,
                'runs': [run.text for run in paragraph.runs],
                'is_bold': any(run.bold for run in paragraph.runs),
                'font_size': self._get_font_size(paragraph)
            })

        return paragraphs

    def _is_likely_header(self, paragraph: Paragraph) -> bool:
        """Determine if paragraph is likely a section header"""
        # Check if text is short and might be a header
        text = paragraph.text.strip()
        if len(text) > 50:
            return False

        # Check formatting indicators
        has_bold = any(run.bold for run in paragraph.runs)
        is_uppercase = text.isupper()

        # Check if matches section patterns
        matches_pattern = any(
            any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)
            for patterns in self.SECTION_PATTERNS.values()
        )

        return (has_bold or is_uppercase) and matches_pattern

    def _get_font_size(self, paragraph: Paragraph) -> Optional[int]:
        """Get font size of paragraph if available"""
        for run in paragraph.runs:
            if run.font.size:
                return int(run.font.size.pt)
        return None

    def _detect_sections(self, paragraphs: List[Dict], job_id: str) -> Dict[str, List[int]]:
        """
        Detect section boundaries in the document

        Returns:
            Dictionary mapping section names to paragraph indices
        """
        sections = {}
        current_section = None

        for para in paragraphs:
            text = para['text'].lower()

            # Check for section headers
            detected_section = None
            for section_name, patterns in self.SECTION_PATTERNS.items():
                if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
                    detected_section = section_name
                    break

            if detected_section and para['is_header']:
                current_section = detected_section
                if current_section not in sections:
                    sections[current_section] = []
                logger.debug(
                    "Section detected",
                    job_id=job_id,
                    section=current_section,
                    header_text=para['text'][:50]
                )
            elif current_section:
                # Add content to current section
                sections[current_section].append(para['index'])

        logger.info(
            "Section detection completed",
            job_id=job_id,
            sections_found=list(sections.keys())
        )

        return sections

    async def _extract_content(self, sections: Dict, paragraphs: List[Dict], job_id: str) -> Dict[str, Any]:
        """Extract and structure content from detected sections"""
        extracted = {
            'contact': {},
            'summary': '',
            'experience': [],
            'education': [],
            'skills': [],
            'projects': [],
            'achievements': [],
            'warnings': []
        }

        # Extract contact information from entire document first
        all_text = ' '.join(p['text'] for p in paragraphs)
        extracted['contact'] = self._extract_contact_info(all_text)

        # Process each section
        for section_name, para_indices in sections.items():
            # Filter out invalid indices
            valid_indices = [i for i in para_indices if 0 <= i < len(paragraphs)]
            section_text = '\n'.join(paragraphs[i]['text'] for i in valid_indices)

            if section_name == 'summary':
                extracted['summary'] = self._clean_text(section_text)

            elif section_name == 'experience':
                extracted['experience'] = self._extract_experience(section_text, job_id)

            elif section_name == 'education':
                extracted['education'] = self._extract_education(section_text, job_id)

            elif section_name == 'skills':
                extracted['skills'] = self._extract_skills(section_text)

            elif section_name == 'projects':
                extracted['projects'] = self._extract_projects(section_text, job_id)

            elif section_name == 'achievements':
                extracted['achievements'] = self._extract_achievements(section_text)

        return extracted

    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract contact information from text"""
        contact = {}

        # Extract email
        emails = self.EMAIL_PATTERN.findall(text)
        if emails:
            contact['email'] = emails[0]

        # Extract phone
        phones = self.PHONE_PATTERN.findall(text)
        if phones:
            contact['phone'] = phones[0].strip()

        # Extract URLs
        urls = self.URL_PATTERN.findall(text)
        if urls:
            contact['urls'] = urls[:3]  # Limit to 3 URLs

        return contact

    def _extract_experience(self, text: str, job_id: str) -> List[Dict[str, Any]]:
        """Extract work experience entries"""
        experience = []

        # Split by potential job entries (look for company/role patterns)
        entries = re.split(r'\n(?=[A-Z][^\n]*(?:,|\n))', text)

        for entry in entries:
            entry = entry.strip()
            if len(entry) < 10:  # Skip very short entries
                continue

            exp_item = self._parse_experience_entry(entry)
            if exp_item:
                experience.append(exp_item)

        logger.debug(
            "Experience extraction completed",
            job_id=job_id,
            entries_found=len(experience)
        )

        return experience

    def _parse_experience_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single experience entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None

        exp = {
            'company': '',
            'title': '',
            'duration': '',
            'responsibilities': []
        }

        # Skip lines that start with bullet points for title/company detection
        title_lines = []
        responsibility_lines = []

        for line in lines:
            line = line.strip()
            # Check if line is a bullet point or responsibility
            if re.match(r'^[\•\-\*\+]\s*', line) or line.lower().startswith(('developed', 'managed', 'led', 'built', 'implemented', 'improved', 'collaborated')):
                # Clean bullet markers and add to responsibilities
                clean_line = re.sub(r'^[\•\-\*\+]\s*', '', line)
                if clean_line:
                    responsibility_lines.append(clean_line)
            else:
                title_lines.append(line)

        # Extract company and title from non-bullet lines
        if title_lines:
            first_line = title_lines[0]

            # Look for dates in all lines to find duration
            for line in lines:
                date_match = self._extract_dates(line)
                if date_match:
                    exp['duration'] = date_match
                    break

            # Try to separate company and title
            if '|' in first_line:
                parts = first_line.split('|', 1)
                exp['title'] = parts[0].strip()
                exp['company'] = parts[1].strip()
            elif ' - ' in first_line:
                parts = first_line.split(' - ', 1)
                exp['title'] = parts[0].strip()
                exp['company'] = parts[1].strip()
            elif ',' in first_line and not self._extract_dates(first_line):
                parts = first_line.split(',', 1)
                exp['title'] = parts[0].strip()
                exp['company'] = parts[1].strip()
            else:
                # If no clear separator, assume it's a title
                exp['title'] = first_line

                # Check if second line could be company
                if len(title_lines) > 1 and not self._extract_dates(title_lines[1]):
                    exp['company'] = title_lines[1]

        exp['responsibilities'] = responsibility_lines

        return exp if exp['company'] or exp['title'] or exp['responsibilities'] else None

    def _extract_dates(self, text: str) -> Optional[str]:
        """Extract date ranges from text"""
        for pattern in self.DATE_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                return matches[0] if isinstance(matches[0], str) else ' - '.join(matches[0])
        return None

    def _extract_education(self, text: str, job_id: str) -> List[Dict[str, Any]]:
        """Extract education entries"""
        education = []

        # Split by potential education entries
        entries = re.split(r'\n(?=[A-Z][^\n]*(?:University|College|Institute|School))', text)

        for entry in entries:
            entry = entry.strip()
            if len(entry) < 5:
                continue

            edu_item = self._parse_education_entry(entry)
            if edu_item:
                education.append(edu_item)

        return education

    def _parse_education_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single education entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None

        edu = {
            'degree': '',
            'institution': '',
            'year': '',
            'details': []
        }

        # First line often contains degree and institution
        first_line = lines[0]

        # Look for institution keywords
        institution_keywords = ['university', 'college', 'institute', 'school']
        for keyword in institution_keywords:
            if keyword.lower() in first_line.lower():
                parts = first_line.split(keyword, 1)
                if len(parts) == 2:
                    edu['degree'] = parts[0].strip()
                    edu['institution'] = (parts[1].strip() + ' ' + keyword).strip()
                break

        if not edu['institution']:
            edu['degree'] = first_line

        # Look for graduation year
        for line in lines:
            year_match = re.search(r'\b(19|20)\d{2}\b', line)
            if year_match:
                edu['year'] = year_match.group()
                break

        return edu if edu['degree'] or edu['institution'] else None

    def _extract_skills(self, text: str) -> List[str]:
        """Extract skills from skills section"""
        # Remove common prefixes and clean text
        text = re.sub(r'^(skills?|technologies?|tools?):?\s*', '', text, flags=re.IGNORECASE)

        # Split by various delimiters
        skills = re.split(r'[,;\n\|•\-\*\+]+', text)

        # Clean and filter skills
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            if skill and len(skill) > 1 and len(skill) < 50:  # Filter reasonable skills
                cleaned_skills.append(skill)

        return cleaned_skills

    def _extract_projects(self, text: str, job_id: str) -> List[Dict[str, Any]]:
        """Extract project entries"""
        projects = []

        # Split by potential project entries
        entries = re.split(r'\n(?=[A-Z][^\n]*(?:\n|$))', text)

        for entry in entries:
            entry = entry.strip()
            if len(entry) < 10:
                continue

            proj_item = self._parse_project_entry(entry)
            if proj_item:
                projects.append(proj_item)

        return projects

    def _parse_project_entry(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse a single project entry"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None

        project = {
            'name': lines[0],
            'description': '',
            'technologies': [],
            'details': []
        }

        # Combine remaining lines as description and details
        if len(lines) > 1:
            project['description'] = ' '.join(lines[1:])

        return project

    def _extract_achievements(self, text: str) -> List[str]:
        """Extract achievements/awards"""
        achievements = []

        # Split by bullet points or lines
        items = re.split(r'[\n•\-\*\+]+', text)

        for item in items:
            item = item.strip()
            if item and len(item) > 5:
                achievements.append(item)

        return achievements

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text.strip())

        # Remove bullet markers at start
        text = re.sub(r'^[\•\-\*\+]\s*', '', text)

        return text

    def _normalize_output(self, extracted: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Normalize and structure the final output"""
        warnings = extracted.get('warnings', [])

        # Add warnings for missing sections
        if not extracted.get('contact', {}).get('email'):
            warnings.append("No email address found")

        if not extracted.get('experience'):
            warnings.append("No work experience found")

        result = {
            "extraction_method": "docx_deterministic",
            "sections": {
                "contact": extracted.get('contact', {}),
                "summary": extracted.get('summary', ''),
                "experience": extracted.get('experience', []),
                "education": extracted.get('education', []),
                "skills": extracted.get('skills', []),
                "projects": extracted.get('projects', []),
                "achievements": extracted.get('achievements', [])
            },
            "warnings": warnings,
            "metadata": {
                "extractor_version": "1.0.0",
                "extraction_timestamp": datetime.now().isoformat(),
                "confidence_score": self._calculate_confidence_score(extracted)
            }
        }

        return result

    def _calculate_confidence_score(self, extracted: Dict[str, Any]) -> float:
        """Calculate extraction confidence score"""
        score = 0.0

        # Award points for found sections
        if extracted.get('contact', {}).get('email'):
            score += 0.2
        if extracted.get('summary'):
            score += 0.1
        if extracted.get('experience'):
            score += 0.3
        if extracted.get('education'):
            score += 0.2
        if extracted.get('skills'):
            score += 0.2

        return min(score, 1.0)