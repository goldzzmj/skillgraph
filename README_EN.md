# SkillGraph (English)

SkillGraph helps you analyze AI agent skills for security risks and visualize relationships with a graph.

## Start Services

```bash
pip install -r requirements.txt
uvicorn skillgraph.api.main:app --host 0.0.0.0 --port 8000
streamlit run src/skillgraph/viz/app.py
```

- API docs: `http://localhost:8000/docs`
- Streamlit UI: `http://localhost:8501`

## What You Can Do

- Upload markdown files, ZIP folders, or paste markdown text
- Build an interpretable graph with typed nodes:
  - `file`, `section`, `entity`, `risk`
- Inspect node details (file path, section, line range, content block)
- View risk findings and remediation suggestions
- Export a remediation markdown report when risk is `medium/high/critical`
- Open graph preview endpoint directly:
  - `GET /api/v1/scan/upload/preview?scan_id=<scan_id>`

## Core Endpoints

- `POST /api/v1/scan/upload`
- `GET /api/v1/scan/upload/preview`
- `POST /api/v1/scan`
- `POST /api/v1/predict`
- `POST /api/v1/batch`
- `POST /api/v1/graph/graph/operations/extract`

## LLM Configuration (OpenAI-compatible, e.g. glm-5)

Use environment variables (do not hardcode secrets):

```bash
export OPENAI_API_KEY=<your_api_key>
export OPENAI_MODEL=glm-5
export OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

Windows:

```bash
set OPENAI_API_KEY=<your_api_key>
set OPENAI_MODEL=glm-5
set OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

## Test

```bash
pytest tests/test_viz_zip_upload.py tests/test_simple.py -q
```
