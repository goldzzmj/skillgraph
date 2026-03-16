"""
Data Models for API

Contains Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, EmailStr, validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime
from enum import Enum


# ========== Skill Scan Models ==========

class SkillScanOptions(BaseModel):
    """Options for skill scanning."""
    use_graphrag: bool = Field(True, description="Whether to use GraphRAG")
    use_llm_extraction: bool = Field(True, description="Whether to use LLM-enhanced entity extraction")
    use_gat_risk_model: bool = Field(True, description="Whether to use GAT risk model")
    include_community_detection: bool = Field(True, description="Whether to include community detection")
    include_embeddings: bool = Field(False, description="Whether to include entity embeddings")
    output_format: Literal["json", "html", "pdf"] = Field("json", description="Output format")
    min_confidence: float = Field(0.5, ge=0.0, le=1.0, description="Minimum confidence for results")


class SkillScanRequest(BaseModel):
    """Request model for skill scanning."""
    skill_content: str = Field(..., description="Skill content in Markdown format")
    skill_name: Optional[str] = Field(None, description="Optional skill name")
    skill_type: Optional[str] = Field(None, description="Optional skill type")
    scan_options: Optional[SkillScanOptions] = Field(None, description="Scanning options")


class EntityResult(BaseModel):
    """Result entity from scanning."""
    entity_id: str
    entity_name: str
    entity_type: str
    risk_score: float
    confidence: float
    risk_level: str
    description: Optional[str] = None


class RelationshipResult(BaseModel):
    """Result relationship from scanning."""
    source_id: str
    target_id: str
    relationship_type: str
    weight: float
    confidence: float


class CommunityResult(BaseModel):
    """Result community from scanning."""
    community_id: str
    description: str
    level: int
    risk_score: float
    entities: List[str]
    entity_types: List[str]
    properties: Optional[Dict[str, Any]] = None


class RiskFinding(BaseModel):
    """Risk finding result."""
    id: str
    type: str
    description: str
    severity: str
    confidence: float
    affected_entities: List[str]
    location: Optional[str] = None


class SkillScanResponse(BaseModel):
    """Response model for skill scanning."""
    scan_id: str
    skill_name: Optional[str]
    scan_status: Literal["pending", "completed", "failed"]
    processing_time: float
    risk_summary: Dict[str, Any]
    entities: List[EntityResult]
    relationships: List[RelationshipResult]
    communities: List[CommunityResult]
    risk_findings: List[RiskFinding]
    recommendations: List[str]
    error: Optional[str] = None


# ========== Risk Prediction Models ==========

class RiskPredictionOptions(BaseModel):
    """Options for risk prediction."""
    use_gat_model: bool = Field(True, description="Whether to use GAT model")
    use_ensemble: bool = Field(False, description="Whether to use ensemble method")
    return_attention_weights: bool = Field(True, description="Whether to return attention weights")
    confidence_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Confidence threshold")
    explain_predictions: bool = Field(True, description="Whether to include explanations")


class RiskPredictionRequest(BaseModel):
    """Request model for risk prediction."""
    entities: List[Dict[str, Any]] = Field(..., description="List of entities with features")
    relationships: List[Dict[str, Any]] = Field(..., description="List of relationships")
    prediction_options: Optional[RiskPredictionOptions] = Field(None, description="Prediction options")


class RiskPredictionResponse(BaseModel):
    """Response model for risk prediction."""
    prediction_id: str
    status: Literal["pending", "completed", "failed"]
    predictions: List[EntityResult]
    attention_weights: Optional[Dict[str, float]] = None
    confidence_metrics: Dict[str, float]
    processing_time: float
    explanations: Optional[List[str]] = None
    error: Optional[str] = None


# ========== Batch Processing Models ==========

class BatchOptions(BaseModel):
    """Options for batch processing."""
    parallelism: int = Field(1, ge=1, le=10, description="Number of parallel workers")
    max_concurrent_scans: int = Field(5, ge=1, le=20, description="Maximum concurrent scans")
    priority_order: Literal["queue", "priority"] = Field("queue", description="Order of priority")
    retry_failed: bool = Field(True, description="Whether to retry failed scans")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")


class BatchScanRequest(BaseModel):
    """Request model for batch scanning."""
    skills: List[SkillScanRequest] = Field(..., description="List of skills to scan")
    batch_options: Optional[BatchOptions] = Field(None, description="Batch processing options")


class BatchScanResponse(BaseModel):
    """Response model for batch scanning."""
    batch_id: str
    status: Literal["pending", "in_progress", "completed", "partial", "failed"]
    total_skills: int
    completed_skills: int
    failed_skills: int
    results: List[SkillScanResponse]
    summary: Dict[str, Any]
    errors: List[str]
    processing_time: float
    error: Optional[str] = None


# ========== Authentication Models ==========

class UserLogin(BaseModel):
    """User login request."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response."""
    user_id: str
    email: EmailStr
    access_token: str
    refresh_token: str
    token_type: str
    expires_in: int


class UserCreate(BaseModel):
    """User creation request."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    role: Literal["admin", "user", "analyst", "viewer"] = "user"


# ========== Error Response Models ==========

class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    message: str
    status_code: int
    request_id: Optional[str] = None
    timestamp: datetime
    details: Optional[Dict[str, Any]] = None


# ========== Validation Errors ==========

class ValidationError(BaseModel):
    """Validation error."""
    field: str
    message: str
    value: Optional[Any] = None
