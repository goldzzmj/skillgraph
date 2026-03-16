"""
API Routes - Scan Endpoints

Skill scanning and analysis endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
import uuid
import time
import numpy as np

from ..models import SkillScanOptions, SkillScanRequest, SkillScanResponse, EntityResult, RiskFinding
from ..dependencies import get_db, get_parser, get_entity_extractor, get_community_detector

router = APIRouter(tags=["scan"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Singleton instances
parser = get_parser()
entity_extractor = get_entity_extractor()
community_detector = get_community_detector()


@router.post("/scan", response_model=SkillScanResponse)
async def scan_skill(
    request: SkillScanRequest,
    background_tasks: BackgroundTasks,
    db: Any = Depends(get_db)
):
    """
    Scan skill and return risk analysis results.

    Args:
        request: Skill scan request
        background_tasks: Background tasks for async processing
        db: Database session

    Returns:
        SkillScanResponse with scan results
    """
    try:
        # Generate scan ID
        scan_id = str(uuid.uuid4())
        start_time = time.time()

        # Parse skill
        skill = parser.parse(request.skill_content)

        # Perform analysis
        entities, relationships, risk_findings, communities = perform_scan(
            skill,
            request.skill_content,
            request.scan_options
        )

        processing_time = time.time() - start_time

        # Calculate risk summary
        risk_summary = calculate_risk_summary(entities, risk_findings)

        # Generate recommendations
        recommendations = generate_recommendations(risk_findings, communities)

        # Prepare entity results
        entity_results = [
            EntityResult(
                entity_id=entity.id,
                entity_name=entity.name,
                entity_type=entity.type.value,
                risk_score=entity.risk_score,
                confidence=entity.confidence,
                risk_level=_risk_level_from_score(entity.risk_score),
                description=entity.description
            )
            for entity in entities
        ]

        # Prepare relationship results
        relationship_results = []
        for rel in relationships[:100]:  # Limit to 100 for response
            if isinstance(rel, dict):
                source_id = rel.get('source_id', '')
                target_id = rel.get('target_id', '')
                relationship_type = rel.get('type', 'unknown')
                weight = rel.get('weight', 1.0)
                confidence = rel.get('confidence', 0.0)
            else:
                source_id = rel.source_id
                target_id = rel.target_id
                relationship_type = rel.type.value if hasattr(rel.type, 'value') else str(rel.type)
                weight = rel.weight
                confidence = rel.confidence

            relationship_results.append({
                'source_id': source_id,
                'target_id': target_id,
                'relationship_type': relationship_type,
                'weight': weight,
                'confidence': confidence
            })

        # Prepare community results
        community_results = []
        for community in communities[:20]:  # Limit to 20 for response
            community_results.append({
                'community_id': community.id,
                'description': community.description,
                'level': community.level.value if hasattr(community.level, 'value') else community.level,
                'risk_score': community.risk_score,
                'entities': community.entities,
                'entity_types': list(set([e.type.value for e in entities if e.id in community.entities])),
                'properties': community.properties
            })

        # Prepare risk findings
        risk_finding_results = []
        for finding in risk_findings[:50]:  # Limit to 50 for response
            risk_finding_results.append({
                'id': str(uuid.uuid4()),
                'type': finding.get('type', 'unknown'),
                'description': finding.get('content_snippet', ''),
                'severity': finding.get('severity', 'unknown'),
                'confidence': finding.get('confidence', 0.0),
                'affected_entities': finding.get('affected_entities', [])
            })

        # Create response
        response = SkillScanResponse(
            scan_id=scan_id,
            skill_name=skill.name,
            scan_status="completed",
            processing_time=processing_time,
            risk_summary=risk_summary,
            entities=entity_results,
            relationships=relationship_results,
            communities=community_results,
            risk_findings=risk_finding_results,
            recommendations=recommendations
        )

        return response

    except Exception as e:
        # Return error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}"
        )


@router.get("/scan/{scan_id}", response_model=SkillScanResponse)
async def get_scan_results(scan_id: str):
    """
    Get scan results by scan ID.

    Args:
        scan_id: Scan ID

    Returns:
        SkillScanResponse with scan results
    """
    # In production, this would retrieve from database or cache
    # For now, return a simple response
    return SkillScanResponse(
        scan_id=scan_id,
        skill_name=None,
        scan_status="pending",
        processing_time=0.0,
        risk_summary={},
        entities=[],
        relationships=[],
        communities=[],
        risk_findings=[],
        recommendations=[]
    )


def perform_scan(skill, skill_content, options):
    """Perform actual skill scanning."""
    if options is None:
        options = SkillScanOptions()

    # Extract entities
    if options.use_graphrag:
        entities = entity_extractor.extract(
            skill_content,
            skill.sections,
            skill.code_blocks
        )
    else:
        entities = []

    # Extract relationships
    relationships = entity_extractor.extract_relationships(
        entities,
        skill_content,
        skill.sections
    )

    # Detect communities
    if options.include_community_detection:
        from skillgraph.graphrag.models import Relationship, RelationType

        relationship_objects = []
        for rel in relationships:
            if isinstance(rel, dict):
                relation_type = rel.get("type", "calls")
                try:
                    relation_type = RelationType(relation_type)
                except ValueError:
                    relation_type = RelationType.CALLS

                relationship_objects.append(
                    Relationship(
                        source_id=rel.get("source_id", ""),
                        target_id=rel.get("target_id", ""),
                        type=relation_type,
                        description=f"{rel.get('source_id', '')} -> {rel.get('target_id', '')}",
                        weight=float(rel.get("weight", 1.0)),
                        confidence=float(rel.get("confidence", 0.0)),
                    )
                )
            else:
                relationship_objects.append(rel)

        communities = community_detector.detect(entities, relationship_objects)
    else:
        communities = []

    # Extract risk findings
    risk_findings = extract_risk_findings(skill_content, entities, options)

    return entities, relationships, risk_findings, communities


def extract_risk_findings(skill_content, entities, options):
    """Extract risk findings from skill content."""
    risk_findings = []

    # Simple risk detection based on keywords
    risk_keywords = [
        '.env', 'secret', 'password', 'token', 'key',
        'sudo', 'root', 'admin', 'exec', 'system',
        'http://', 'https://', 'upload', 'download',
        'rm -rf', 'eval', 'exec('
    ]

    content = skill_content.lower()

    for entity in entities:
        entity_name_lower = entity.name.lower()

        # Check if entity matches risk keywords
        for keyword in risk_keywords:
            if keyword in entity_name_lower:
                risk_findings.append({
                    'type': 'high_risk_entity',
                    'content_snippet': f"Found high-risk {entity.type.value}: {entity.name}",
                    'severity': 'high' if keyword in ['eval(', 'exec(', 'rm -rf'] else 'medium',
                    'confidence': 0.9,
                    'affected_entities': [entity.id]
                })
                break

    return risk_findings


def calculate_risk_summary(entities, risk_findings):
    """Calculate risk summary."""
    high_risk_count = sum(1 for e in entities if e.risk_score > 0.6)
    medium_risk_count = sum(1 for e in entities if 0.4 < e.risk_score <= 0.6)
    low_risk_count = sum(1 for e in entities if 0.2 < e.risk_score <= 0.4)
    safe_count = sum(1 for e in entities if e.risk_score <= 0.2)

    return {
        'total_entities': len(entities),
        'high_risk': high_risk_count,
        'medium_risk': medium_risk_count,
        'low_risk': low_risk_count,
        'safe': safe_count,
        'avg_risk_score': np.mean([e.risk_score for e in entities]) if entities else 0.0,
        'total_risk_findings': len(risk_findings)
    }


def generate_recommendations(risk_findings, communities):
    """Generate recommendations based on risk findings."""
    recommendations = []

    # Risk-based recommendations
    if risk_findings:
        recommendations.append("Review high-risk entities for potential security issues")

        high_risk_findings = [f for f in risk_findings if f['severity'] in ['high', 'critical']]
        if len(high_risk_findings) > 5:
            recommendations.append("High number of high-risk findings detected - thorough security review required")

    # Community-based recommendations
    high_risk_communities = [c for c in communities if c.risk_score > 0.6]
    if len(high_risk_communities) > 2:
        recommendations.append("Multiple high-risk communities detected - analyze community interactions")

    return recommendations


def _risk_level_from_score(score: float) -> str:
    """Map risk score to risk level string."""
    if score >= 0.8:
        return "critical"
    if score >= 0.6:
        return "high"
    if score >= 0.4:
        return "medium"
    if score >= 0.2:
        return "low"
    return "safe"
