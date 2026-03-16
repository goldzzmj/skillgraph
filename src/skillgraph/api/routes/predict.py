"""
API Routes - Predict Endpoints

Risk prediction endpoints using GAT model.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import uuid
import time

from ..models import RiskPredictionRequest, RiskPredictionResponse
from ..dependencies import get_parser, get_entity_extractor

router = APIRouter(prefix="/api/v1", tags=["predict"])

# Singleton instances
parser = get_parser()
entity_extractor = get_entity_extractor()

# GAT model (will be initialized)
gat_model = None
gat_trainer = None


def init_gat_model():
    """Initialize GAT model and trainer."""
    global gat_model, gat_trainer

    try:
        from skillgraph.graphrag.gat_risk_model import GATRiskTrainer

        # Check if model file exists
        model_path = "models/gat_risk_model/gat_risk_model.pt"

        import os
        if os.path.exists(model_path):
            # Load trained model
            gat_trainer = GATRiskTrainer()
            gat_trainer.load_model(model_path)
            gat_model = gat_trainer.model
            print(f"GAT model loaded from: {model_path}")
        else:
            print(f"Warning: GAT model file not found: {model_path}")
            print("Will use rule-based prediction instead")
            gat_model = None
            gat_trainer = None

    except Exception as e:
        print(f"Error initializing GAT model: {e}")
        gat_model = None
        gat_trainer = None


@router.on_event("startup")
async def startup_event():
    """Initialize GAT model on startup."""
    init_gat_model()


@router.post("/predict", response_model=RiskPredictionResponse)
async def predict_risk(request: RiskPredictionRequest):
    """
    Predict risk scores using GAT model.

    Args:
        request: Risk prediction request

    Returns:
        RiskPredictionResponse with predictions
    """
    try:
        # Initialize model if needed
        init_gat_model()

        # Generate prediction ID
        prediction_id = str(uuid.uuid4())
        start_time = time.time()

        # Check if GAT model is available
        if gat_model is None or gat_trainer is None:
            # Use rule-based prediction
            predictions = rule_based_prediction(request.entities)

            processing_time = time.time() - start_time

            return RiskPredictionResponse(
                prediction_id=prediction_id,
                status="completed",
                predictions=predictions,
                attention_weights=None,
                confidence_metrics={},
                processing_time=processing_time
            )

        # Use GAT model for prediction
        # Convert request data to internal format
        entities = convert_to_internal_entities(request.entities)
        relationships = convert_to_internal_relationships(request.relationships)

        # Run GAT prediction
        prediction_results = gat_trainer.predict_risk(
            entities,
            relationships,
            return_attention=request.prediction_options.return_attention_weights
        )

        processing_time = time.time() - start_time

        # Calculate confidence metrics
        predictions = prediction_results['predictions']

        risk_scores = [p['risk_score'] for p in predictions]
        confidence_scores = [p['confidence'] for p in predictions]

        confidence_metrics = {
            'avg_risk_score': float(sum(risk_scores) / len(risk_scores)) if risk_scores else 0.0,
            'max_risk_score': max(risk_scores) if risk_scores else 0.0,
            'min_risk_score': min(risk_scores) if risk_scores else 0.0,
            'avg_confidence': float(sum(confidence_scores) / len(confidence_scores)) if confidence_scores else 0.0
        }

        # Extract attention weights if available
        attention_weights = None
        if request.prediction_options.return_attention_weights:
            try:
                attention_weights = extract_attention_weights(
                    prediction_results.get('attention_weights', [])
                )
            except Exception as e:
                print(f"Warning: Could not extract attention weights: {e}")

        # Create response
        response = RiskPredictionResponse(
            prediction_id=prediction_id,
            status="completed",
            predictions=predictions,
            attention_weights=attention_weights,
            confidence_metrics=confidence_metrics,
            processing_time=processing_time,
            explanations=prediction_results.get('explanations', [])
        )

        return response

    except Exception as e:
        # Return error response
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction failed: {str(e)}"
        )


@router.get("/predict/{prediction_id}", response_model=RiskPredictionResponse)
async def get_prediction_results(prediction_id: str):
    """
    Get prediction results by prediction ID.

    Args:
        prediction_id: Prediction ID

    Returns:
        RiskPredictionResponse with prediction results
    """
    # In production, this would retrieve from database or cache
    # For now, return a simple response
    return RiskPredictionResponse(
        prediction_id=prediction_id,
        status="pending",
        predictions=[],
        attention_weights=None,
        confidence_metrics={},
        processing_time=0.0,
        explanations=[]
    )


def convert_to_internal_entities(entities: List[Dict[str, Any]]):
    """Convert external entity format to internal format."""
    from skillgraph.graphrag.models import Entity, EntityType

    internal_entities = []

    for i, entity_data in enumerate(entities):
        # Extract properties
        entity_id = entity_data.get('entity_id', f"entity_{i}")
        entity_name = entity_data.get('entity_name', f"entity_{i}")
        entity_type = entity_data.get('entity_type', 'unknown')
        embedding = entity_data.get('embedding')
        risk_score = entity_data.get('risk_score', 0.0)
        confidence = entity_data.get('confidence', 0.8)
        properties = entity_data.get('properties', {})

        # Get entity type enum
        try:
            entity_type_enum = EntityType(entity_type.upper())
        except ValueError:
            entity_type_enum = EntityType.UNKNOWN

        # Create embedding if not provided
        import numpy as np
        if embedding is None:
            embedding = np.random.randn(1536).astype(np.float32)

        # Create entity
        entity = Entity(
            id=entity_id,
            name=entity_name,
            type=entity_type_enum,
            description=f"Entity: {entity_name}",
            embedding=embedding,
            risk_score=risk_score,
            confidence=confidence,
            properties=properties
        )

        internal_entities.append(entity)

    return internal_entities


def convert_to_internal_relationships(relationships: List[Dict[str, Any]]):
    """Convert external relationship format to internal format."""
    from skillgraph.graphrag.models import Relationship, RelationType

    internal_relationships = []

    for rel_data in relationships:
        # Extract properties
        source_id = rel_data.get('source_id', '')
        target_id = rel_data.get('target_id', '')
        relationship_type = rel_data.get('relationship_type', 'calls')
        weight = rel_data.get('weight', 1.0)
        confidence = rel_data.get('confidence', 0.9)

        # Get relation type enum
        try:
            relation_type_enum = RelationType(relationship_type.upper())
        except ValueError:
            relation_type_enum = RelationType.CALLS

        # Create relationship
        relationship = Relationship(
            source_id=source_id,
            target_id=target_id,
            type=relation_type_enum,
            description=f"{source_id} → {target_id}",
            weight=weight,
            confidence=confidence
        )

        internal_relationships.append(relationship)

    return internal_relationships


def rule_based_prediction(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Rule-based risk prediction (fallback)."""
    predictions = []

    risk_keywords = {
        'critical': ['.env', 'secret_key', 'password', 'token', 'ssh_key', 'root_access'],
        'high': ['admin_access', 'sudo_command', 'exec(', 'eval('],
        'medium': ['api_call', 'http_request', 'network_request', 'external_service'],
        'low': ['config_file', 'read_database', 'log_entry']
    }

    for entity_data in entities:
        entity_name = entity_data.get('entity_name', '')

        # Check keywords
        risk_score = 0.0
        for severity, keywords in risk_keywords.items():
            for keyword in keywords:
                if keyword in entity_name.lower():
                    if severity == 'critical':
                        risk_score = max(risk_score, 0.9)
                    elif severity == 'high':
                        risk_score = max(risk_score, 0.7)
                    elif severity == 'medium':
                        risk_score = max(risk_score, 0.5)
                    elif severity == 'low':
                        risk_score = max(risk_score, 0.3)

        # Determine risk level
        if risk_score >= 0.8:
            risk_level = "critical"
        elif risk_score >= 0.6:
            risk_level = "high"
        elif risk_score >= 0.4:
            risk_level = "medium"
        elif risk_score >= 0.2:
            risk_level = "low"
        else:
            risk_level = "safe"

        prediction = {
            'entity_id': entity_data.get('entity_id', ''),
            'entity_name': entity_name,
            'entity_type': entity_data.get('entity_type', ''),
            'risk_score': risk_score,
            'confidence': 0.8,
            'risk_level': risk_level
        }

        predictions.append(prediction)

    return predictions


def extract_attention_weights(attention_data: List[Any]) -> Dict[str, float]:
    """Extract attention weights from model output."""
    attention_weights = {}

    if not attention_data:
        return attention_weights

    # Process attention data (simplified for now)
    for i, attention in enumerate(attention_data):
        if hasattr(attention, 'numpy'):
            # Assume it's a numpy array or tensor
            try:
                import numpy as np
                if isinstance(attention, np.ndarray):
                    avg_attention = np.mean(attention)
                    attention_weights[f"attention_{i}"] = float(avg_attention)
            except Exception as e:
                print(f"Warning: Could not extract attention weight {i}: {e}")
                continue

    return attention_weights
