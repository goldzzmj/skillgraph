"""
LLM Enhanced Entity Extraction Module

Uses GPT-4 to enhance entity extraction with higher accuracy and better context understanding.
"""

import os
import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("Warning: OpenAI library not installed. Install with: pip install openai")

from .models import Entity, EntityType, Relationship, RelationType
from .entity_extraction import EntityExtractor


class LLMEnhancedEntityExtractor:
    """
    LLM-enhanced entity extraction using GPT-4.

    Features:
    - Higher accuracy through LLM understanding
    - Better context awareness
    - Entity disambiguation
    - Entity linking to external knowledge bases
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize LLM-enhanced entity extractor.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.base_extractor = EntityExtractor(config)

        # OpenAI configuration
        self.api_key = self.config.get('model', {}).get('api_key') or os.getenv('OPENAI_API_KEY')
        self.model_name = self.config.get('model', {}).get('model_name', 'gpt-4-turbo-preview')
        self.temperature = self.config.get('model', {}).get('temperature', 0.0)

        # Enable LLM enhancement?
        self.enabled = self.config.get('llm_extraction', {}).get('enabled', True)

        # Initialize OpenAI client
        if OPENAI_AVAILABLE and self.api_key and self.enabled:
            self.client = OpenAI(api_key=self.api_key)
        else:
            self.client = None
            if self.enabled:
                print("Warning: LLM enhancement enabled but OpenAI not available")

        # Entity linking configuration
        self.enable_linking = self.config.get('llm_extraction', {}).get('enable_linking', False)
        self.knowledge_base_path = self.config.get('llm_extraction', {}).get('knowledge_base_path')

    def extract(
        self,
        content: str,
        sections: List[Any],
        code_blocks: List[Any]
    ) -> List[Entity]:
        """
        Extract entities with LLM enhancement.

        Args:
            content: Full text content
            sections: List of sections
            code_blocks: List of code blocks

        Returns:
            List of extracted entities
        """
        if not self.enabled or not self.client:
            # Fall back to base extractor
            print("Using base entity extractor (LLM disabled or unavailable)")
            return self.base_extractor.extract(content, sections, code_blocks)

        print("Using LLM-enhanced entity extraction")

        # Step 1: Extract with base method
        base_entities = self.base_extractor.extract(content, sections, code_blocks)

        # Step 2: Enhance with LLM
        enhanced_entities = self._enhance_with_llm(
            base_entities,
            content,
            sections,
            code_blocks
        )

        # Step 3: Disambiguate entities
        if self.enable_linking:
            disambiguated = self._disambiguate_entities(enhanced_entities, content)
        else:
            disambiguated = enhanced_entities

        # Step 4: Link to knowledge base
        if self.enable_linking and self.knowledge_base_path:
            linked = self._link_to_knowledge_base(disambiguated)
        else:
            linked = disambiguated

        print(f"Base extraction: {len(base_entities)} entities")
        print(f"Enhanced extraction: {len(enhanced_entities)} entities")
        print(f"Final extraction: {len(linked)} entities")

        return linked

    def _enhance_with_llm(
        self,
        entities: List[Entity],
        content: str,
        sections: List[Any],
        code_blocks: List[Any]
    ) -> List[Entity]:
        """
        Enhance entities using LLM.

        Args:
            entities: Base extracted entities
            content: Full text content
            sections: List of sections
            code_blocks: List of code blocks

        Returns:
            Enhanced list of entities
        """
        # Prepare context
        context = self._prepare_extraction_context(content, sections, code_blocks)

        # Prepare entities for LLM
        entities_json = self._entities_to_json(entities)

        # Create prompt
        prompt = self._create_enhancement_prompt(entities_json, context)

        try:
            # Call GPT-4
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing AI agent skills and security risks. Extract and enhance entities from the provided code and documentation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=2000
            )

            # Parse response
            enhanced_entities = self._parse_llm_response(response.choices[0].message.content)

            return enhanced_entities

        except Exception as e:
            print(f"Error in LLM enhancement: {e}")
            # Fall back to base entities
            return entities

    def _prepare_extraction_context(
        self,
        content: str,
        sections: List[Any],
        code_blocks: List[Any]
    ) -> str:
        """
        Prepare context for LLM extraction.

        Args:
            content: Full text content
            sections: List of sections
            code_blocks: List of code blocks

        Returns:
            Context string
        """
        context_parts = []

        # Add sections
        for i, section in enumerate(sections[:5], 1):
            section_text = getattr(section, 'content', str(section))
            context_parts.append(f"Section {i}: {section_text[:500]}")

        # Add code blocks
        for i, code_block in enumerate(code_blocks[:3], 1):
            code_text = getattr(code_block, 'code', str(code_block))
            context_parts.append(f"Code Block {i}: {code_text[:300]}")

        return "\n\n".join(context_parts)

    def _create_enhancement_prompt(
        self,
        entities_json: str,
        context: str
    ) -> str:
        """
        Create prompt for LLM entity enhancement.

        Args:
            entities_json: JSON string of base entities
            context: Context string

        Returns:
            Prompt string
        """
        prompt = f"""You are analyzing an AI agent skill for security risks.

