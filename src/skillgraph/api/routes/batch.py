"""
API Routes - Batch Processing Endpoints

Batch processing endpoints for skill scanning and risk prediction.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from typing import List, Dict, Any
import uuid
import time

from ..models import BatchScanRequest, BatchScanResponse, SkillScanRequest, SkillScanResponse
from ..dependencies import get_parser, get_entity_extractor

router = APIRouter(prefix="/api/v1", tags=["batch"])

# Singleton instances
parser = get_parser()
entity_extractor = get_entity_extractor()


@router.post("/batch", response_model=BatchScanResponse)
async def batch_scan_skills(
    request: BatchScanRequest,
    background_tasks: BackgroundTasks
):
    """
    Batch scan multiple skills.

    Args:
        request: Batch scan request
        background_tasks: Background tasks for async processing

    Returns:
        BatchScanResponse with batch processing status
    """
    try:
        # Generate batch ID
        batch_id = str(uuid.uuid4())
        start_time = time.time()

        # Submit individual scans to background tasks
        batch_results = []

        for skill_data in request.skills:
            # Create scan request
            scan_request = SkillScanRequest(
                skill_content=skill_data['skill_content'],
                skill_name=skill_data.get('skill_name'),
                skill_type=skill_data.get('skill_type'),
                scan_options=skill_data.get('scan_options')
            )

            # Submit to background task
            # In production, this would be a Celery task
            # For now, we simulate immediate processing
            try:
                scan_result = perform_scan(scan_request)

                if scan_result.get('error') is None:
                    batch_results.append(scan_result)
                else:
                    batch_results.append({
                        'scan_id': str(uuid.uuid4()),
                        'skill_name': scan_request.skill_name,
                        'scan_status': 'failed',
                        'error': scan_result['error']
                    })

            except Exception as e:
                batch_results.append({
                    'scan_id': str(uuid.uuid4()),
                    'skill_name': scan_request.skill_name,
                    'scan_status': 'failed',
                    'error': str(e)
                })

        processing_time = time.time() - start_time

        # Calculate summary
        total_skills = len(request.skills)
        completed_skills = len([r for r in batch_results if r.get('scan_status') == 'completed'])
        failed_skills = len([r for r in batch_results if r.get('scan_status') == 'failed'])

        # Aggregate risk summary
        risk_summary = aggregate_batch_risks(batch_results)

        # Create response
        response = BatchScanResponse(
            batch_id=batch_id,
            status="completed",
            total_skills=total_skills,
            completed_skills=completed_skills,
            failed_skills=failed_skills,
            results=batch_results,
            summary=risk_summary,
            errors=[],
            processing_time=processing_time
        )

        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch scan failed: {str(e)}"
        )


@router.get("/batch/{batch_id}", response_model=BatchScanResponse)
async def get_batch_results(batch_id: str):
    """
    Get batch scan results by batch ID.

    Args:
        batch_id: Batch ID

    Returns:
        BatchScanResponse with batch results
    """
    # In production, this would retrieve from database or cache
    # For now, return a simple response
    return BatchScanResponse(
        batch_id=batch_id,
        status="pending",
        total_skills=0,
        completed_skills=0,
        failed_skills=0,
        results=[],
        summary={},
        errors=[]
    )


def perform_scan(scan_request: SkillScanRequest) -> Dict[str, Any]:
    """Perform single skill scan."""
    try:
        # Parse skill
        skill = parser.parse_content(scan_request.skill_content)

        # Extract entities
        entities = entity_extractor.extract(
            scan_request.skill_content,
            skill.sections,
            skill.code_blocks
        )

        # Extract relationships
        relationships = entity_extractor.extract_relationships(
            entities,
            scan_request.skill_content
        )

        # Analyze risk
        risk_summary = {
            'total_entities': len(entities),
            'total_relationships': len(relationships),
            'high_risk_entities': sum(1 for e in entities if e.risk_score > 0.6)
        }

        # Create scan result
        result = {
            'scan_id': str(uuid.uuid4()),
            'skill_name': skill.name,
            'scan_status': 'completed',
            'risk_summary': risk_summary,
            'entities': [
                {
                    'entity_id': entity.id,
                    'entity_name': entity.name,
                    'entity_type': entity.type.value,
                    'risk_score': entity.risk_score,
                    'confidence': entity.confidence
                }
                for entity in entities[:100]  # Limit to 100 for response
            ],
            'relationships': len(relationships),
            'processing_time': 0.1
        }

        return result

    except Exception as e:
        return {
            'scan_id': str(uuid.uuid4()),
            'skill_name': scan_request.skill_name,
            'scan_status': 'failed',
            'error': str(e)
        }


def aggregate_batch_risks(batch_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate risks from batch results."""
    total_entities = 0
    total_relationships = 0
    high_risk_entities = 0
    medium_risk_entities = 0
    low_risk_entities = 0

    for result in batch_results:
        if result.get('scan_status') == 'completed':
            risk_summary = result.get('risk_summary', {})

            total_entities += risk_summary.get('total_entities', 0)
            total_relationships += risk_summary.get('total_relationships', 0)
            high_risk_entities += risk_summary.get('high_risk_entities', 0)

    return {
        'total_entities': total_entities,
        'total_relationships': total_relationships,
        'high_risk_entities': high_risk_entities,
        'medium_risk_entities': medium_risk_entities,
        'low_risk_entities': low_risk_entities,
        'high_risk_ratio': high_risk_entities / total_entities if total_entities > 0 else 0.0
    }
