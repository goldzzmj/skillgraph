"""
FastAPI Application - Simple Configuration

简化版本，只包含核心扫描功能
"""

import os
import sys

# Add src to path
src_path = os.path.join(os.path.dirname(__file__), '..', '..')
sys.path.insert(0, str(src_path))

from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import uuid
import time

# FastAPI application
app = FastAPI(
    title="SkillGraph API",
    description="AI Agent Skills Security Detection API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Request models
class SkillScanRequest(BaseModel):
    skill_content: str
    skill_name: Optional[str] = None
    scan_options: Optional[Dict[str, Any]] = None

class EntityResult(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    risk_score: float
    confidence: float
    risk_level: str
    description: Optional[str] = None

class RiskFinding(BaseModel):
    id: str
    type: str
    description: str
    severity: str
    confidence: float
    affected_entities: List[str]

class SkillScanResponse(BaseModel):
    scan_id: str
    skill_name: str
    scan_status: str
    processing_time: float
    entities: List[EntityResult]
    relationships: List[Dict[str, Any]]
    risk_findings: List[Dict[str, Any]]
    risk_summary: Dict[str, Any]
    recommendations: List[str]

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "SkillGraph API",
        "version": "1.0.0",
        "description": "AI Agent Skills Security Detection API",
        "endpoints": {
            "health": "/health",
            "scan": "/api/v1/scan"
        },
        "documentation": {
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "api": "ready"
        }
    }

# Scan endpoint
@app.post("/api/v1/scan", response_model=SkillScanResponse)
async def scan_skill(request: SkillScanRequest):
    """Scan skill and return risk analysis results."""
    start_time = time.time()
    scan_id = str(uuid.uuid4())

    # Simple risk detection based on keywords
    risk_keywords = [
        '.env', 'secret', 'password', 'token', 'api_key',
        'sudo', 'root', 'admin', 'exec', 'system(',
        'eval(', 'rm -rf', 'chmod 777', 'curl',
        'requests.get', 'subprocess.Popen', 'os.system'
    ]

    content_lower = request.skill_content.lower()
    risk_findings = []
    entities = []

    # Check for risk keywords
    for keyword in risk_keywords:
        if keyword in content_lower:
            risk_findings.append({
                "id": str(uuid.uuid4()),
                "type": "keyword_detected",
                "description": f"Potentially risky keyword found: {keyword}",
                "severity": "medium" if keyword in ['.env', 'secret', 'password', 'token', 'api_key'] else "low",
                "confidence": 0.0,
                "affected_entities": []
            })

    # Calculate overall risk
    overall_risk = len(risk_findings) * 0.1

    processing_time = time.time() - start_time

    return SkillScanResponse(
        scan_id=scan_id,
        skill_name=request.skill_name or "unknown",
        scan_status="completed",
        processing_time=processing_time,
        entities=entities,
        relationships=[],
        risk_findings=risk_findings,
        risk_summary={
            "total_findings": len(risk_findings),
            "overall_risk_score": overall_risk,
            "risk_level": "high" if overall_risk > 0.5 else "medium" if overall_risk > 0.2 else "low"
        },
        recommendations=[
            "Review detected keywords for potential security issues",
            "Ensure sensitive data is properly protected"
        ] if risk_findings else []
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
