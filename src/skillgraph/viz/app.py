"""Streamlit frontend for SkillGraph FastAPI endpoints."""

from __future__ import annotations

import io
import zipfile
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
import streamlit.components.v1 as components

from skillgraph.parser import SkillParser
from skillgraph.rules import RiskDetector


def create_app() -> None:
    """Create and render Streamlit app."""
    st.set_page_config(
        page_title="SkillGraph Studio",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("🔍 SkillGraph Studio")
    st.caption("Upload files / folder zip / markdown text, then inspect graph + security analysis.")

    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None

    with st.sidebar:
        st.header("API Settings")
        api_base = st.text_input("FastAPI Base URL", value="http://127.0.0.1:8000")
        include_graph = st.checkbox("Include graph", value=True)
        use_graphrag = st.checkbox("Use GraphRAG extraction", value=True)
        include_community_detection = st.checkbox("Community detection", value=True)

    input_col, output_col = st.columns([1, 1.25])

    with input_col:
        st.subheader("Input")
        input_mode = st.radio(
            "Choose upload mode",
            [
                "Drag or upload files",
                "Upload folder zip",
                "Paste markdown",
            ],
        )

        run_analysis = False
        markdown_input = ""
        uploaded_files: List[Any] = []
        uploaded_zip = None

        if input_mode == "Drag or upload files":
            uploaded_files = st.file_uploader(
                "Drop markdown files here",
                type=["md", "markdown", "mkd", "txt"],
                accept_multiple_files=True,
            )
            run_analysis = st.button("Analyze uploaded files", type="primary")

        elif input_mode == "Upload folder zip":
            uploaded_zip = st.file_uploader("Upload folder ZIP", type=["zip"])
            run_analysis = st.button("Analyze ZIP folder", type="primary")

        else:
            markdown_input = st.text_area(
                "Paste markdown content",
                height=360,
                placeholder="# Skill\nDescribe skill behavior here...",
            )
            run_analysis = st.button("Analyze markdown text", type="primary")

        if run_analysis:
            with st.spinner("Analyzing..."):
                try:
                    result = _run_analysis(
                        api_base=api_base,
                        input_mode=input_mode,
                        uploaded_files=uploaded_files,
                        uploaded_zip=uploaded_zip,
                        markdown_input=markdown_input,
                        include_graph=include_graph,
                        use_graphrag=use_graphrag,
                        include_community_detection=include_community_detection,
                    )
                    st.session_state.latest_result = result
                    st.success("Analysis finished")
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")

        latest_result = st.session_state.latest_result
        if latest_result:
            st.subheader("Upload Summary")
            st.json(
                {
                    "scan_id": latest_result.get("scan_id"),
                    "status": latest_result.get("scan_status"),
                    "input_files": latest_result.get("input_files", 1),
                    "processing_time": latest_result.get("processing_time"),
                }
            )

            per_file = latest_result.get("per_file_results", [])
            if per_file:
                st.markdown("#### Per-file Risk")
                st.dataframe(per_file, use_container_width=True)

    with output_col:
        st.subheader("Graph & Security")

        latest_result = st.session_state.latest_result
        if not latest_result:
            st.info("Run analysis to view graph, score, and remediation suggestions.")
            return

        _render_score_sidebar(latest_result)

        graph = latest_result.get("graph") or {}
        graph_html = graph.get("html")
        if graph_html:
            st.markdown("#### Interactive Relationship Graph")
            st.caption("Click any node to locate related content block and remediation suggestions.")
            components.html(graph_html, height=780, scrolling=True)

        preview_scan_id = latest_result.get("scan_id", "")
        if preview_scan_id:
            preview_url = f"{api_base.rstrip('/')}/api/v1/scan/upload/preview?scan_id={preview_scan_id}"
            st.link_button("Open graph preview endpoint", preview_url)

        findings = latest_result.get("risk_findings", [])
        st.markdown("#### Risk Findings")
        if not findings:
            st.success("No risky findings detected.")
        else:
            for item in findings:
                severity = (item.get("severity") or "unknown").upper()
                title = f"{severity} · {item.get('type', 'risk')}"
                with st.expander(title, expanded=False):
                    st.write(item.get("description") or item.get("content_snippet") or "")
                    location = item.get("location") or {}
                    st.write(
                        {
                            "file_path": item.get("file_path"),
                            "section_title": location.get("section_title"),
                            "line_start": location.get("line_start"),
                            "line_end": location.get("line_end"),
                            "confidence": item.get("confidence"),
                        }
                    )
                    if item.get("suggestion"):
                        st.info(item["suggestion"])
                    block = location.get("content_block")
                    if block:
                        st.code(block, language="markdown")

        recommendations = latest_result.get("recommendations", [])
        st.markdown("#### Recommendations")
        if recommendations:
            for idx, text in enumerate(recommendations, start=1):
                st.markdown(f"{idx}. {text}")
        else:
            st.write("No additional recommendations.")


def _render_score_sidebar(result: Dict[str, Any]) -> None:
    """Render risk score summary in Streamlit sidebar."""
    summary = result.get("risk_summary", {})
    with st.sidebar:
        st.header("Security Score")
        st.metric("Overall Risk Level", str(summary.get("overall_risk_level", "unknown")).upper())
        st.metric("Overall Risk Score", summary.get("overall_risk_score", summary.get("avg_risk_score", 0.0)))
        st.metric("Findings", summary.get("total_risk_findings", 0))

        severity_distribution = summary.get("severity_distribution", {})
        if severity_distribution:
            st.markdown("#### Severity distribution")
            st.json(severity_distribution)


def _run_analysis(
    api_base: str,
    input_mode: str,
    uploaded_files: List[Any],
    uploaded_zip: Any,
    markdown_input: str,
    include_graph: bool,
    use_graphrag: bool,
    include_community_detection: bool,
) -> Dict[str, Any]:
    """Dispatch analysis request to FastAPI."""
    base = api_base.rstrip("/")
    session = requests.Session()
    session.trust_env = False

    if input_mode == "Paste markdown":
        if not markdown_input.strip():
            raise ValueError("Markdown input is empty")

        payload = {
            "skill_content": markdown_input,
            "skill_name": "pasted_markdown",
            "scan_options": {
                "use_graphrag": use_graphrag,
                "include_community_detection": include_community_detection,
            },
        }
        response = session.post(f"{base}/api/v1/scan", json=payload, timeout=180)
        _raise_for_status(response)
        scan_result = response.json()

        # Convert /scan response shape to align with upload UI.
        return {
            "scan_id": scan_result.get("scan_id"),
            "scan_status": scan_result.get("scan_status"),
            "processing_time": scan_result.get("processing_time"),
            "input_files": 1,
            "per_file_results": [
                {
                    "file_path": scan_result.get("skill_name") or "pasted_markdown",
                    "risk_level": (scan_result.get("risk_summary") or {}).get("overall_risk_level", "unknown"),
                    "risk_score": (scan_result.get("risk_summary") or {}).get("overall_risk_score", 0),
                    "entities": len(scan_result.get("entities") or []),
                    "relationships": len(scan_result.get("relationships") or []),
                    "risk_findings": len(scan_result.get("risk_findings") or []),
                    "sections": None,
                }
            ],
            "risk_summary": scan_result.get("risk_summary", {}),
            "entities": scan_result.get("entities", []),
            "relationships": scan_result.get("relationships", []),
            "risk_findings": scan_result.get("risk_findings", []),
            "recommendations": scan_result.get("recommendations", []),
            "graph": None,
        }

    files_data: List[Tuple[str, Tuple[str, bytes, str]]] = []
    form_data = {
        "include_graph": str(include_graph).lower(),
        "use_graphrag": str(use_graphrag).lower(),
        "include_community_detection": str(include_community_detection).lower(),
    }

    if input_mode == "Upload folder zip":
        if uploaded_zip is None:
            raise ValueError("Please upload a ZIP file first")
        files_data.append(
            (
                "skill_folder_zip",
                (uploaded_zip.name or "skills.zip", uploaded_zip.getvalue(), "application/zip"),
            )
        )
    else:
        if not uploaded_files:
            raise ValueError("Please upload at least one markdown file")
        for file_item in uploaded_files:
            files_data.append(
                (
                    "skill_files",
                    (file_item.name, file_item.getvalue(), "text/markdown"),
                )
            )

    response = session.post(
        f"{base}/api/v1/scan/upload",
        files=files_data,
        data=form_data,
        timeout=240,
    )
    _raise_for_status(response)
    return response.json()


def _raise_for_status(response: requests.Response) -> None:
    """Raise concise error with backend detail."""
    if response.status_code < 400:
        return
    try:
        detail = response.json().get("detail", response.text)
    except Exception:
        detail = response.text
    raise RuntimeError(f"HTTP {response.status_code}: {detail}")


# ---------------------------------------------------------------------------
# Compatibility helpers retained for existing tests.
# ---------------------------------------------------------------------------

def process_zip_upload(uploaded_zip, parser: SkillParser, detector: RiskDetector) -> List[Tuple[str, str, Any, List[Any]]]:
    """Process a ZIP file containing markdown skill files."""
    skills_data: List[Tuple[str, str, Any, List[Any]]] = []

    with tempfile.TemporaryDirectory() as temp_dir:
        zip_path = Path(temp_dir) / "upload.zip"
        zip_bytes = uploaded_zip.getvalue() if hasattr(uploaded_zip, "getvalue") else uploaded_zip.read()
        zip_path.write_bytes(zip_bytes)

        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
        except zipfile.BadZipFile:
            st.error("Uploaded file is not a valid ZIP archive.")
            return []

        markdown_suffixes = {".md", ".markdown", ".mdown", ".mkd", ".txt"}
        for md_file in Path(temp_dir).rglob("*"):
            if not md_file.is_file() or md_file.suffix.lower() not in markdown_suffixes:
                continue
            try:
                content = md_file.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                content = md_file.read_text(encoding="utf-8", errors="replace")

            if len(content.strip()) <= 50:
                continue

            try:
                parsed, findings = analyze_skill(content, parser, detector)
                relative_name = md_file.relative_to(Path(temp_dir)).as_posix()
                skills_data.append((relative_name, content, parsed, findings))
            except Exception as exc:
                st.warning(f"Could not parse {md_file.name}: {exc}")

    return skills_data


def analyze_skill(content: str, parser: SkillParser, detector: RiskDetector) -> Tuple[Any, List[Any]]:
    """Analyze a single skill string with local parser and detector."""
    try:
        parsed = parser.parse(content)
        findings = detector.detect(parsed)
        return parsed, findings
    except Exception:
        from skillgraph.parser import ParsedSkill

        return ParsedSkill(name="Error"), []


def run_app(port: int = 8501) -> None:
    """Run streamlit app."""
    import subprocess
    import sys

    subprocess.run(
        [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            __file__,
            "--server.port",
            str(port),
        ]
    )


if __name__ == "__main__":
    create_app()
