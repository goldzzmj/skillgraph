"""
API Routes - Scan Endpoints

Skill scanning and analysis endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from fastapi.security import OAuth2PasswordBearer
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional, Tuple
import uuid
import time
import numpy as np
import io
import zipfile
import json
import re
from collections import Counter

from ..models import SkillScanOptions, SkillScanRequest, SkillScanResponse, EntityResult, RiskFinding
from ..dependencies import get_db, get_parser, get_entity_extractor, get_community_detector
from skillgraph.rules import RiskDetector

router = APIRouter(tags=["scan"])

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Singleton instances
parser = get_parser()
entity_extractor = get_entity_extractor()
community_detector = get_community_detector()
risk_detector = RiskDetector()
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
                'id': finding.get('id', str(uuid.uuid4())),
                'type': finding.get('type', 'unknown'),
                'description': finding.get('content_snippet', ''),
                'severity': finding.get('severity', 'unknown'),
                'confidence': finding.get('confidence', 0.0),
                'affected_entities': finding.get('affected_entities', []),
                'location': _format_location_text(finding.get('location'))
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
    """Scan uploaded file/folder and return graph/risk analysis for frontend visualization."""
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

    all_entities: List[Any] = []
    all_relationships: List[Dict[str, Any]] = []
    all_risk_findings: List[Dict[str, Any]] = []
    all_communities: List[Any] = []
    per_file_results: List[Dict[str, Any]] = []
    parsed_files: List[Dict[str, Any]] = []

    for idx, file_item in enumerate(sorted(files_to_scan, key=lambda item: item["path"])):
        file_path = file_item["path"]
        file_content = file_item["content"]
        skill = parser.parse(file_content)
        section_blocks = _build_section_blocks(file_content, skill.sections)

        entities, relationships, risk_findings, communities = perform_scan(
            skill,
            file_content,
            scan_options,
            file_path=file_path,
            section_blocks=section_blocks,
            finding_id_prefix=f"f{idx}",
        )

        # Make entity ids globally unique across files and attach file metadata.
        entity_id_map: Dict[str, str] = {}
        for entity in entities:
            old_id = entity.id
            new_id = f"f{idx}_{old_id}"
            entity.id = new_id
            entity_id_map[old_id] = new_id
            entity.properties = entity.properties or {}
            entity.properties["file_path"] = file_path
            if entity.source_section:
                section_meta = _find_section_by_id(section_blocks, entity.source_section)
                if section_meta:
                    entity.properties["section_title"] = section_meta.get("section_title", "")
                    entity.properties["line_start"] = section_meta.get("line_start")
                    entity.properties["line_end"] = section_meta.get("line_end")

        normalized_rels: List[Dict[str, Any]] = []
        for rel in relationships:
            if isinstance(rel, dict):
                source_id = entity_id_map.get(rel.get("source_id", ""), rel.get("source_id", ""))
                target_id = entity_id_map.get(rel.get("target_id", ""), rel.get("target_id", ""))
                rel_type = rel.get("type", "unknown")
                normalized_rels.append(
                    {
                        "source_id": source_id,
                        "target_id": target_id,
                        "type": rel_type,
                        "relationship_label": _relationship_label(rel_type),
                        "weight": rel.get("weight", 1.0),
                        "confidence": rel.get("confidence", 0.0),
                        "file_path": file_path,
                    }
                )
            else:
                rel_type = rel.type.value if hasattr(rel.type, "value") else str(rel.type)
                normalized_rels.append(
                    {
                        "source_id": entity_id_map.get(rel.source_id, rel.source_id),
                        "target_id": entity_id_map.get(rel.target_id, rel.target_id),
                        "type": rel_type,
                        "relationship_label": _relationship_label(rel_type),
                        "weight": rel.weight,
                        "confidence": rel.confidence,
                        "file_path": file_path,
                    }
                )

        for ridx, finding in enumerate(risk_findings):
            finding["id"] = f"risk_f{idx}_{ridx:03d}"
            finding["file_path"] = file_path
            finding["affected_entities"] = [
                entity_id_map.get(entity_id, entity_id)
                for entity_id in finding.get("affected_entities", [])
            ]

        file_risk_score = _calculate_file_risk_score(entities, risk_findings)
        file_risk_level = _risk_level_from_score(file_risk_score)

        all_entities.extend(entities)
        all_relationships.extend(normalized_rels)
        all_risk_findings.extend(risk_findings)
        all_communities.extend(communities)

        per_file_results.append(
            {
                "file_path": file_path,
                "risk_score": file_risk_score,
                "risk_level": file_risk_level,
                "entities": len(entities),
                "relationships": len(normalized_rels),
                "risk_findings": len(risk_findings),
                "sections": len(section_blocks),
            }
        )

        parsed_files.append(
            {
                "file_path": file_path,
                "section_blocks": section_blocks,
                "risk_findings": [_compact_risk_finding(item) for item in risk_findings],
            }
        )

    processing_time = time.time() - start_time
    risk_summary = calculate_risk_summary(all_entities, all_risk_findings)
    recommendations = generate_recommendations(all_risk_findings, all_communities)

    graph_data = (
        _build_graph_view(parsed_files, all_entities, all_relationships, all_risk_findings)
        if include_graph
        else {"nodes": [], "edges": [], "legend": []}
    )

    response = {
        "scan_id": scan_id,
        "scan_status": "completed",
        "processing_time": processing_time,
        "input_files": len(files_to_scan),
        "per_file_results": per_file_results,
        "file_index": parsed_files,
        "risk_summary": risk_summary,
        "entities": [
            {
                "entity_id": e.id,
                "entity_name": e.name,
                "entity_type": e.type.value,
                "risk_score": e.risk_score,
                "risk_level": _risk_level_from_score(e.risk_score),
                "confidence": e.confidence,
                "description": e.description,
                "file_path": (e.properties or {}).get("file_path"),
                "section_title": (e.properties or {}).get("section_title"),
                "line_start": (e.properties or {}).get("line_start"),
                "line_end": (e.properties or {}).get("line_end"),
            }
            for e in all_entities
        ],
        "relationships": all_relationships,
        "risk_findings": all_risk_findings,
        "recommendations": recommendations,
        "graph_preview_url": f"/api/v1/scan/upload/preview?scan_id={scan_id}" if include_graph else None,
        "graph": {
            "nodes": graph_data["nodes"],
            "edges": graph_data["edges"],
            "legend": graph_data.get("legend", []),
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


def perform_scan(
    skill,
    skill_content,
    options,
    file_path: str = "",
    section_blocks: Optional[List[Dict[str, Any]]] = None,
    finding_id_prefix: str = "",
):
    """Perform actual skill scanning."""
    if options is None:
        options = SkillScanOptions()

    if section_blocks is None:
        section_blocks = _build_section_blocks(skill_content, skill.sections)

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
    risk_findings = extract_risk_findings(
        skill_content,
        entities,
        options,
        parsed_skill=skill,
        file_path=file_path,
        section_blocks=section_blocks,
        finding_id_prefix=finding_id_prefix,
    )

    return entities, relationships, risk_findings, communities


def extract_risk_findings(
    skill_content,
    entities,
    options,
    parsed_skill=None,
    file_path: str = "",
    section_blocks: Optional[List[Dict[str, Any]]] = None,
    finding_id_prefix: str = "",
):
    """Extract risk findings from content and entities with location metadata."""
    if parsed_skill is None:
        parsed_skill = parser.parse(skill_content)

    if section_blocks is None:
        section_blocks = _build_section_blocks(skill_content, parsed_skill.sections)

    risk_findings: List[Dict[str, Any]] = []

    # 1) Rule-based detection with richer suggestions and snippets.
    for idx, finding in enumerate(risk_detector.detect(parsed_skill)):
        location = _locate_content_block(skill_content, finding.content_snippet, section_blocks)
        affected_entities = _find_affected_entities(
            entities,
            finding.content_snippet,
            location.get("section_id"),
        )

        risk_findings.append(
            {
                "id": f"risk_{finding_id_prefix}_{idx:03d}" if finding_id_prefix else f"risk_{idx:03d}",
                "type": finding.category,
                "severity": finding.level.value,
                "confidence": 0.95,
                "description": finding.description,
                "content_snippet": finding.content_snippet,
                "suggestion": finding.suggestion,
                "affected_entities": affected_entities,
                "file_path": file_path,
                "location": location,
            }
        )

    # 2) Entity-level fallback for suspicious entities missed by rule engine.
    risky_entities = [entity for entity in entities if entity.risk_score >= 0.55]
    for entity in risky_entities:
        if any(entity.id in item.get("affected_entities", []) for item in risk_findings):
            continue

        section_meta = _find_section_by_id(section_blocks, entity.source_section)
        location = {
            "section_id": entity.source_section,
            "section_title": (section_meta or {}).get("section_title", "Unknown section"),
            "line_start": (section_meta or {}).get("line_start"),
            "line_end": (section_meta or {}).get("line_end"),
            "content_block": (section_meta or {}).get("content_preview", ""),
        }

        risk_findings.append(
            {
                "id": f"risk_entity_{entity.id}",
                "type": "suspicious_entity",
                "severity": _risk_level_from_score(entity.risk_score),
                "confidence": min(1.0, max(0.6, entity.confidence)),
                "description": f"Potentially risky entity: {entity.name}",
                "content_snippet": entity.name,
                "suggestion": "Review this entity and confirm whether it requires elevated access or external data transfer.",
                "affected_entities": [entity.id],
                "file_path": file_path,
                "location": location,
            }
        )

    # 3) Deduplicate and sort by severity and confidence.
    deduped: List[Dict[str, Any]] = []
    seen_keys = set()
    for finding in risk_findings:
        key = (
            finding.get("type", ""),
            finding.get("content_snippet", ""),
            finding.get("file_path", ""),
            (finding.get("location") or {}).get("line_start", -1),
        )
        if key in seen_keys:
            continue
        seen_keys.add(key)
        deduped.append(finding)

    deduped.sort(
        key=lambda item: (
            _severity_rank(item.get("severity", "low")),
            -float(item.get("confidence", 0.0)),
        )
    )

    return deduped


def calculate_risk_summary(entities, risk_findings):
    """Calculate risk summary."""
    high_risk_count = sum(1 for e in entities if e.risk_score > 0.6)
    medium_risk_count = sum(1 for e in entities if 0.4 < e.risk_score <= 0.6)
    low_risk_count = sum(1 for e in entities if 0.2 < e.risk_score <= 0.4)
    safe_count = sum(1 for e in entities if e.risk_score <= 0.2)

    entity_score = float(np.mean([e.risk_score for e in entities])) if entities else 0.0
    finding_scores = [_severity_score(item.get("severity", "safe")) for item in risk_findings]
    findings_score = float(np.mean(finding_scores)) if finding_scores else 0.0
    overall_score = max(entity_score, findings_score)

    severity_counter = Counter(item.get("severity", "unknown") for item in risk_findings)

    return {
        'total_entities': len(entities),
        'high_risk': high_risk_count,
        'medium_risk': medium_risk_count,
        'low_risk': low_risk_count,
        'safe': safe_count,
        'avg_risk_score': entity_score,
        'total_risk_findings': len(risk_findings),
        'overall_risk_score': round(overall_score, 3),
        'overall_risk_level': _risk_level_from_score(overall_score),
        'severity_distribution': {
            'critical': severity_counter.get('critical', 0),
            'high': severity_counter.get('high', 0),
            'medium': severity_counter.get('medium', 0),
            'low': severity_counter.get('low', 0),
        },
    }


def generate_recommendations(risk_findings, communities):
    """Generate recommendations based on risk findings."""
    recommendations: List[str] = []

    if not risk_findings:
        return [
            "No obvious risky pattern detected. Keep least-privilege defaults and pin trusted tool versions.",
        ]

    high_risk_findings = [f for f in risk_findings if f.get('severity') in ['high', 'critical']]
    if high_risk_findings:
        recommendations.append(
            "Prioritize remediation for high/critical findings: restrict sensitive file access, block destructive commands, and validate external endpoints."
        )

    category_counter = Counter(item.get('type', 'unknown') for item in risk_findings)
    for category, _ in category_counter.most_common(3):
        recommendations.append(f"Review repeated risk category `{category}` and add explicit guardrails in skill instructions.")

    high_risk_communities = [community for community in communities if community.risk_score > 0.6]
    if len(high_risk_communities) > 1:
        recommendations.append("Multiple risky communities were detected; split unsafe steps into isolated, auditable phases.")

    return recommendations[:6]


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


def _severity_score(level: str) -> float:
    mapping = {
        "critical": 0.95,
        "high": 0.75,
        "medium": 0.55,
        "low": 0.35,
        "safe": 0.1,
    }
    return mapping.get((level or "").lower(), 0.2)


def _severity_rank(level: str) -> int:
    rank = {
        "critical": 0,
        "high": 1,
        "medium": 2,
        "low": 3,
        "safe": 4,
    }
    return rank.get((level or "").lower(), 5)


def _calculate_file_risk_score(entities: List[Any], risk_findings: List[Dict[str, Any]]) -> float:
    entity_score = float(np.mean([entity.risk_score for entity in entities])) if entities else 0.0
    finding_score = float(np.mean([_severity_score(item.get("severity", "safe")) for item in risk_findings])) if risk_findings else 0.0
    return round(max(entity_score, finding_score), 3)


def _relationship_label(rel_type: str) -> str:
    labels = {
        "calls": "calls",
        "depends_on": "depends on",
        "accesses": "accesses",
        "modifies": "modifies",
        "contains": "contains",
        "requires": "requires",
        "validates": "validates",
        "transforms": "transforms",
        "authenticates": "authenticates",
    }
    return labels.get(rel_type, rel_type.replace("_", " "))


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
    files: List[Dict[str, str]] = []
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


def _build_section_blocks(content: str, sections: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Build section blocks with line range and content previews."""
    lines = content.splitlines()
    total_lines = len(lines)
    blocks: List[Dict[str, Any]] = []

    sorted_sections = sorted(sections or [], key=lambda item: (item.get("position", {}).get("start", 0), item.get("id", "")))
    for idx, section in enumerate(sorted_sections):
        line_start = int(section.get("position", {}).get("start", 0)) + 1
        if idx + 1 < len(sorted_sections):
            next_start = int(sorted_sections[idx + 1].get("position", {}).get("start", total_lines))
            line_end = max(line_start, next_start)
        else:
            line_end = total_lines

        snippet_start = max(1, line_start)
        snippet_end = min(total_lines, snippet_start + 24)
        content_preview = "\n".join(lines[snippet_start - 1:snippet_end]).strip()

        blocks.append(
            {
                "section_id": section.get("id", f"section_{idx}"),
                "section_title": section.get("title", "Untitled"),
                "level": section.get("level", 1),
                "line_start": line_start,
                "line_end": line_end,
                "content_preview": content_preview,
            }
        )

    if not blocks:
        blocks.append(
            {
                "section_id": "section_000",
                "section_title": "Document",
                "level": 1,
                "line_start": 1,
                "line_end": total_lines,
                "content_preview": "\n".join(lines[:25]).strip(),
            }
        )
    return blocks


