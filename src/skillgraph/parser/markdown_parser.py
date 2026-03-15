"""
Markdown Skill Parser

Parse Markdown-formatted Agent Skills into structured data.
"""

import re
import json
from dataclasses import dataclass, field, asdict
from typing import Optional
from pathlib import Path

import markdown
from markdown.extensions import fenced_code, tables


@dataclass
class Section:
    """Represents a section in the skill document."""
    id: str
    type: str  # instruction, code, reference
    title: str
    content: str
    level: int
    position: dict = field(default_factory=dict)
    language: Optional[str] = None  # for code blocks


@dataclass
class ParsedSkill:
    """Structured representation of a parsed skill."""
    name: str
    description: str = ""
    tags: list = field(default_factory=list)
    sections: list = field(default_factory=list)
    code_blocks: list = field(default_factory=list)
    links: list = field(default_factory=list)
    file_paths: list = field(default_factory=list)
    urls: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


class SkillParser:
    """
    Parse Markdown skill files into structured data.

    Features:
    - Frontmatter extraction (YAML)
    - Section hierarchy parsing
    - Code block identification
    - Link and file path extraction
    """

    # Patterns for extraction
    CODE_BLOCK_PATTERN = re.compile(r'```(\w+)?\n(.*?)```', re.DOTALL)
    LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    FILE_PATH_PATTERN = re.compile(r'["\']?([./~][\w/.-]+)["\']?')
    URL_PATTERN = re.compile(r'https?://[^\s\)]+')
    FRONTMATTER_PATTERN = re.compile(r'^---\n(.*?)\n---', re.DOTALL)

    def __init__(self):
        self.md = markdown.Markdown(extensions=['fenced_code', 'tables', 'meta'])

    def parse(self, content: str) -> ParsedSkill:
        """
        Parse skill content string.

        Args:
            content: Raw Markdown content of the skill

        Returns:
            ParsedSkill object with structured data
        """
        # Extract frontmatter
        metadata = self._extract_frontmatter(content)

        # Remove frontmatter for further parsing
        clean_content = self.FRONTMATTER_PATTERN.sub('', content).strip()

        # Extract sections
        sections = self._extract_sections(clean_content)

        # Extract code blocks
        code_blocks = self._extract_code_blocks(clean_content)

        # Extract links, paths, URLs
        links = self._extract_links(clean_content)
        file_paths = self._extract_file_paths(clean_content)
        urls = self._extract_urls(clean_content)

        # Determine skill name
        name = metadata.get('name', self._extract_title(clean_content) or 'unnamed')

        return ParsedSkill(
            name=name,
            description=metadata.get('description', ''),
            tags=metadata.get('tags', []),
            sections=sections,
            code_blocks=code_blocks,
            links=links,
            file_paths=file_paths,
            urls=urls,
            metadata=metadata
        )

    def parse_file(self, file_path: str) -> ParsedSkill:
        """
        Parse skill from file.

        Args:
            file_path: Path to the skill Markdown file

        Returns:
            ParsedSkill object
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Skill file not found: {file_path}")

        content = path.read_text(encoding='utf-8')
        skill = self.parse(content)
        skill.metadata['source_file'] = str(path)
        return skill

    def _extract_frontmatter(self, content: str) -> dict:
        """Extract YAML frontmatter."""
        match = self.FRONTMATTER_PATTERN.match(content)
        if not match:
            return {}

        try:
            import yaml
            return yaml.safe_load(match.group(1)) or {}
        except ImportError:
            # Fallback: simple key-value parsing
            result = {}
            for line in match.group(1).split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    result[key.strip()] = value.strip()
            return result

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from first H1 heading."""
        for line in content.split('\n'):
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def _extract_sections(self, content: str) -> list:
        """Extract sections based on headings."""
        sections = []
        lines = content.split('\n')
        current_section = None
        section_id = 0

        for i, line in enumerate(lines):
            if line.startswith('#'):
                # Save previous section
                if current_section:
                    sections.append(current_section)

                # Parse heading level
                level = len(line) - len(line.lstrip('#'))
                title = line.lstrip('#').strip()

                section_id += 1
                current_section = {
                    'id': f'sec_{section_id:03d}',
                    'type': 'instruction',
                    'level': level,
                    'title': title,
                    'content': '',
                    'position': {'start': i}
                }
            elif current_section:
                current_section['content'] += line + '\n'

        # Add last section
        if current_section:
            sections.append(current_section)

        return sections

    def _extract_code_blocks(self, content: str) -> list:
        """Extract code blocks with language info."""
        blocks = []
        for i, match in enumerate(self.CODE_BLOCK_PATTERN.finditer(content)):
            language = match.group(1) or 'unknown'
            code = match.group(2)
            blocks.append({
                'id': f'code_{i:03d}',
                'language': language,
                'content': code,
                'position': {'start': match.start(), 'end': match.end()}
            })
        return blocks

    def _extract_links(self, content: str) -> list:
        """Extract markdown links."""
        return [
            {'text': text, 'url': url}
            for text, url in self.LINK_PATTERN.findall(content)
        ]

    def _extract_file_paths(self, content: str) -> list:
        """Extract file paths."""
        return list(set(self.FILE_PATH_PATTERN.findall(content)))

    def _extract_urls(self, content: str) -> list:
        """Extract URLs."""
        return list(set(self.URL_PATTERN.findall(content)))
