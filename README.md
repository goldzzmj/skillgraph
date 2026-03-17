# SkillGraph

SkillGraph is an AI agent skill security analysis platform with FastAPI + Streamlit.

- 中文文档: `README_ZH.md`
- English docs: `README_EN.md`

## Quick Start

```bash
pip install -r requirements.txt
uvicorn skillgraph.api.main:app --host 0.0.0.0 --port 8000
streamlit run src/skillgraph/viz/app.py
```

- API docs: `http://localhost:8000/docs`
- Streamlit: `http://localhost:8501`

## Key Capabilities

- Upload skill files, ZIP folders, pasted markdown, or skill URLs
- Build interpretable relationship graph (file/section/entity/risk)
- Click nodes to locate risky content blocks and suggestions
- Export remediation markdown for medium/high risk skills (includes before/after rewrite templates)
- Open graph preview endpoint directly from scan results

## Useful Endpoints

- `POST /api/v1/scan/upload`
- `POST /api/v1/scan/url`
- `GET /api/v1/scan/upload/preview?scan_id=<scan_id>`

## Repository Structure

- User-facing docs are kept in `README.md`, `README_EN.md`, and `README_ZH.md`.
- Process/progress/research markdown files are organized under `docs/process/`.

## Security Note

Never commit secrets (API keys, tokens, private keys, `.env`) into this repository.
