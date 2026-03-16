"""
API Routes - Scan Endpoints

Skill scanning and analysis endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
import uuid
import time
import numpy as np
import io
import zipfile
import json

from ..models import SkillScanOptions, SkillScanRequest, SkillScanResponse, EntityResult, RiskFinding
from ..dependencies import get_db, get_parser, get_entity_extractor, get_community_detector

router = APIRouter(tags=["scan"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Singleton instances
parser = get_parser()
entity_extractor = get_entity_extractor()
community_detector = get_community_detector()
UPLOAD_GRAPH_PREVIEWS: Dict[str, str] = {}
LATEST_UPLOAD_SCAN_ID: Optional[str] = None


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
                'level': _community_level_to_value(community.level),
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


@router.post("/scan/upload")
async def scan_skill_upload(
    skill_file: Optional[UploadFile] = File(None, description="Single markdown file"),
    skill_files: Optional[List[UploadFile]] = File(None, description="Multiple markdown files (folder upload)"),
    skill_folder_zip: Optional[UploadFile] = File(None, description="ZIP file for a full folder"),
    include_graph: bool = Form(True),
    use_graphrag: bool = Form(True),
    include_community_detection: bool = Form(True),
):
    """Scan uploaded file/folder (multipart) and optionally return graph view data."""
    global LATEST_UPLOAD_SCAN_ID

    scan_id = str(uuid.uuid4())
    start_time = time.time()

    scan_options = SkillScanOptions(
        use_graphrag=use_graphrag,
        include_community_detection=include_community_detection,
    )

    files_to_scan: List[Dict[str, str]] = []

    if skill_file is not None:
        content = await skill_file.read()
        text = _decode_text_file(content)
        if _is_markdown_file(skill_file.filename or ""):
            files_to_scan.append({"path": skill_file.filename or "skill.md", "content": text})

    if skill_files:
        for f in skill_files:
            content = await f.read()
            text = _decode_text_file(content)
            if _is_markdown_file(f.filename or ""):
                files_to_scan.append({"path": f.filename or "skill.md", "content": text})

    if skill_folder_zip is not None:
        zip_bytes = await skill_folder_zip.read()
        files_to_scan.extend(_extract_markdown_from_zip(zip_bytes))

    if not files_to_scan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No markdown files found. Please upload .md/.markdown/.mkd/.txt files or a ZIP containing them.",
        )

    all_entities = []
    all_relationships = []
    all_risk_findings = []
    all_communities = []
    per_file_results = []

    for idx, file_item in enumerate(files_to_scan):
        skill = parser.parse(file_item["content"])
        entities, relationships, risk_findings, communities = perform_scan(
            skill,
            file_item["content"],
            scan_options,
        )

        entity_id_map = {}
        for e in entities:
            old_id = e.id
            e.id = f"f{idx}_{old_id}"
            entity_id_map[old_id] = e.id

        normalized_rels = []
        for rel in relationships:
            if isinstance(rel, dict):
                source_id = entity_id_map.get(rel.get("source_id", ""), rel.get("source_id", ""))
                target_id = entity_id_map.get(rel.get("target_id", ""), rel.get("target_id", ""))
                normalized_rels.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "type": rel.get("type", "unknown"),
                        "weight": rel.get("weight", 1.0),
                        "confidence": rel.get("confidence", 0.0),
                    }
                )
            else:
                normalized_rels.append(
                    {
                        "source_id": entity_id_map.get(rel.source_id, rel.source_id),
                        "target_id": entity_id_map.get(rel.target_id, rel.target_id),
                        "type": rel.type.value if hasattr(rel.type, "value") else str(rel.type),
                        "weight": rel.weight,
                        "confidence": rel.confidence,
                    }
                )

        for finding in risk_findings:
            finding["file_path"] = file_item["path"]
            finding["affected_entities"] = [entity_id_map.get(eid, eid) for eid in finding.get("affected_entities", [])]

        all_entities.extend(entities)
        all_relationships.extend(normalized_rels)
        all_risk_findings.extend(risk_findings)
        all_communities.extend(communities)

        per_file_results.append(
            {
                "file_path": file_item["path"],
                "entities": len(entities),
                "relationships": len(normalized_rels),
                "risk_findings": len(risk_findings),
            }
        )

    processing_time = time.time() - start_time
    risk_summary = calculate_risk_summary(all_entities, all_risk_findings)
    recommendations = generate_recommendations(all_risk_findings, all_communities)

    graph_data = _build_graph_view(files_to_scan, all_entities, all_relationships, all_risk_findings) if include_graph else {"nodes": [], "edges": []}

    response = {
        "scan_id": scan_id,
        "scan_status": "completed",
        "processing_time": processing_time,
        "input_files": len(files_to_scan),
        "per_file_results": per_file_results,
        "risk_summary": risk_summary,
        "entities": [
            {
                "entity_id": e.id,
                "entity_name": e.name,
                "entity_type": e.type.value,
                "risk_score": e.risk_score,
                "risk_level": _risk_level_from_score(e.risk_score),
                "confidence": e.confidence,
            }
            for e in all_entities
        ],
        "relationships": all_relationships,
        "risk_findings": all_risk_findings,
        "recommendations": recommendations,
        "graph": {
            "nodes": graph_data["nodes"],
            "edges": graph_data["edges"],
            "html": _build_graph_html(graph_data),
        } if include_graph else None,
    }

    if include_graph and response.get("graph") and response["graph"].get("html"):
        UPLOAD_GRAPH_PREVIEWS[scan_id] = response["graph"]["html"]
        LATEST_UPLOAD_SCAN_ID = scan_id

    return response


@router.get("/scan/upload/preview", response_class=HTMLResponse)
async def scan_upload_preview(scan_id: Optional[str] = None):
    """Return upload scan graph preview page as HTML."""
    preview_scan_id = scan_id or LATEST_UPLOAD_SCAN_ID
    if not preview_scan_id or preview_scan_id not in UPLOAD_GRAPH_PREVIEWS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No upload graph preview found. Run POST /api/v1/scan/upload with include_graph=true first.",
        )
    return HTMLResponse(content=UPLOAD_GRAPH_PREVIEWS[preview_scan_id])


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


def _community_level_to_value(level: Any) -> Any:
    try:
        return level.value
    except Exception:
        return level


def _is_markdown_file(filename: str) -> bool:
    lower_name = filename.lower()
    return lower_name.endswith((".md", ".markdown", ".mkd", ".txt"))


def _decode_text_file(raw: bytes) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gbk", "latin-1"):
        try:
            return raw.decode(encoding)
        except Exception:
            continue
    return raw.decode("utf-8", errors="ignore")


def _extract_markdown_from_zip(zip_bytes: bytes) -> List[Dict[str, str]]:
    files = []
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes), "r") as archive:
            for info in archive.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                if ".." in name:
                    continue
                if not _is_markdown_file(name):
                    continue
                raw = archive.read(info)
                files.append({"path": name, "content": _decode_text_file(raw)})
    except zipfile.BadZipFile as exc:
        raise HTTPException(status_code=400, detail=f"Invalid ZIP file: {exc}")
    return files


def _build_graph_view(files_to_scan, entities, relationships, risk_findings) -> Dict[str, Any]:
    nodes = []
    edges = []
    file_node_ids = {}

    for i, file_item in enumerate(files_to_scan):
        node_id = f"file_{i}"
        file_node_ids[file_item["path"]] = node_id
        nodes.append(
            {
                "id": node_id,
                "label": file_item["path"],
                "group": "file",
                "color": "#2563eb",
            }
        )

    for entity in entities:
        nodes.append(
            {
                "id": entity.id,
                "label": entity.name,
                "group": entity.type.value,
                "color": _color_for_risk(_risk_level_from_score(entity.risk_score)),
            }
        )

    for i, finding in enumerate(risk_findings):
        finding_id = f"risk_{i}"
        nodes.append(
            {
                "id": finding_id,
                "label": finding.get("type", "risk"),
                "group": "risk",
                "color": _color_for_risk(finding.get("severity", "medium")),
            }
        )
        for entity_id in finding.get("affected_entities", []):
            edges.append({"from": finding_id, "to": entity_id, "label": "affects"})

        file_path = finding.get("file_path")
        if file_path in file_node_ids:
            edges.append({"from": file_node_ids[file_path], "to": finding_id, "label": "contains"})

    for rel in relationships:
        edges.append(
            {
                "from": rel.get("source_id", ""),
                "to": rel.get("target_id", ""),
                "label": rel.get("type", "related"),
            }
        )

    return {"nodes": nodes, "edges": edges}


def _color_for_risk(level: str) -> str:
    colors = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#ca8a04",
        "low": "#16a34a",
        "safe": "#0284c7",
    }
    return colors.get(level, "#6b7280")


def _build_graph_html(graph_data: Dict[str, Any]) -> str:
    nodes_json = json.dumps(graph_data.get("nodes", []), ensure_ascii=False)
    edges_json = json.dumps(graph_data.get("edges", []), ensure_ascii=False)
    return (
        "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>SkillGraph View</title>"
        "<script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>"
        "</head><body><div id='mynetwork' style='width:100%;height:720px;border:1px solid #ddd;'></div>"
        "<script>"
        f"const nodes = new vis.DataSet({nodes_json});"
        f"const edges = new vis.DataSet({edges_json});"
        "const container=document.getElementById('mynetwork');"
        "const data={nodes,edges};"
        "const options={physics:{stabilization:false},interaction:{hover:true},edges:{arrows:'to'}};"
        "new vis.Network(container,data,options);"
        "</script></body></html>"
    )