def _find_section_by_id(section_blocks: List[Dict[str, Any]], section_id: str) -> Optional[Dict[str, Any]]:
    for section in section_blocks:
        if section.get("section_id") == section_id:
            return section
    return None


def _locate_content_block(
    content: str,
    snippet: str,
    section_blocks: List[Dict[str, Any]],
    context_lines: int = 3,
) -> Dict[str, Any]:
    """Locate snippet to section/line info with context block."""
    lines = content.splitlines()
    total_lines = max(1, len(lines))

    snippet_text = (snippet or "").strip()
    lower_content = content.lower()
    start_pos = lower_content.find(snippet_text.lower()) if snippet_text else -1

    if start_pos >= 0:
        line_start = content[:start_pos].count("\n") + 1
        line_end = line_start + max(0, snippet_text.count("\n"))
    else:
        line_start = section_blocks[0].get("line_start", 1) if section_blocks else 1
        line_end = line_start

    view_start = max(1, line_start - context_lines)
    view_end = min(total_lines, line_end + context_lines)
    content_block = "\n".join(lines[view_start - 1:view_end]).strip()

    section_title = "Document"
    section_id = ""
    for section in section_blocks:
        if section.get("line_start", 1) <= line_start <= section.get("line_end", total_lines):
            section_title = section.get("section_title", "Document")
            section_id = section.get("section_id", "")
            break

    return {
        "section_id": section_id,
        "section_title": section_title,
        "line_start": line_start,
        "line_end": line_end,
        "content_block": content_block,
    }


