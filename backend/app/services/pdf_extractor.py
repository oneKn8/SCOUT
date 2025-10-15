"""
PDF Resume Extractor with Heuristic Fallback
Implements basic text extraction for PDF files with known limitations
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

try:
    import pdfplumber
    from PyPDF2 import PdfReader
except ImportError:
    pdfplumber = None
    PdfReader = None

logger = structlog.get_logger()


class PDFExtractor:
    """
    PDF resume parser using heuristic text extraction
    Has known limitations with tables, multi-column layouts, and images
    """

    # Section headers patterns (same as DOCX extractor)
    SECTION_PATTERNS = {
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

    # Contact patterns
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    PHONE_PATTERN = re.compile(r'[\+]?[1-9]?[\d\s\-\(\)\.]{8,15}\d')
    URL_PATTERN = re.compile(r'https?://[^\s]+|www\.[^\s]+')

    def __init__(self):
        if not pdfplumber or not PdfReader:
            raise ImportError("pdfplumber and PyPDF2 are required for PDF extraction")

    async def extract(self, file_path: Path, job_id: str) -> Dict[str, Any]:
        """
        Main extraction method for PDF files

        Args:
            file_path: Path to PDF file
            job_id: Job ID for logging

        Returns:
            ProfileJSON-compatible dictionary
        """
        logger.info(
            "Starting PDF extraction",
            job_id=job_id,
            file_path=str(file_path)
        )

        warnings = [
            "PDF extraction has limitations with complex layouts",
            "Tables and multi-column formats may not parse correctly",
            "Some formatting information may be lost"
        ]

        try:
            # Try pdfplumber first (better text extraction)
            text_content = await self._extract_with_pdfplumber(file_path, job_id)

            if not text_content.strip():
                # Fallback to PyPDF2
                logger.warning(
                    "pdfplumber extraction failed, trying PyPDF2",
                    job_id=job_id
                )
                text_content = await self._extract_with_pypdf2(file_path, job_id)
                warnings.append("Used fallback PDF extraction method")

            if not text_content.strip():
                logger.error(
                    "Both PDF extraction methods failed",
                    job_id=job_id
                )
                warnings.append("PDF text extraction failed - document may be image-based")

            # Process extracted text
            extracted_data = await self._process_text_content(text_content, job_id)
            extracted_data['warnings'] = warnings

            # Normalize output
            result = self._normalize_output(extracted_data, job_id)

            logger.info(
                "PDF extraction completed",
                job_id=job_id,
                text_length=len(text_content),
                warnings=len(result.get('warnings', []))
            )

            return result

        except Exception as e:
            logger.error(
                "PDF extraction failed",
                job_id=job_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True
            )
            raise

    async def _extract_with_pdfplumber(self, file_path: Path, job_id: str) -> str:
        """Extract text using pdfplumber (preferred method)"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text_parts = []
                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                        else:
                            logger.warning(
                                "No text extracted from page",
                                job_id=job_id,
                                page_number=page_num
                            )
                    except Exception as page_error:
                        logger.warning(
                            "Failed to extract text from page",
                            job_id=job_id,
                            page_number=page_num,
                            error=str(page_error)
                        )

                return '\n\n'.join(text_parts)

        except Exception as e:
            logger.warning(
                "pdfplumber extraction failed",
                job_id=job_id,
                error=str(e)
            )
            return ""

    async def _extract_with_pypdf2(self, file_path: Path, job_id: str) -> str:
        """Extract text using PyPDF2 as fallback"""
        try:
            with open(file_path, 'rb') as file:
                reader = PdfReader(file)
                text_parts = []

                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text_parts.append(page_text)
                    except Exception as page_error:
                        logger.warning(
                            "PyPDF2 failed to extract from page",
                            job_id=job_id,
                            page_number=page_num,
                            error=str(page_error)
                        )

                return '\n\n'.join(text_parts)

        except Exception as e:
            logger.warning(
                "PyPDF2 extraction failed",
                job_id=job_id,
                error=str(e)
            )
            return ""

    async def _process_text_content(self, text: str, job_id: str) -> Dict[str, Any]:
        """Process extracted text content into structured data"""
        if not text.strip():
            return {
                'contact': {},
                'summary': '',
                'experience': [],
                'education': [],
                'skills': [],
                'projects': [],
                'achievements': [],
                'warnings': ["No text content extracted from PDF"]
            }

        # Clean and normalize text
        text = self._clean_text(text)

        # Split into lines for processing
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # Detect sections using simple heuristics
        sections = self._detect_sections_heuristic(lines, job_id)

        # Extract content
        extracted = {
            'contact': self._extract_contact_info(text),
            'summary': '',
            'experience': [],
            'education': [],
            'skills': [],
            'projects': [],
            'achievements': [],
            'warnings': []
        }

        # Process each detected section
        for section_name, line_indices in sections.items():
            section_lines = [lines[i] for i in line_indices]
            section_text = '\n'.join(section_lines)

            if section_name == 'summary':
                extracted['summary'] = self._extract_summary_heuristic(section_text)

            elif section_name == 'experience':
                extracted['experience'] = self._extract_experience_heuristic(section_text, job_id)

            elif section_name == 'education':
                extracted['education'] = self._extract_education_heuristic(section_text)

            elif section_name == 'skills':
                extracted['skills'] = self._extract_skills_heuristic(section_text)

            elif section_name == 'projects':
                extracted['projects'] = self._extract_projects_heuristic(section_text)

            elif section_name == 'achievements':
                extracted['achievements'] = self._extract_achievements_heuristic(section_text)

        # If no sections detected, try to extract from full text
        if not any(sections.values()):
            extracted['warnings'].append("No clear sections detected - using heuristic extraction")
            extracted = self._extract_from_full_text(text, extracted)

        return extracted

    def _clean_text(self, text: str) -> str:
        """Clean extracted PDF text"""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)

        # Remove page numbers and footers (basic heuristics)
        lines = text.split('\n')
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            # Skip likely page numbers
            if re.match(r'^\d+$', line):
                continue
            # Skip very short lines that might be artifacts
            if len(line) < 2:
                continue

            cleaned_lines.append(line)

        return '\n'.join(cleaned_lines)

    def _detect_sections_heuristic(self, lines: List[str], job_id: str) -> Dict[str, List[int]]:
        """Detect sections using simple pattern matching"""
        sections = {}
        current_section = None

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check for section headers
            detected_section = None
            for section_name, patterns in self.SECTION_PATTERNS.items():
                if any(re.search(pattern, line_lower) for pattern in patterns):
                    # Additional check: line should be relatively short to be a header
                    if len(line.split()) <= 5:
                        detected_section = section_name
                        break

            if detected_section:
                current_section = detected_section
                if current_section not in sections:
                    sections[current_section] = []
                logger.debug(
                    "PDF section detected",
                    job_id=job_id,
                    section=current_section,
                    line_index=i
                )
            elif current_section and i < len(lines) - 1:
                # Add content to current section
                sections[current_section].append(i)

        return sections

    def _extract_contact_info(self, text: str) -> Dict[str, Any]:
        """Extract contact information (same as DOCX extractor)"""
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
            contact['urls'] = urls[:3]

        return contact

    def _extract_summary_heuristic(self, text: str) -> str:
        """Extract summary with basic cleaning"""
        # Take first few sentences or paragraphs
        sentences = text.split('.')
        summary_parts = []

        for sentence in sentences[:5]:  # Max 5 sentences
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                summary_parts.append(sentence)

        return '. '.join(summary_parts)

    def _extract_experience_heuristic(self, text: str, job_id: str) -> List[Dict[str, Any]]:
        """Extract experience with basic heuristics"""
        experience = []

        # Split by paragraphs or potential job entries
        entries = re.split(r'\n\n+', text)

        for entry in entries:
            entry = entry.strip()
            if len(entry) < 20:  # Skip very short entries
                continue

            exp_item = self._parse_experience_entry_heuristic(entry)
            if exp_item:
                experience.append(exp_item)

        return experience[:10]  # Limit to 10 entries

    def _parse_experience_entry_heuristic(self, entry: str) -> Optional[Dict[str, Any]]:
        """Parse experience entry with heuristics"""
        lines = [line.strip() for line in entry.split('\n') if line.strip()]
        if not lines:
            return None

        exp = {
            'title': '',
            'company': '',
            'duration': '',
            'responsibilities': []
        }

        # First line often contains title/company
        first_line = lines[0]

        # Look for company indicators
        if any(word in first_line.lower() for word in ['inc', 'corp', 'ltd', 'llc', 'company']):
            exp['company'] = first_line
        else:
            exp['title'] = first_line

        # Look for dates
        for line in lines[:3]:
            date_match = re.search(r'\b\d{4}\b.*?\b\d{4}\b|\b\d{4}\b.*?present', line, re.IGNORECASE)
            if date_match:
                exp['duration'] = date_match.group().strip()
                break

        # Rest are responsibilities
        for line in lines[1:]:
            if line and not re.search(r'\b\d{4}\b', line):
                line = re.sub(r'^[\•\-\*\+]\s*', '', line)
                if line:
                    exp['responsibilities'].append(line)

        return exp if exp['title'] or exp['company'] else None

    def _extract_education_heuristic(self, text: str) -> List[Dict[str, Any]]:
        """Extract education with heuristics"""
        education = []

        # Look for degree keywords and university names
        lines = text.split('\n')
        current_edu = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for degree keywords
            degree_keywords = ['bachelor', 'master', 'phd', 'degree', 'b.s.', 'm.s.', 'b.a.', 'm.a.']
            institution_keywords = ['university', 'college', 'institute']

            has_degree = any(keyword in line.lower() for keyword in degree_keywords)
            has_institution = any(keyword in line.lower() for keyword in institution_keywords)

            if has_degree or has_institution:
                if current_edu:
                    education.append(current_edu)

                current_edu = {
                    'degree': line if has_degree else '',
                    'institution': line if has_institution else '',
                    'year': '',
                    'details': []
                }

                # Look for year in same line
                year_match = re.search(r'\b(19|20)\d{2}\b', line)
                if year_match:
                    current_edu['year'] = year_match.group()

            elif current_edu:
                # Add additional details
                current_edu['details'].append(line)

        if current_edu:
            education.append(current_edu)

        return education[:5]  # Limit to 5 entries

    def _extract_skills_heuristic(self, text: str) -> List[str]:
        """Extract skills with heuristics"""
        # Remove section header
        text = re.sub(r'^(skills?|technologies?):?\s*', '', text, flags=re.IGNORECASE | re.MULTILINE)

        # Split by various delimiters
        skills = re.split(r'[,;\n\|•\-\*\+]+', text)

        # Clean and filter
        cleaned_skills = []
        for skill in skills:
            skill = skill.strip()
            if skill and 2 <= len(skill) <= 50:  # Reasonable skill length
                cleaned_skills.append(skill)

        return cleaned_skills[:20]  # Limit to 20 skills

    def _extract_projects_heuristic(self, text: str) -> List[Dict[str, Any]]:
        """Extract projects with heuristics"""
        projects = []

        # Split by paragraphs
        entries = re.split(r'\n\n+', text)

        for entry in entries:
            entry = entry.strip()
            if len(entry) < 10:
                continue

            lines = [line.strip() for line in entry.split('\n') if line.strip()]
            if not lines:
                continue

            project = {
                'name': lines[0],
                'description': ' '.join(lines[1:]) if len(lines) > 1 else '',
                'technologies': [],
                'details': []
            }

            projects.append(project)

        return projects[:5]  # Limit to 5 projects

    def _extract_achievements_heuristic(self, text: str) -> List[str]:
        """Extract achievements with heuristics"""
        achievements = []

        # Split by bullet points or lines
        items = re.split(r'[\n•\-\*\+]+', text)

        for item in items:
            item = item.strip()
            if item and 5 <= len(item) <= 200:
                achievements.append(item)

        return achievements[:10]  # Limit to 10 achievements

    def _extract_from_full_text(self, text: str, extracted: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback: extract basic info from full text when no sections detected"""
        # Try to extract contact if not found
        if not extracted['contact']:
            extracted['contact'] = self._extract_contact_info(text)

        # Try to extract some skills based on common technology terms
        if not extracted['skills']:
            tech_terms = [
                'python', 'java', 'javascript', 'react', 'angular', 'vue',
                'sql', 'mysql', 'postgresql', 'mongodb', 'git', 'docker',
                'aws', 'azure', 'linux', 'windows', 'html', 'css'
            ]
            found_skills = []
            text_lower = text.lower()
            for term in tech_terms:
                if term in text_lower:
                    found_skills.append(term.title())

            extracted['skills'] = found_skills[:10]

        extracted['warnings'].append("Limited extraction due to unclear document structure")
        return extracted

    def _normalize_output(self, extracted: Dict[str, Any], job_id: str) -> Dict[str, Any]:
        """Normalize output format"""
        warnings = extracted.get('warnings', [])

        # Add additional warnings for PDF limitations
        if not extracted.get('contact', {}).get('email'):
            warnings.append("No email address detected (PDF parsing limitation)")

        result = {
            "extraction_method": "pdf_heuristic",
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
        """Calculate confidence score for PDF extraction (generally lower than DOCX)"""
        score = 0.0

        # Award points but with lower confidence than DOCX
        if extracted.get('contact', {}).get('email'):
            score += 0.15
        if extracted.get('summary'):
            score += 0.1
        if extracted.get('experience'):
            score += 0.2  # Lower confidence for PDF experience extraction
        if extracted.get('education'):
            score += 0.15
        if extracted.get('skills'):
            score += 0.1

        # PDF extraction is inherently less confident
        return min(score * 0.8, 0.8)  # Max 80% confidence for PDF