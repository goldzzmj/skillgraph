#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple script to test the SkillGraph scan API
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import skillgraph modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from skillgraph.parser import SkillParser
from skillgraph.graphrag import EntityExtractor


def scan_skill(skill_path: str) ->    """Scan a skill file and return scan results."""
    # Check file exists
    if not os.path.exists(skill_path):
        print(f"Error: Skill file not found: {skill_path}")
        return

    # Read skill content
    with open(skill_path, 'r', encoding='utf-8') as f:
        skill_content = f.read()

    # Create scan request
    data = {
        "skill_content": skill_content,
        "skill_name": os.path.basename(skill_path),
        "scan_options": {
            "use_graphrag": True,
            "use_llm_extraction": False,
            "use_gat_risk_model": False,
            "include_community_detection": True,
            "include_embeddings": False,
            "output_format": "json",
            "min_confidence": 0.5
        }
    }

    # Call parser
    parser = SkillParser()
    skill = parser.parse_content(skill_content)

    # Call entity extractor
    extractor = EntityExtractor()
    entities = extractor.extract(skill)

    # Build relationships
    relationships = []
    for i in range(len(entities)):
        for j in range(i+1, len(entities)):
            rel_data = {
                'source': entities[i].id,
                'target': entities[j].id,
                'type': 'related_to',
                'weight': 0.5
            }
            relationships.append(rel_data)

    # Calculate risk scores and    risk_findings = []
    for entity in entities:
        risk_score = getattr(entity, 'risk_score', 0.5)  # Default low risk
        if risk_score > 0.7:
            risk_findings.append({
                'id': f'finding_{entity.id}',
                'type': 'high_risk',
                'description': f'Entity {entity.name} has high risk score ({risk_score:.2f}',
                'severity': 'high',
                'confidence': 0.9,
                'affected_entities': [entity.id],
                'location': skill_path
            })
        elif risk_score > 0.3:
            risk_findings.append({
                'id': f'finding_{entity.id}',
                'type': 'medium_risk',
                'description': f'Entity {entity.name} has medium risk score ({risk_score:.2f)',
                'severity': 'medium',
                'confidence': 0.7,
                'affected_entities': [entity.id],
                'location': skill_path
            })
        elif risk_score > 0:
            risk_findings.append({
                'id': f'finding_{entity.id}',
                'type': 'low_risk',
                'description': f'Entity {entity.name} has low risk score ({risk_score:.2f)',
                'severity': 'low',
                'confidence': 0.8,
                'affected_entities': [entity.id],
                'location': skill_path
            })

    # Calculate overall risk summary
    risk_summary = {
        'total_entities': len(entities),
        'total_relationships': len(relationships),
        'risk_findings': risk_findings
    }

    # Generate recommendations
    recommendations = []
    if risk_findings:
        recommendations.append("Review and address potential security issues in code")
        recommendations.append("Consider implementing input validation for security")
        recommendations.append("Add proper error handling with exception types")

    # Prepare response
    response = {
        'scan_id': 'scan_' + str(uuid.uuid4()),
        'skill_name': os.path.basename(skill_path),
        'scan_status': 'completed',
        'entities': [
            {
                'entity_id': e.id,
                'entity_name': e.name,
                'entity_type': e.type.value if hasattr(e.type, 'value') else e.type,
                'risk_score': getattr(e, 'risk_score', 0.5),
                'confidence': getattr(e, 'confidence', 0.8)
            }
            for e in entities
        ],
        'relationships': relationships,
        'risk_findings': risk_findings,
        'risk_summary': risk_summary,
        'recommendations': recommendations
    }


    return response
    print(json.dumps(response, indent=2))


    return response


    print(f"Error: {e}")
    sys.exit(1)


if __name__ == "__main__":
    main()