## Base Entities (from regex extraction)
{entities_json}

## Full Context
{context}

## Task
Please enhance the extracted entities by:
1. Reviewing the base entities for accuracy
2. Adding any missed entities (especially security-relevant ones)
3. Improving entity descriptions
4. Correcting entity types if misclassified
5. Assigning risk scores (0.0-1.0) based on security relevance

## Security-relevant entity types:
- network: URLs, API endpoints, external services
- permission: sudo, admin, root, elevated privileges
- file: sensitive files (.env, .ssh, credentials)
- api: HTTP requests, network calls
- config: security settings, tokens

## Risk scoring guidelines:
- 0.8-1.0: Critical - Data theft, credential theft, system destruction
- 0.6-0.8: High - Sensitive access, network requests to unknown hosts
- 0.4-0.6: Medium - Code execution, config modifications
- 0.2-0.4: Low - File operations, general tools
- 0.0-0.2: Safe - Documentation, safe operations

## Output Format
Return a JSON array of enhanced entities:
{{
  "entities": [
    {{
      "id": "entity_id",
      "name": "entity_name",
      "type": "entity_type",
      "description": "enhanced_description",
      "risk_score": 0.7,
      "confidence": 0.9,
      "source_section": "section_id"
    }}
  ]
}}

Focus on SECURITY RISKS and malicious patterns. Enhance the existing entities and add any missing ones."""

        return prompt

    def _entities_to_json(self, entities: List[Entity]) -> str:
        """
        Convert entities to JSON string.

        Args:
            entities: List of entities

        Returns:
            JSON string
        """
        entities_data = []
        for entity in entities:
            entities_data.append({
                'id': entity.id,
                'name': entity.name,
                'type': entity.type.value,
                'description': entity.description,
                'risk_score': entity.risk_score,
                'confidence': entity.confidence
            })

        return json.dumps(entities_data, indent=2)

    def _parse_llm_response(self, response_text: str) -> List[Entity]:
        """
        Parse LLM response into entities.

        Args:
            response_text: LLM response text

        Returns:
            List of Entity objects
        """
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                print("Warning: Could not find JSON in LLM response")
                return []

            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            # Convert to Entity objects
            entities = []
            for entity_data in data.get('entities', []):
                try:
                    entity = Entity(
                        id=entity_data['id'],
                        name=entity_data['name'],
                        type=EntityType(entity_data['type']),
                        description=entity_data['description'],
                        risk_score=entity_data.get('risk_score', 0.0),
                        confidence=entity_data.get('confidence', 0.8),
                        source_section=entity_data.get('source_section', '')
                    )
                    entities.append(entity)
                except Exception as e:
                    print(f"Error parsing entity: {e}")
                    continue

            return entities

        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return []

    def _disambiguate_entities(
        self,
        entities: List[Entity],
        content: str
    ) -> List[Entity]:
        """
        Disambiguate similar entities.

        Args:
            entities: List of entities
            content: Full content

        Returns:
            Disambiguated list of entities
        """
        # Group similar entities by name
        entity_groups = {}
        for entity in entities:
            name_lower = entity.name.lower().strip()
            if name_lower not in entity_groups:
                entity_groups[name_lower] = []
            entity_groups[name_lower].append(entity)

        # Merge similar entities
        disambiguated = []
        for name, group in entity_groups.items():
            if len(group) == 1:
                disambiguated.extend(group)
            else:
                # Merge group into one entity
                merged = self._merge_entity_group(group)
                disambiguated.append(merged)

        print(f"Disambiguated {len(entities)} -> {len(disambiguated)} entities")

        return disambiguated

    def _merge_entity_group(self, entities: List[Entity]) -> Entity:
        """
        Merge a group of similar entities.

        Args:
            entities: List of similar entities

        Returns:
            Merged Entity object
        """
        # Use the entity with highest confidence
        primary = max(entities, key=lambda e: e.confidence)

        # Merge descriptions
        descriptions = [e.description for e in entities if e.description]
        merged_description = " | ".join(descriptions[:3])

        # Average risk scores
        avg_risk = sum(e.risk_score for e in entities) / len(entities)

        return Entity(
            id=primary.id,
            name=primary.name,
            type=primary.type,
            description=merged_description,
            risk_score=avg_risk,
            confidence=primary.confidence,
            source_section=primary.source_section
        )

    def _link_to_knowledge_base(
        self,
        entities: List[Entity]
    ) -> List[Entity]:
        """
        Link entities to external knowledge base.

        Args:
            entities: List of entities

        Returns:
            Entities with knowledge base links
        """
        if not self.knowledge_base_path:
            return entities

        try:
            # Load knowledge base
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                kb = json.load(f)

            # Link entities
            linked_entities = []
            for entity in entities:
                # Find matching entry in knowledge base
                match = self._find_kb_match(entity, kb)

                if match:
                    # Enhance entity with KB info
                    entity.properties['kb_match'] = match
                    entity.properties['kb_confidence'] = match.get('confidence', 0.8)

                    # Boost risk if KB indicates high risk
                    if match.get('risk_level') == 'high':
                        entity.risk_score = min(1.0, entity.risk_score * 1.2)

                linked_entities.append(entity)

            print(f"Linked {len([e for e in linked_entities if 'kb_match' in e.properties])} entities to KB")

            return linked_entities

        except Exception as e:
            print(f"Error linking to knowledge base: {e}")
            return entities

    def _find_kb_match(
        self,
        entity: Entity,
        kb: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Find matching entry in knowledge base.

        Args:
            entity: Entity to match
            kb: Knowledge base

        Returns:
            Matching entry or None
        """
        entity_lower = entity.name.lower()

        for entry in kb:
            kb_name = entry.get('name', '').lower()
            kb_aliases = entry.get('aliases', [])

            # Check exact match
            if kb_name == entity_lower:
                return entry

            # Check aliases
            for alias in kb_aliases:
                if alias.lower() == entity_lower:
                    return entry

        return None

    def extract_relationships(
        self,
        entities: List[Entity],
        content: str
    ) -> List[Dict[str, Any]]:
        """
        Extract relationships with LLM enhancement.

        Args:
            entities: List of entities
            content: Content string

        Returns:
            List of relationship dictionaries
        """
        if not self.enabled or not self.client:
            # Fall back to base extractor
            return self.base_extractor.extract_relationships(entities, content)

        # Prepare context
        entities_json = self._entities_to_json(entities)

        # Create prompt for relationship extraction
        prompt = f"""You are analyzing relationships between entities in an AI agent skill.

## Entities
{entities_json}

## Context
{content[:2000]}

## Task
Extract relationships between entities. Focus on security-relevant relationships.

## Relationship types:
- calls: Entity A calls Entity B (function calls, API requests)
- accesses: Entity A accesses Entity B (file reads, config access)
- modifies: Entity A modifies Entity B (writes, changes)
- depends_on: Entity A depends on Entity B
- contains: Entity A contains Entity B

## Output Format
Return a JSON array of relationships:
{{
  "relationships": [
    {{
      "source_id": "entity_id_1",
      "target_id": "entity_id_2",
      "type": "relationship_type",
      "confidence": 0.9
    }}
  ]
}}

Focus on SECURITY-RELEVANT relationships. Prioritize relationships that could indicate risks."""

        try:
            # Call GPT-4
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing code and security relationships."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=1000
            )

            # Parse response
            relationships = self._parse_relationships_response(response.choices[0].message.content)

            return relationships

        except Exception as e:
            print(f"Error in LLM relationship extraction: {e}")
            # Fall back to base extraction
            return self.base_extractor.extract_relationships(entities, content)

    def _parse_relationships_response(self, response_text: str) -> List[Dict[str, Any]]:
        """
        Parse LLM relationship response.

        Args:
            response_text: LLM response text

        Returns:
            List of relationship dictionaries
        """
        try:
            # Extract JSON
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1

            if start_idx == -1 or end_idx == 0:
                return []

            json_str = response_text[start_idx:end_idx]
            data = json.loads(json_str)

            return data.get('relationships', [])

        except Exception as e:
            print(f"Error parsing relationships: {e}")
            return []
