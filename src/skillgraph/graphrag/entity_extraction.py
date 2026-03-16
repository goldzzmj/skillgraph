"""
Entity Extraction Module

Extract entities from skill content using LLM-based extraction.
"""

import re
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict
from pathlib import Path

from .models import Entity, EntityType


class EntityExtractor:
    """
    Extract entities from skill content using LLM.

    Supports two extraction modes:
    1. Pattern-based extraction (fast, no LLM required)
    2. LLM-based extraction (accurate, requires API key)
    """

    # Pattern-based entity patterns (fallback when LLM unavailable)
    ENTITY_PATTERNS = {
        EntityType.TOOL: [
            r'\b(exec|execute|run|launch|invoke|call)\s+([a-zA-Z_][\w./-]*)',
            r'`(?:bash|cmd|sh|powershell)\s+([a-zA-Z_][\w./-]*)`',
            r'(?:tool|command|utility):\s*`?([a-zA-Z_][\w./-]*)',
        ],
        EntityType.API: [
            r'\b(GET|POST|PUT|DELETE|PATCH)\s+([/][^\s)]+)',
            r'\b([a-zA-Z_][\w-]*)\.(?:get|post|put|delete|patch)\(',
            r'api[_-]?call:\s*`?([a-zA-Z_][\w-]*)',
        ],
        EntityType.FILE: [
            r'["\']([~./][\w/\\.\-]+)["\']',
            r'(?:file|path):\s*["\']?([~./][\w/\\.\-]+)["\']?',
            r'\b(read|write|open|load|save)\s*\(\s*["\']([^"\']+)["\']',
        ],
        EntityType.NETWORK: [
            r'https?://[^\s\)]+',
            r'(?:url|endpoint|host):\s*["\']?([a-zA-Z0-9\-\.]+)',
            r'(?:connect|request|fetch)\s+\(?["\']?([a-zA-Z0-9\-\.]+)',
        ],
        EntityType.PERMISSION: [
            r'(?:permission|privilege|access):\s*["\']?([\w\s]+)["\']?',
            r'(?:allow|permit|grant):\s*["\']?([\w\s]+)["\']?',
            r'\b(root|sudo|admin|administrator)\b',
        ],
        EntityType.CONFIG: [
            r'(?:config|setting|option):\s*["\']?([\w-]+)["\']?',
            r'(?:variable|param|parameter):\s*["\']?([\w-]+)["\']?',
            r'(?:ENV|environment):\s*["\']?([\w-]+)["\']?',
        ],
    }

    NOISE_TOKENS = {
        "run",
        "exec",
        "execute",
        "call",
        "invoke",
        "tool",
        "command",
        "utility",
        "file",
        "path",
        "url",
        "endpoint",
    }

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize entity extractor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.use_llm = self.config.get('entity_extraction', {}).get('enabled', True)
        self.chunk_size = self.config.get('entity_extraction', {}).get('chunk_size', 2000)
        self.chunk_overlap = self.config.get('entity_extraction', {}).get('chunk_overlap', 200)
        self.min_confidence = self.config.get('entity_extraction', {}).get('min_confidence', 0.5)

    def extract(
        self,
        content: str,
        sections: List[Dict[str, Any]] = None,
        code_blocks: List[Dict[str, Any]] = None
    ) -> List[Entity]:
        """
        Extract entities from skill content.

        Args:
            content: Full skill content
            sections: Parsed sections
            code_blocks: Parsed code blocks

        Returns:
            List of extracted Entity objects
        """
        entities = []
        entity_id = 0

        # Extract from sections
        if sections:
            for section in sections:
                section_entities = self._extract_from_text(
                    section.get('content', ''),
                    section_id=section.get('id', ''),
                    position=section.get('position', {})
                )
                entities.extend(section_entities)

        # Extract from code blocks
        if code_blocks:
            for block in code_blocks:
                code_entities = self._extract_from_text(
                    block.get('content', ''),
                    section_id=f"code_{block.get('id', '')}",
                    position=block.get('position', {}),
                    is_code=True,
                    language=block.get('language', 'unknown')
                )
                entities.extend(code_entities)

        # Deduplicate entities
        entities = self._deduplicate_entities(entities)

        # Assign sequential IDs
        for i, entity in enumerate(entities):
            entity.id = f"entity_{i:03d}"

        return entities

    def _extract_from_text(
        self,
        text: str,
        section_id: str = "",
        position: Dict[str, int] = None,
        is_code: bool = False,
        language: str = "unknown"
    ) -> List[Entity]:
        """
        Extract entities from a text segment.

        Args:
            text: Text to extract from
            section_id: Source section ID
            position: Position in document
            is_code: Whether this is code content
            language: Programming language (for code blocks)

        Returns:
            List of extracted Entity objects
        """
        entities = []

        if self.use_llm:
            # Try LLM-based extraction
            try:
                entities = self._extract_with_llm(text, section_id, is_code, language)
            except Exception as e:
                # Fallback to pattern-based extraction
                entities = self._extract_with_patterns(text, section_id, position, is_code, language)
        else:
            # Pattern-based extraction only
            entities = self._extract_with_patterns(text, section_id, position, is_code, language)

        return entities

    def _extract_with_patterns(
        self,
        text: str,
        section_id: str = "",
        position: Dict[str, int] = None,
        is_code: bool = False,
        language: str = "unknown"
    ) -> List[Entity]:
        """
        Extract entities using regex patterns (fallback method).

        Args:
            text: Text to extract from
            section_id: Source section ID
            position: Position in document
            is_code: Whether this is code content
            language: Programming language

        Returns:
            List of extracted Entity objects
        """
        entities = []

        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)

                for match in matches:
                    name = self._select_match_name(match)
                    name = self._clean_entity_name(name)

                    # Skip empty or very short names
                    if not name or len(name) < 2:
                        continue

                    if name.lower() in self.NOISE_TOKENS:
                        continue

                    # Create entity
                    entity = Entity(
                        id="",  # Will be assigned later
                        name=name.strip(),
                        type=entity_type,
                        description=self._generate_description(name, entity_type, is_code, language),
                        properties={
                            'is_code': is_code,
                            'language': language,
                            'matched_pattern': pattern
                        },
                        risk_score=self._infer_entity_risk_score(name, entity_type),
                        confidence=0.7,  # Pattern-based extraction has lower confidence
                        source_section=section_id,
                        position=position or {}
                    )

                    entities.append(entity)

        return entities

    def _select_match_name(self, match: re.Match) -> str:
        """Select the most meaningful token from regex groups."""
        groups = [g for g in match.groups() if isinstance(g, str) and g.strip()]
        if not groups:
            return match.group(0)

        # Prefer longer groups (usually actual entity name instead of action verb).
        groups.sort(key=lambda token: len(token.strip()), reverse=True)
        return groups[0]

    def _clean_entity_name(self, name: str) -> str:
        """Normalize extracted entity names for readability and dedup."""
        cleaned = name.strip().strip("`\"'()[]{}<>.,;:")
        cleaned = cleaned.replace("\\\\", "/")
        return cleaned

    def _infer_entity_risk_score(self, name: str, entity_type: EntityType) -> float:
        """Infer initial risk score from entity text and type."""
        lowered = name.lower()

        high_keywords = (".env", ".ssh", ".pem", "password", "token", "secret", "sudo", "rm -rf", "eval", "exec(")
        medium_keywords = ("http://", "https://", "curl", "wget", "admin", "credential", "upload", "download")

        if any(keyword in lowered for keyword in high_keywords):
            return 0.85
        if any(keyword in lowered for keyword in medium_keywords):
            return 0.55
        if entity_type in (EntityType.NETWORK, EntityType.PERMISSION):
            return 0.35
        return 0.1

    def _extract_with_llm(
        self,
        text: str,
        section_id: str = "",
        is_code: bool = False,
        language: str = "unknown"
    ) -> List[Entity]:
        """
        Extract entities using LLM (primary method).

        Args:
            text: Text to extract from
            section_id: Source section ID
            is_code: Whether this is code content
            language: Programming language

        Returns:
            List of extracted Entity objects
        """
        # This is a placeholder for LLM-based extraction
        # In a real implementation, this would call the LLM API
        # For now, fall back to pattern-based extraction

        return self._extract_with_patterns(text, section_id, {}, is_code, language)

    def _generate_description(
        self,
        name: str,
        entity_type: EntityType,
        is_code: bool = False,
        language: str = "unknown"
    ) -> str:
        """
        Generate a description for an entity.

        Args:
            name: Entity name
            entity_type: Entity type
            is_code: Whether from code block
            language: Programming language

        Returns:
            Entity description
        """
        descriptions = {
            EntityType.TOOL: f"External tool or command: {name}",
            EntityType.API: f"API endpoint or function: {name}",
            EntityType.FILE: f"File or directory path: {name}",
            EntityType.VARIABLE: f"Variable or configuration item: {name}",
            EntityType.CONFIG: f"Configuration setting: {name}",
            EntityType.PERMISSION: f"Permission or access right: {name}",
            EntityType.NETWORK: f"Network resource or URL: {name}",
            EntityType.CODE: f"Code block or function: {name}",
            EntityType.INSTRUCTION: f"Instruction or directive: {name}"
        }

        base_desc = descriptions.get(entity_type, f"Entity: {name}")

        if is_code:
            base_desc += f" (language: {language})"

        return base_desc

    def _deduplicate_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Deduplicate entities based on name and type.

        Args:
            entities: List of entities to deduplicate

        Returns:
            Deduplicated list of entities
        """
        seen = set()
        unique_entities = []

        for entity in entities:
            key = (entity.name.lower(), entity.type)

            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
            else:
                # Update existing entity with higher confidence
                for existing in unique_entities:
                    if (existing.name.lower() == entity.name.lower() and
                        existing.type == entity.type):
                        if entity.confidence > existing.confidence:
                            existing.confidence = entity.confidence
                            existing.description = entity.description
                        break

        return unique_entities

    def extract_relationships(
        self,
        entities: List[Entity],
        content: str,
        sections: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships between entities.

        Args:
            entities: Extracted entities
            content: Full skill content
            sections: Parsed sections

        Returns:
            List of relationship dictionaries
        """
        from .models import Relationship, RelationType

        relationships = []

        # Pattern-based relationship extraction
        relationship_patterns = [
            (RelationType.CALLS, r'({0})\s*\.\s*(?:get|post|put|delete|call|invoke)'),
            (RelationType.DEPENDS_ON, r'(?:requires|depends on|needs)\s+({0})'),
            (RelationType.ACCESSES, r'(?:access|read|open)\s+({0})'),
            (RelationType.MODIFIES, r'(?:modify|write|update|change)\s+({0})'),
            (RelationType.VALIDATES, r'(?:validate|verify|check)\s+({0})'),
        ]

        # Create entity name lookup
        entity_names = {e.name.lower(): e.id for e in entities if len(e.name) > 3}

        for rel_type, pattern_template in relationship_patterns:
            # Build pattern with entity names
            entity_pattern = '|'.join(re.escape(name) for name in entity_names.keys())
            pattern = pattern_template.format(entity_pattern)

            matches = re.finditer(pattern, content, re.IGNORECASE)

            for match in matches:
                for group in match.groups():
                    if group and group.lower() in entity_names:
                        # Find source entity (context before match)
                        before_text = content[max(0, match.start()-50):match.start()]
                        for source_name, source_id in entity_names.items():
                            if source_name in before_text.lower():
                                relationships.append({
                                    'source_id': source_id,
                                    'target_id': entity_names[group.lower()],
                                    'type': rel_type.value,
                                    'confidence': 0.6
                                })
                                break

        return relationships