def _find_affected_entities(entities: List[Any], snippet: str, section_id: Optional[str]) -> List[str]:
    """Find entities associated with a snippet or section."""
    affected: List[str] = []
    snippet_lower = (snippet or "").lower()
    for entity in entities:
        name_lower = (entity.name or "").lower()
        in_section = section_id and entity.source_section == section_id
        by_name = snippet_lower and (name_lower in snippet_lower or snippet_lower in name_lower)
        if in_section or by_name:
            affected.append(entity.id)
    return list(dict.fromkeys(affected))


def _compact_risk_finding(finding: Dict[str, Any]) -> Dict[str, Any]:
    location = finding.get("location") or {}
    return {
        "id": finding.get("id"),
        "type": finding.get("type"),
        "severity": finding.get("severity"),
        "confidence": finding.get("confidence"),
        "file_path": finding.get("file_path"),
        "content_snippet": finding.get("content_snippet"),
        "suggestion": finding.get("suggestion", ""),
        "line_start": location.get("line_start"),
        "line_end": location.get("line_end"),
        "section_title": location.get("section_title"),
    }


def _format_location_text(location: Any) -> Optional[str]:
    if not location:
        return None
    if isinstance(location, str):
        return location
    if isinstance(location, dict):
        section = location.get("section_title", "")
        line_start = location.get("line_start")
        line_end = location.get("line_end")
        if line_start and line_end:
            return f"{section} (line {line_start}-{line_end})".strip()
        if line_start:
            return f"{section} (line {line_start})".strip()
        return section or None
    return str(location)


