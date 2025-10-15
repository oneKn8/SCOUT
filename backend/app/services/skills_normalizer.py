"""
Skills Normalization Service with Alias Mapping
Provides canonical naming and categorization for extracted skills
"""

from typing import Dict, List, Optional, Set, Tuple
import re
import structlog
from app.models.profile_schema import SkillCategoryEnum, SkillEntrySchema

logger = structlog.get_logger()


class SkillsNormalizer:
    """
    Service for normalizing and categorizing skills extracted from resumes
    Maintains an alias map for common skill variations
    """

    # Core alias map for skill normalization
    SKILL_ALIASES = {
        # Programming Languages
        'python': {
            'canonical': 'Python',
            'aliases': ['python3', 'py', 'python 3', 'python3.x'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'javascript': {
            'canonical': 'JavaScript',
            'aliases': ['js', 'java script', 'javascript es6', 'es6', 'node.js backend'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'typescript': {
            'canonical': 'TypeScript',
            'aliases': ['ts', 'type script'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'java': {
            'canonical': 'Java',
            'aliases': ['java 8', 'java 11', 'java 17', 'jdk'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'csharp': {
            'canonical': 'C#',
            'aliases': ['c sharp', 'c#', '.net', 'dotnet'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'cplusplus': {
            'canonical': 'C++',
            'aliases': ['c++', 'cpp', 'c plus plus'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'go': {
            'canonical': 'Go',
            'aliases': ['golang', 'go lang'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'rust': {
            'canonical': 'Rust',
            'aliases': ['rust lang'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'php': {
            'canonical': 'PHP',
            'aliases': ['php7', 'php8'],
            'category': SkillCategoryEnum.PROGRAMMING
        },
        'ruby': {
            'canonical': 'Ruby',
            'aliases': ['ruby on rails'],
            'category': SkillCategoryEnum.PROGRAMMING
        },

        # Web Frameworks
        'react': {
            'canonical': 'React',
            'aliases': ['reactjs', 'react.js', 'react js'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'angular': {
            'canonical': 'Angular',
            'aliases': ['angularjs', 'angular js', 'angular 2+'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'vue': {
            'canonical': 'Vue.js',
            'aliases': ['vuejs', 'vue js', 'vue'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'nextjs': {
            'canonical': 'Next.js',
            'aliases': ['next', 'nextjs', 'next js'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'django': {
            'canonical': 'Django',
            'aliases': ['django rest framework', 'drf'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'flask': {
            'canonical': 'Flask',
            'aliases': [],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'fastapi': {
            'canonical': 'FastAPI',
            'aliases': ['fast api'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'express': {
            'canonical': 'Express.js',
            'aliases': ['expressjs', 'express js'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },
        'spring': {
            'canonical': 'Spring Framework',
            'aliases': ['spring boot', 'spring mvc'],
            'category': SkillCategoryEnum.FRAMEWORKS
        },

        # Databases
        'postgresql': {
            'canonical': 'PostgreSQL',
            'aliases': ['postgres', 'psql', 'pg'],
            'category': SkillCategoryEnum.DATABASES
        },
        'mysql': {
            'canonical': 'MySQL',
            'aliases': ['my sql'],
            'category': SkillCategoryEnum.DATABASES
        },
        'mongodb': {
            'canonical': 'MongoDB',
            'aliases': ['mongo db', 'mongo'],
            'category': SkillCategoryEnum.DATABASES
        },
        'redis': {
            'canonical': 'Redis',
            'aliases': [],
            'category': SkillCategoryEnum.DATABASES
        },
        'sqlite': {
            'canonical': 'SQLite',
            'aliases': ['sql lite'],
            'category': SkillCategoryEnum.DATABASES
        },
        'sql': {
            'canonical': 'SQL',
            'aliases': ['structured query language'],
            'category': SkillCategoryEnum.DATABASES
        },

        # Cloud Platforms
        'aws': {
            'canonical': 'Amazon Web Services',
            'aliases': ['amazon web services', 'aws cloud'],
            'category': SkillCategoryEnum.CLOUD
        },
        'azure': {
            'canonical': 'Microsoft Azure',
            'aliases': ['azure cloud', 'ms azure'],
            'category': SkillCategoryEnum.CLOUD
        },
        'gcp': {
            'canonical': 'Google Cloud Platform',
            'aliases': ['google cloud', 'google cloud platform', 'gcloud'],
            'category': SkillCategoryEnum.CLOUD
        },
        'docker': {
            'canonical': 'Docker',
            'aliases': ['containerization'],
            'category': SkillCategoryEnum.TOOLS
        },
        'kubernetes': {
            'canonical': 'Kubernetes',
            'aliases': ['k8s', 'kube'],
            'category': SkillCategoryEnum.CLOUD
        },

        # Development Tools
        'git': {
            'canonical': 'Git',
            'aliases': ['version control', 'git version control'],
            'category': SkillCategoryEnum.TOOLS
        },
        'github': {
            'canonical': 'GitHub',
            'aliases': ['git hub'],
            'category': SkillCategoryEnum.TOOLS
        },
        'gitlab': {
            'canonical': 'GitLab',
            'aliases': ['git lab'],
            'category': SkillCategoryEnum.TOOLS
        },
        'jenkins': {
            'canonical': 'Jenkins',
            'aliases': ['ci/cd'],
            'category': SkillCategoryEnum.TOOLS
        },
        'jira': {
            'canonical': 'Jira',
            'aliases': ['atlassian jira'],
            'category': SkillCategoryEnum.TOOLS
        },

        # Machine Learning / AI
        'tensorflow': {
            'canonical': 'TensorFlow',
            'aliases': ['tensor flow', 'tf'],
            'category': SkillCategoryEnum.TECHNICAL
        },
        'pytorch': {
            'canonical': 'PyTorch',
            'aliases': ['torch'],
            'category': SkillCategoryEnum.TECHNICAL
        },
        'pandas': {
            'canonical': 'Pandas',
            'aliases': [],
            'category': SkillCategoryEnum.TECHNICAL
        },
        'numpy': {
            'canonical': 'NumPy',
            'aliases': ['num py'],
            'category': SkillCategoryEnum.TECHNICAL
        },
        'scikitlearn': {
            'canonical': 'Scikit-learn',
            'aliases': ['sklearn', 'scikit learn'],
            'category': SkillCategoryEnum.TECHNICAL
        },

        # Operating Systems
        'linux': {
            'canonical': 'Linux',
            'aliases': ['unix', 'ubuntu', 'centos', 'red hat'],
            'category': SkillCategoryEnum.TECHNICAL
        },
        'windows': {
            'canonical': 'Windows',
            'aliases': ['microsoft windows', 'windows server'],
            'category': SkillCategoryEnum.TECHNICAL
        },
        'macos': {
            'canonical': 'macOS',
            'aliases': ['mac os', 'osx', 'os x'],
            'category': SkillCategoryEnum.TECHNICAL
        },

        # Soft Skills (common ones)
        'leadership': {
            'canonical': 'Leadership',
            'aliases': ['team leadership', 'leading teams'],
            'category': SkillCategoryEnum.SOFT_SKILLS
        },
        'communication': {
            'canonical': 'Communication',
            'aliases': ['verbal communication', 'written communication'],
            'category': SkillCategoryEnum.SOFT_SKILLS
        },
        'project_management': {
            'canonical': 'Project Management',
            'aliases': ['project mgmt', 'pm'],
            'category': SkillCategoryEnum.SOFT_SKILLS
        },
        'problem_solving': {
            'canonical': 'Problem Solving',
            'aliases': ['problem-solving', 'troubleshooting'],
            'category': SkillCategoryEnum.SOFT_SKILLS
        }
    }

    def __init__(self):
        """Initialize the normalizer with precomputed lookup tables"""
        self._alias_to_canonical = {}
        self._canonical_to_info = {}

        # Build reverse lookup maps
        self._build_lookup_tables()

    def _build_lookup_tables(self) -> None:
        """Build optimized lookup tables from the alias map"""
        for skill_key, skill_info in self.SKILL_ALIASES.items():
            canonical = skill_info['canonical']

            # Map canonical name (case-insensitive)
            self._alias_to_canonical[canonical.lower()] = skill_info
            self._canonical_to_info[canonical.lower()] = skill_info

            # Map all aliases
            for alias in skill_info['aliases']:
                self._alias_to_canonical[alias.lower()] = skill_info

    def normalize_skill(self, raw_skill: str, context: str = '') -> SkillEntrySchema:
        """
        Normalize a single skill string into a structured skill entry

        Args:
            raw_skill: Raw skill name as extracted
            context: Context where skill was found (for confidence scoring)

        Returns:
            SkillEntrySchema with normalized information
        """
        cleaned_skill = self._clean_skill_name(raw_skill)

        # Look up in alias map
        skill_info = self._alias_to_canonical.get(cleaned_skill.lower())

        if skill_info:
            return SkillEntrySchema(
                name=raw_skill.strip(),
                canonical_name=skill_info['canonical'],
                aliases=skill_info['aliases'],
                category=skill_info['category'],
                context=context[:500] if context else None,
                confidence_score=0.95  # High confidence for known skills
            )
        else:
            # Unknown skill - try to infer category
            inferred_category = self._infer_skill_category(cleaned_skill)

            return SkillEntrySchema(
                name=raw_skill.strip(),
                canonical_name=cleaned_skill.title(),
                aliases=[],
                category=inferred_category,
                context=context[:500] if context else None,
                confidence_score=0.7  # Lower confidence for unknown skills
            )

    def normalize_skills_list(self, raw_skills: List[str], context: str = '') -> List[SkillEntrySchema]:
        """
        Normalize a list of skills and deduplicate

        Args:
            raw_skills: List of raw skill names
            context: Context where skills were found

        Returns:
            List of normalized, deduplicated skill entries
        """
        if not raw_skills:
            return []

        normalized_skills = []
        seen_canonical = set()

        for raw_skill in raw_skills:
            if not raw_skill or not raw_skill.strip():
                continue

            normalized = self.normalize_skill(raw_skill, context)

            # Deduplicate by canonical name
            canonical_key = normalized.canonical_name.lower()
            if canonical_key not in seen_canonical:
                seen_canonical.add(canonical_key)
                normalized_skills.append(normalized)

        # Sort by category and then by canonical name
        normalized_skills.sort(key=lambda s: (s.category.value if s.category else 'z_other', s.canonical_name))

        return normalized_skills

    def _clean_skill_name(self, skill: str) -> str:
        """Clean and normalize skill name string"""
        if not skill:
            return ''

        # Remove extra whitespace
        skill = re.sub(r'\s+', ' ', skill.strip())

        # Remove common prefixes/suffixes
        skill = re.sub(r'^(proficient in|experience with|knowledge of)\s+', '', skill, flags=re.IGNORECASE)
        skill = re.sub(r'\s+(programming|development|framework|library|database)$', '', skill, flags=re.IGNORECASE)

        # Remove version numbers for cleaner matching
        skill = re.sub(r'\s+\d+(\.\d+)*$', '', skill)

        # Remove parenthetical information
        skill = re.sub(r'\s*\([^)]*\)\s*', ' ', skill)

        # Clean up punctuation
        skill = re.sub(r'[.,;:!?]', '', skill)
        skill = re.sub(r'\s+', ' ', skill.strip())

        return skill

    def _infer_skill_category(self, skill: str) -> Optional[SkillCategoryEnum]:
        """
        Infer skill category based on patterns and keywords

        Args:
            skill: Cleaned skill name

        Returns:
            Inferred category or None
        """
        skill_lower = skill.lower()

        # Programming languages patterns
        prog_patterns = [
            r'\b(lang|language)$',
            r'^(c|r|matlab|scala|kotlin|swift|perl|shell)$',
            r'script$'
        ]
        if any(re.search(pattern, skill_lower) for pattern in prog_patterns):
            return SkillCategoryEnum.PROGRAMMING

        # Framework patterns
        framework_patterns = [
            r'(framework|js|\.js)$',
            r'^(spring|hibernate|laravel|rails|ember|backbone)$'
        ]
        if any(re.search(pattern, skill_lower) for pattern in framework_patterns):
            return SkillCategoryEnum.FRAMEWORKS

        # Database patterns
        db_patterns = [
            r'(db|database|sql|nosql)$',
            r'^(oracle|cassandra|neo4j|influx|elastic)$'
        ]
        if any(re.search(pattern, skill_lower) for pattern in db_patterns):
            return SkillCategoryEnum.DATABASES

        # Cloud patterns
        cloud_patterns = [
            r'(cloud|aws|azure|gcp)$',
            r'^(serverless|lambda|functions)$'
        ]
        if any(re.search(pattern, skill_lower) for pattern in cloud_patterns):
            return SkillCategoryEnum.CLOUD

        # Tool patterns
        tool_patterns = [
            r'^(ide|editor|vim|vscode|intellij|eclipse)$',
            r'(testing|test|ci|cd|devops)$'
        ]
        if any(re.search(pattern, skill_lower) for pattern in tool_patterns):
            return SkillCategoryEnum.TOOLS

        # Soft skills patterns
        soft_skill_patterns = [
            r'^(teamwork|collaboration|analytical|creative)$',
            r'(management|planning|organization)$'
        ]
        if any(re.search(pattern, skill_lower) for pattern in soft_skill_patterns):
            return SkillCategoryEnum.SOFT_SKILLS

        # Certification patterns
        cert_patterns = [
            r'(certified|certification|cert)$',
            r'^(pmp|cissp|cism|aws|azure|google).*cert'
        ]
        if any(re.search(pattern, skill_lower) for pattern in cert_patterns):
            return SkillCategoryEnum.CERTIFICATIONS

        # Default to technical if it contains technical terms
        if any(word in skill_lower for word in ['api', 'rest', 'http', 'json', 'xml', 'web', 'mobile', 'algorithm']):
            return SkillCategoryEnum.TECHNICAL

        return SkillCategoryEnum.OTHER

    def get_skill_suggestions(self, partial_skill: str, limit: int = 10) -> List[str]:
        """
        Get skill suggestions based on partial input

        Args:
            partial_skill: Partial skill name
            limit: Maximum number of suggestions

        Returns:
            List of suggested canonical skill names
        """
        if not partial_skill or len(partial_skill) < 2:
            return []

        partial_lower = partial_skill.lower()
        suggestions = []

        # Check canonical names and aliases
        for alias, skill_info in self._alias_to_canonical.items():
            if partial_lower in alias:
                canonical = skill_info['canonical']
                if canonical not in suggestions:
                    suggestions.append(canonical)

        # Sort by relevance (starts with match first, then contains)
        starts_with = [s for s in suggestions if s.lower().startswith(partial_lower)]
        contains = [s for s in suggestions if s not in starts_with]

        return (starts_with + contains)[:limit]

    def get_category_stats(self, skills: List[SkillEntrySchema]) -> Dict[str, int]:
        """
        Get statistics about skill categories

        Args:
            skills: List of normalized skills

        Returns:
            Dictionary with category counts
        """
        stats = {}
        for skill in skills:
            category = skill.category.value if skill.category else 'uncategorized'
            stats[category] = stats.get(category, 0) + 1

        return stats

    def add_custom_alias(self, canonical_name: str, alias: str, category: SkillCategoryEnum = SkillCategoryEnum.OTHER) -> None:
        """
        Add a custom skill alias at runtime

        Args:
            canonical_name: Canonical skill name
            alias: Alias to add
            category: Skill category
        """
        canonical_lower = canonical_name.lower()

        # Update or create skill info
        if canonical_lower in self._canonical_to_info:
            skill_info = self._canonical_to_info[canonical_lower]
            if alias.lower() not in [a.lower() for a in skill_info['aliases']]:
                skill_info['aliases'].append(alias)
        else:
            skill_info = {
                'canonical': canonical_name,
                'aliases': [alias],
                'category': category
            }
            self._canonical_to_info[canonical_lower] = skill_info

        # Update alias lookup
        self._alias_to_canonical[alias.lower()] = skill_info

        logger.info(
            "Custom skill alias added",
            canonical=canonical_name,
            alias=alias,
            category=category.value
        )