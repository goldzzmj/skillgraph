"""Streamlit frontend for SkillGraph FastAPI endpoints."""

from __future__ import annotations

import datetime as dt
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests
import streamlit as st
import streamlit.components.v1 as components

from skillgraph.parser import SkillParser
from skillgraph.rules import RiskDetector


RISK_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "safe": 4,
}


def create_app() -> None:
    """Create and render Streamlit app."""
    st.set_page_config(
        page_title="SkillGraph Studio",
        page_icon="🔍",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    _inject_styles()

    st.markdown("<h1 class='sg-title'>SkillGraph Studio</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p class='sg-subtitle'>"
        "Upload skills, inspect security graph, locate risky blocks, and export remediation markdown."
        "</p>",
        unsafe_allow_html=True,
    )

    if "latest_result" not in st.session_state:
        st.session_state.latest_result = None

    with st.sidebar:
        st.markdown("### API Settings")
        api_base = st.text_input("FastAPI Base URL", value="http://127.0.0.1:8000")
        include_graph = st.checkbox("Include graph", value=True)
        use_graphrag = st.checkbox("Use GraphRAG extraction", value=True)
        include_community_detection = st.checkbox("Community detection", value=True)
        st.caption("Tip: Keep `include_graph=true` to enable preview endpoint and node-level tracing.")

    left_col, right_col = st.columns([1.0, 1.35], gap="large")

    with left_col:
        st.markdown("## Input")
        input_mode = st.radio(
            "Upload mode",
            ["Drag or upload files", "Upload folder zip", "Paste markdown", "Analyze from URL"],
            horizontal=True,
        )

        run_analysis = False
        markdown_input = ""
        markdown_filename = "pasted_skill.md"
        uploaded_files: List[Any] = []
        uploaded_zip = None
        skill_url = ""

        if input_mode == "Drag or upload files":
            uploaded_files = st.file_uploader(
                "Drop markdown files here",
                type=["md", "markdown", "mkd", "txt"],
                accept_multiple_files=True,
                help="Supports nested skill files exported by your editor.",
            )
            run_analysis = st.button("Analyze uploaded files", type="primary", use_container_width=True)

        elif input_mode == "Upload folder zip":
            uploaded_zip = st.file_uploader(
                "Upload ZIP",
                type=["zip"],
                help="Zip the entire skill folder and upload here.",
            )
            run_analysis = st.button("Analyze ZIP folder", type="primary", use_container_width=True)

        else:
            if input_mode == "Paste markdown":
                markdown_filename = st.text_input("Virtual file name", value="pasted_skill.md")
                markdown_input = st.text_area(
                    "Paste markdown content",
                    height=360,
                    placeholder="# Skill\nDescribe skill behavior here...",
                )
                run_analysis = st.button("Analyze markdown text", type="primary", use_container_width=True)
            else:
                skill_url = st.text_input(
                    "Skill URL",
                    placeholder="https://raw.githubusercontent.com/.../SKILL.md or GitHub tree URL",
                )
                st.caption("Supports markdown URL, zip URL, GitHub blob URL, and GitHub tree URL.")
                run_analysis = st.button("Analyze from URL", type="primary", use_container_width=True)

        if run_analysis:
            with st.spinner("Analyzing with FastAPI..."):
                try:
                    result = _run_analysis(
                        api_base=api_base,
                        input_mode=input_mode,
                        uploaded_files=uploaded_files,
                        uploaded_zip=uploaded_zip,
                        markdown_input=markdown_input,
                        markdown_filename=markdown_filename,
                        skill_url=skill_url,
                        include_graph=include_graph,
                        use_graphrag=use_graphrag,
                        include_community_detection=include_community_detection,
                    )
                    st.session_state.latest_result = result
                    st.success("Analysis completed")
                except Exception as exc:
                    st.error(f"Analysis failed: {exc}")

        latest_result = st.session_state.latest_result
        if latest_result:
            st.markdown("## Summary")
            st.json(
                {
                    "scan_id": latest_result.get("scan_id"),
                    "scan_status": latest_result.get("scan_status"),
                    "input_files": latest_result.get("input_files", 1),
                    "processing_time": latest_result.get("processing_time"),
                }
            )

            per_file = latest_result.get("per_file_results", [])
            if per_file:
                st.markdown("#### Per-file risk overview")
                st.dataframe(per_file, use_container_width=True)

    with right_col:
        st.markdown("## Graph & Risk Insights")

        latest_result = st.session_state.latest_result
        if not latest_result:
            st.info("Run analysis to view graph, findings, and remediation report.")
            return

        _render_score_panel(latest_result)

        tab_graph, tab_findings, tab_report, tab_json = st.tabs(
            ["Graph", "Findings", "Remediation Markdown", "Raw JSON"]
        )

        with tab_graph:
            graph = latest_result.get("graph") or {}
            graph_html = graph.get("html")
            if graph_html:
                st.caption("Click a node to inspect file path, section, line range, and suggestions.")
                components.html(graph_html, height=780, scrolling=True)

                preview_path = latest_result.get("graph_preview_url")
                if preview_path:
                    preview_url = preview_path
                    if preview_url.startswith("/"):
                        preview_url = f"{api_base.rstrip('/')}{preview_url}"
                    st.link_button("Open graph preview endpoint", preview_url, use_container_width=True)
            else:
                st.warning("No graph generated. Enable graph in sidebar and rerun analysis.")

        with tab_findings:
            _render_findings(latest_result)

        with tab_report:
            _render_remediation_export(latest_result)

        with tab_json:
            st.json(latest_result)


def _inject_styles() -> None:
    """Inject custom page styles."""
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at top left, #e0f2fe 0%, #f8fafc 35%, #ffffff 100%);
        }
        .sg-title {
            margin-bottom: 0.2rem;
            font-size: 2.4rem;
            letter-spacing: -0.02em;
        }
        .sg-subtitle {
            margin-top: 0;
            color: #475569;
            font-size: 1.02rem;
        }
        .sg-card {
            border: 1px solid #e2e8f0;
            border-radius: 14px;
            background: linear-gradient(180deg, #ffffff 0%, #f8fafc 100%);
            padding: 0.8rem 1rem;
            margin-bottom: 0.7rem;
        }
        .sg-chip {
            display: inline-block;
            border-radius: 999px;
            padding: 2px 10px;
            font-size: 12px;
            margin-right: 8px;
            border: 1px solid #cbd5e1;
            background: #f8fafc;
            color: #334155;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_score_panel(result: Dict[str, Any]) -> None:
    """Render top metrics for overall risk."""
    summary = result.get("risk_summary", {})
    severity = summary.get("overall_risk_level", "unknown")
    score = summary.get("overall_risk_score", summary.get("avg_risk_score", 0.0))
    findings = summary.get("total_risk_findings", 0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Overall Risk", str(severity).upper())
    with col2:
        st.metric("Risk Score", score)
    with col3:
        st.metric("Findings", findings)

    dist = summary.get("severity_distribution") or {}
    if dist:
        st.markdown(
            "<div class='sg-card'>"
            f"<span class='sg-chip'>CRITICAL {dist.get('critical', 0)}</span>"
            f"<span class='sg-chip'>HIGH {dist.get('high', 0)}</span>"
            f"<span class='sg-chip'>MEDIUM {dist.get('medium', 0)}</span>"
            f"<span class='sg-chip'>LOW {dist.get('low', 0)}</span>"
            "</div>",
            unsafe_allow_html=True,
        )


def _render_findings(result: Dict[str, Any]) -> None:
    """Render findings with location and suggestions."""
    findings = result.get("risk_findings", [])
    if not findings:
        st.success("No risky findings detected.")
        return

    sorted_findings = sorted(
        findings,
        key=lambda item: RISK_ORDER.get(str(item.get("severity", "safe")).lower(), 99),
    )

    for item in sorted_findings:
        severity = str(item.get("severity", "unknown")).upper()
        title = f"{severity} · {item.get('type', 'risk')}"
        with st.expander(title, expanded=False):
            st.markdown(f"**Description:** {item.get('description') or item.get('content_snippet') or ''}")
            location = item.get("location") or {}

            # /scan endpoint may return location as string, upload mode returns dict.
            if isinstance(location, dict):
                st.write(
                    {
                        "file_path": item.get("file_path"),
                        "section_title": location.get("section_title"),
                        "line_start": location.get("line_start"),
                        "line_end": location.get("line_end"),
                        "confidence": item.get("confidence"),
                    }
                )
                content_block = location.get("content_block")
            else:
                st.write({"file_path": item.get("file_path"), "location": location, "confidence": item.get("confidence")})
                content_block = None

            if item.get("suggestion"):
                st.info(item["suggestion"])
            if content_block:
                st.code(content_block, language="markdown")


def _render_remediation_export(result: Dict[str, Any]) -> None:
    """Render remediation markdown export section."""
    summary = result.get("risk_summary", {})
    risk_level = str(summary.get("overall_risk_level", "safe")).lower()

    if RISK_ORDER.get(risk_level, 99) > RISK_ORDER["medium"]:
        st.success("Overall risk is low/safe. Remediation markdown export is not required.")
        return

    report_md = _build_remediation_markdown(result)
    st.warning("Medium/High risk detected. Export the remediation markdown and feed it to your AI workflow.")
    st.text_area("Remediation Markdown Preview", value=report_md, height=420)

    scan_id = result.get("scan_id", "scan")
    st.download_button(
        label="Download remediation markdown",
        data=report_md,
        file_name=f"skill-remediation-{scan_id}.md",
        mime="text/markdown",
        use_container_width=True,
    )


def _build_remediation_markdown(result: Dict[str, Any]) -> str:
    """Generate markdown remediation guide for medium/high risk skills."""
    summary = result.get("risk_summary", {})
    findings = result.get("risk_findings", [])
    per_file = result.get("per_file_results", [])
    recommendations = result.get("recommendations", [])
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines: List[str] = []
    lines.append("# Skill Remediation Plan")
    lines.append("")
    lines.append(f"- Generated at: {now}")
    lines.append(f"- Scan ID: {result.get('scan_id')}")
    lines.append(f"- Overall Risk Level: {summary.get('overall_risk_level', 'unknown')}")
    lines.append(f"- Overall Risk Score: {summary.get('overall_risk_score', summary.get('avg_risk_score', 0.0))}")
    lines.append(f"- Total Findings: {summary.get('total_risk_findings', len(findings))}")
    lines.append("")

    lines.append("## Prioritized Fix Strategy")
    lines.append("1. Remove or rewrite high-risk instructions first (credentials, destructive commands, uncontrolled network calls).")
    lines.append("2. Add explicit permission boundaries and trusted-path allowlists.")
    lines.append("3. Keep skill behavior deterministic: avoid hidden side effects and implicit data exfiltration.")
    lines.append("4. Re-run scan until overall risk is low/safe.")
    lines.append("")

    if per_file:
        lines.append("## File Risk Overview")
        lines.append("| File | Risk Level | Risk Score | Findings |")
        lines.append("| --- | --- | ---: | ---: |")
        for item in per_file:
            lines.append(
                f"| {item.get('file_path','')} | {item.get('risk_level','')} | {item.get('risk_score','')} | {item.get('risk_findings','')} |"
            )
        lines.append("")

    lines.append("## Required Modifications")
    grouped = _group_findings_by_file(findings)
    for file_path, file_findings in grouped.items():
        lines.append(f"### {file_path}")
        for idx, finding in enumerate(file_findings, start=1):
            location = finding.get("location") or {}
            if isinstance(location, dict):
                loc_text = f"{location.get('section_title', 'N/A')} ({location.get('line_start', '?')}-{location.get('line_end', '?')})"
                block_text = location.get("content_block", "")
            else:
                loc_text = str(location or "N/A")
                block_text = ""

            lines.append(f"{idx}. **[{str(finding.get('severity','unknown')).upper()}] {finding.get('type','risk')}**")
            lines.append(f"   - Current content: `{finding.get('content_snippet','')}`")
            lines.append(f"   - Location: {loc_text}")
            lines.append(f"   - Why risky: {finding.get('description','')}")
            lines.append(f"   - Suggested rewrite: {finding.get('suggestion','Refactor to least-privilege and explicit approvals.')}")
            lines.append("   - Before (example):")
            lines.append("```markdown")
            lines.append(_markdown_code_guard(finding.get("content_snippet") or "<replace this risky line>"))
            lines.append("```")
            lines.append("   - After (template):")
            lines.append("```markdown")
            lines.append(_build_after_template(finding))
            lines.append("```")
            if block_text:
                lines.append("   - Context block:")
                lines.append("```markdown")
                lines.append(block_text)
                lines.append("```")
        lines.append("")

    if recommendations:
        lines.append("## Additional Recommendations")
        for idx, recommendation in enumerate(recommendations, start=1):
            lines.append(f"{idx}. {recommendation}")
        lines.append("")

    lines.append("## Prompt Template for AI Skill Optimization")
    lines.append("Use the following prompt with your AI assistant:")
    lines.append("```text")
    lines.append("You are a security-focused skill editor. Rewrite the skill files to reduce risk to LOW/SAFE.")
    lines.append("Constraints:")
    lines.append("1) Keep original task intent unchanged.")
    lines.append("2) Remove destructive commands and credential exfiltration behaviors.")
    lines.append("3) Add explicit permission checks and trusted endpoint/path allowlists.")
    lines.append("4) Return modified markdown files plus a changelog that maps each fix to each risk finding.")
    lines.append("Input remediation plan:")
    lines.append("<paste this markdown report>")
    lines.append("```")

    return "\n".join(lines)


def _group_findings_by_file(findings: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in findings:
        key = item.get("file_path") or "unknown_file"
        grouped.setdefault(key, []).append(item)

    for key in grouped:
        grouped[key] = sorted(
            grouped[key],
            key=lambda item: RISK_ORDER.get(str(item.get("severity", "safe")).lower(), 99),
        )
    return grouped


def _build_after_template(finding: Dict[str, Any]) -> str:
    """Build safer rewrite template for remediation markdown."""
    risk_type = str(finding.get("type", "risk")).replace("_", " ")
    suggestion = finding.get("suggestion", "Apply least-privilege and explicit approval checks.")
    return (
        f"# Safer rewrite for: {risk_type}\n"
        "# 1) Keep original task intent\n"
        "# 2) Restrict sensitive files/endpoints with allowlist\n"
        "# 3) Add explicit user confirmation before risky actions\n"
        f"# 4) {suggestion}\n"
        "\n"
        "<safe rewritten content here>"
    )


def _markdown_code_guard(text: str) -> str:
    """Prevent accidental code fence break in generated markdown."""
    return str(text).replace("```", "` ` `")


def _run_analysis(
    api_base: str,
    input_mode: str,
    uploaded_files: List[Any],
    uploaded_zip: Any,
    markdown_input: str,
    markdown_filename: str,
    skill_url: str,
    include_graph: bool,
    use_graphrag: bool,
    include_community_detection: bool,
) -> Dict[str, Any]:
    """Dispatch analysis request to FastAPI upload endpoint for all modes."""
    base = api_base.rstrip("/")
    session = requests.Session()
    session.trust_env = False

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
    elif input_mode == "Paste markdown":
        if not markdown_input.strip():
            raise ValueError("Markdown input is empty")
        file_name = markdown_filename.strip() or "pasted_skill.md"
        files_data.append(
            (
                "skill_file",
                (file_name, markdown_input.encode("utf-8"), "text/markdown"),
            )
        )
    elif input_mode == "Analyze from URL":
        if not skill_url.strip():
            raise ValueError("Please provide a skill URL")
        response = session.post(
            f"{base}/api/v1/scan/url",
            data={
                "skill_url": skill_url.strip(),
                "include_graph": str(include_graph).lower(),
                "use_graphrag": str(use_graphrag).lower(),
                "include_community_detection": str(include_community_detection).lower(),
            },
            timeout=300,
        )
        _raise_for_status(response)
        return response.json()
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
        timeout=300,
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