def _safe_node_id(prefix: str, raw_id: str) -> str:
    safe_part = re.sub(r"[^a-zA-Z0-9_:-]", "_", raw_id)
    return f"{prefix}:{safe_part}"


def _color_for_risk(level: str) -> str:
    colors = {
        "critical": "#dc2626",
        "high": "#ea580c",
        "medium": "#ca8a04",
        "low": "#16a34a",
        "safe": "#0284c7",
    }
    return colors.get((level or "").lower(), "#6b7280")


def _build_graph_view(
    parsed_files: List[Dict[str, Any]],
    entities: List[Any],
    relationships: List[Dict[str, Any]],
    risk_findings: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build an interpretable graph view with typed nodes and edges."""
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []
    added_nodes = set()
    added_edges = set()

    file_node_ids: Dict[str, str] = {}
    section_node_ids: Dict[Tuple[str, str], str] = {}

    for file_item in parsed_files:
        file_path = file_item["file_path"]
        file_node_id = _safe_node_id("file", file_path)
        file_node_ids[file_path] = file_node_id

        if file_node_id not in added_nodes:
            nodes.append(
                {
                    "id": file_node_id,
                    "label": file_path,
                    "node_type": "file",
                    "group": "file",
                    "shape": "box",
                    "color": "#2563eb",
                    "size": 28,
                    "file_path": file_path,
                    "title": f"File: {file_path}",
                }
            )
            added_nodes.add(file_node_id)

        for section in file_item.get("section_blocks", []):
            section_id = section.get("section_id", "section")
            section_node_id = _safe_node_id("section", f"{file_path}:{section_id}")
            section_node_ids[(file_path, section_id)] = section_node_id
            if section_node_id not in added_nodes:
                nodes.append(
                    {
                        "id": section_node_id,
                        "label": f"H{section.get('level', 1)} {section.get('section_title', 'Untitled')}",
                        "node_type": "section",
                        "group": "section",
                        "shape": "box",
                        "color": "#64748b",
                        "size": 20,
                        "file_path": file_path,
                        "section_id": section_id,
                        "line_start": section.get("line_start"),
                        "line_end": section.get("line_end"),
                        "content_block": section.get("content_preview", ""),
                        "title": f"Section: {section.get('section_title', 'Untitled')}",
                    }
                )
                added_nodes.add(section_node_id)

            edge_key = (file_node_id, section_node_id, "contains")
            if edge_key not in added_edges:
                edges.append(
                    {
                        "from": file_node_id,
                        "to": section_node_id,
                        "type": "contains",
                        "label": "contains",
                        "color": "#94a3b8",
                        "arrows": "to",
                    }
                )
                added_edges.add(edge_key)

    for entity in entities:
        entity_type = entity.type.value
        risk_level = _risk_level_from_score(entity.risk_score)
        file_path = (entity.properties or {}).get("file_path", "")
        section_id = entity.source_section or (entity.properties or {}).get("section_id", "")
        section_node_id = section_node_ids.get((file_path, section_id))

        if entity.id not in added_nodes:
            nodes.append(
                {
                    "id": entity.id,
                    "label": entity.name,
                    "node_type": "entity",
                    "group": f"entity_{entity_type}",
                    "shape": "dot",
                    "color": _color_for_risk(risk_level),
                    "size": 16 + int(entity.confidence * 8),
                    "risk_score": entity.risk_score,
                    "risk_level": risk_level,
                    "entity_type": entity_type,
                    "description": entity.description,
                    "file_path": file_path,
                    "section_id": section_id,
                    "section_title": (entity.properties or {}).get("section_title", ""),
                    "line_start": (entity.properties or {}).get("line_start"),
                    "line_end": (entity.properties or {}).get("line_end"),
                    "title": f"Entity ({entity_type}): {entity.name}",
                }
            )
            added_nodes.add(entity.id)

        parent_node_id = section_node_id or file_node_ids.get(file_path)
        if parent_node_id:
            edge_key = (parent_node_id, entity.id, "mentions")
            if edge_key not in added_edges:
                edges.append(
                    {
                        "from": parent_node_id,
                        "to": entity.id,
                        "type": "mentions",
                        "label": "mentions",
                        "color": "#cbd5e1",
                        "arrows": "to",
                    }
                )
                added_edges.add(edge_key)

    for rel in relationships:
        source_id = rel.get("source_id", "")
        target_id = rel.get("target_id", "")
        if not source_id or not target_id:
            continue
        if source_id not in added_nodes or target_id not in added_nodes:
            continue

        rel_type = rel.get("type", "related")
        edge_key = (source_id, target_id, rel_type)
        if edge_key in added_edges:
            continue

        edges.append(
            {
                "from": source_id,
                "to": target_id,
                "type": rel_type,
                "label": rel.get("relationship_label", _relationship_label(rel_type)),
                "color": "#475569",
                "width": max(1, int(float(rel.get("weight", 1.0)) * 2)),
                "arrows": "to",
                "confidence": rel.get("confidence", 0.0),
            }
        )
        added_edges.add(edge_key)

    for finding in risk_findings:
        risk_id = finding.get("id") or _safe_node_id("risk", f"{finding.get('type', 'risk')}:{finding.get('content_snippet', '')}")
        severity = finding.get("severity", "medium")
        location = finding.get("location") or {}
        file_path = finding.get("file_path", "")
        section_id = location.get("section_id", "")
        section_node_id = section_node_ids.get((file_path, section_id))
        file_node_id = file_node_ids.get(file_path)

        if risk_id not in added_nodes:
            nodes.append(
                {
                    "id": risk_id,
                    "label": f"{severity.upper()} · {finding.get('type', 'risk')}",
                    "node_type": "risk",
                    "group": "risk",
                    "shape": "diamond",
                    "color": _color_for_risk(severity),
                    "size": 26,
                    "severity": severity,
                    "description": finding.get("description", ""),
                    "content_snippet": finding.get("content_snippet", ""),
                    "suggestion": finding.get("suggestion", ""),
                    "file_path": file_path,
                    "section_id": section_id,
                    "section_title": location.get("section_title", ""),
                    "line_start": location.get("line_start"),
                    "line_end": location.get("line_end"),
                    "content_block": location.get("content_block", ""),
                    "title": f"Risk ({severity}): {finding.get('type', 'risk')}",
                }
            )
            added_nodes.add(risk_id)

        if section_node_id:
            edge_key = (section_node_id, risk_id, "has_risk")
            if edge_key not in added_edges:
                edges.append(
                    {
                        "from": section_node_id,
                        "to": risk_id,
                        "type": "has_risk",
                        "label": "has risk",
                        "color": _color_for_risk(severity),
                        "arrows": "to",
                    }
                )
                added_edges.add(edge_key)
        elif file_node_id:
            edge_key = (file_node_id, risk_id, "has_risk")
            if edge_key not in added_edges:
                edges.append(
                    {
                        "from": file_node_id,
                        "to": risk_id,
                        "type": "has_risk",
                        "label": "has risk",
                        "color": _color_for_risk(severity),
                        "arrows": "to",
                    }
                )
                added_edges.add(edge_key)

        for entity_id in finding.get("affected_entities", []):
            if entity_id not in added_nodes:
                continue
            edge_key = (risk_id, entity_id, "affects")
            if edge_key not in added_edges:
                edges.append(
                    {
                        "from": risk_id,
                        "to": entity_id,
                        "type": "affects",
                        "label": "affects",
                        "color": _color_for_risk(severity),
                        "arrows": "to",
                    }
                )
                added_edges.add(edge_key)

    legend = [
        {"label": "File", "node_type": "file", "color": "#2563eb", "shape": "box"},
        {"label": "Section", "node_type": "section", "color": "#64748b", "shape": "box"},
        {"label": "Entity", "node_type": "entity", "color": "#0284c7", "shape": "dot"},
        {"label": "Risk", "node_type": "risk", "color": "#dc2626", "shape": "diamond"},
    ]

    return {"nodes": nodes, "edges": edges, "legend": legend}


def _json_for_html_script(data: Any) -> str:
    """Serialize JSON safely for embedding in HTML script blocks."""
    text = json.dumps(data, ensure_ascii=False)
    return text.replace("</", "<\\/").replace("<", "\\u003c")


def _build_graph_html(graph_data: Dict[str, Any]) -> str:
    """Build interactive HTML graph with click-to-locate detail panel."""
    nodes_json = _json_for_html_script(graph_data.get("nodes", []))
    edges_json = _json_for_html_script(graph_data.get("edges", []))
    legend_json = _json_for_html_script(graph_data.get("legend", []))

    return (
        "<!DOCTYPE html>"
        "<html><head><meta charset='UTF-8'><title>SkillGraph View</title>"
        "<script src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>"
        "<style>"
        "body{margin:0;font-family:Arial,sans-serif;background:#f8fafc;color:#111827;}"
        ".layout{display:grid;grid-template-columns:2fr 1fr;height:760px;}"
        "#graph{height:100%;border-right:1px solid #e2e8f0;background:#fff;}"
        ".panel{padding:12px;overflow:auto;}"
        ".title{font-size:15px;font-weight:700;margin-bottom:8px;}"
        ".badge{display:inline-block;padding:2px 8px;border-radius:999px;background:#e2e8f0;font-size:12px;margin-right:6px;}"
        ".meta{font-size:12px;color:#475569;margin-top:8px;white-space:pre-wrap;}"
        "pre{background:#0f172a;color:#e2e8f0;padding:10px;border-radius:8px;white-space:pre-wrap;font-size:12px;}"
        "ul{padding-left:18px;}"
        "</style></head><body>"
        "<div class='layout'>"
        "<div id='graph'></div>"
        "<div class='panel'>"
        "<div class='title'>Node Details</div>"
        "<div id='detail'>Click a node to inspect file/section/risk details.</div>"
        "<hr/>"
        "<div class='title'>Legend</div>"
        "<ul id='legend'></ul>"
        "</div></div>"
        f"<script id='sg-nodes' type='application/json'>{nodes_json}</script>"
        f"<script id='sg-edges' type='application/json'>{edges_json}</script>"
        f"<script id='sg-legend' type='application/json'>{legend_json}</script>"
        "<script>"
        "const nodeData = JSON.parse(document.getElementById('sg-nodes').textContent || '[]');"
        "const edgeData = JSON.parse(document.getElementById('sg-edges').textContent || '[]');"
        "const legendData = JSON.parse(document.getElementById('sg-legend').textContent || '[]');"
        "const nodes = new vis.DataSet(nodeData);"
        "const edges = new vis.DataSet(edgeData.map((e)=>({from:e.from,to:e.to,label:e.label,color:e.color,width:e.width||1,arrows:e.arrows||'to'})));"
        "const container = document.getElementById('graph');"
        "const data = {nodes, edges};"
        "const options = {"
        "  layout:{improvedLayout:true},"
        "  physics:{enabled:true, stabilization:{iterations:120}},"
        "  interaction:{hover:true, navigationButtons:true, keyboard:true},"
        "  nodes:{font:{size:12}, borderWidth:1},"
        "  edges:{smooth:{type:'dynamic'}, font:{align:'middle', size:10}}"
        "};"
        "const network = new vis.Network(container, data, options);"
        "function esc(v){if(v===null||v===undefined){return '';} return String(v)"
        ".replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');}"
        "function renderDetail(node){"
        " let html = `<div><span class='badge'>${esc(node.node_type||node.group||'node')}</span>`;"
        " if(node.severity){ html += `<span class='badge'>${esc(node.severity)}</span>`;}"
        " html += `</div><div class='title'>${esc(node.label||node.id)}</div>`;"
        " if(node.description){ html += `<div class='meta'><b>Description:</b> ${esc(node.description)}</div>`;}"
        " if(node.relationship_label){ html += `<div class='meta'><b>Relation:</b> ${esc(node.relationship_label)}</div>`;}"
        " if(node.file_path){ html += `<div class='meta'><b>File:</b> ${esc(node.file_path)}</div>`;}"
        " if(node.section_title){ html += `<div class='meta'><b>Section:</b> ${esc(node.section_title)}</div>`;}"
        " if(node.line_start){ html += `<div class='meta'><b>Lines:</b> ${esc(node.line_start)}-${esc(node.line_end||node.line_start)}</div>`;}"
        " if(node.suggestion){ html += `<div class='meta'><b>Suggestion:</b> ${esc(node.suggestion)}</div>`;}"
        " if(node.content_snippet){ html += `<div class='meta'><b>Snippet:</b> ${esc(node.content_snippet)}</div>`;}"
        " if(node.content_block){ html += `<pre>${esc(node.content_block)}</pre>`;}"
        " document.getElementById('detail').innerHTML = html;"
        "}"
        "network.on('click', function(params){"
        " if(params.nodes.length){ const id=params.nodes[0]; const node=nodes.get(id); if(node){ renderDetail(node); } }"
        "});"
        "const legendEl = document.getElementById('legend');"
        "legendData.forEach((item)=>{"
        "  const li=document.createElement('li');"
        "  li.innerHTML = `<span class='badge' style='background:${item.color};color:#fff'>${item.shape}</span> ${esc(item.label)}`;"
        "  legendEl.appendChild(li);"
        "});"
        "</script></body></html>"
    )
