# SkillGraph（中文）

SkillGraph 用于分析 AI Agent Skills 的安全风险，并以可解释关系图谱进行可视化。

## 启动方式

```bash
pip install -r requirements.txt
uvicorn skillgraph.api.main:app --host 0.0.0.0 --port 8000
streamlit run src/skillgraph/viz/app.py
```

- API 文档：`http://localhost:8000/docs`
- Streamlit 前端：`http://localhost:8501`

## 主要能力

- 支持输入：多文件上传、ZIP 文件夹上传、粘贴 Markdown、Skills URL 解析
- 关系图谱：按 `file / section / entity / risk` 节点类型展示
- 节点定位：点击节点查看文件路径、段落、行号和上下文内容块
- 风险分析：展示风险等级、发现详情与修复建议
- 整改导出：当风险为 `medium/high/critical` 时，可导出整改 Markdown 文档
  - 包含 before/after 改写模板，便于后续交给 AI 进行 skill 优化
- 图谱预览：可直接打开预览接口
  - `GET /api/v1/scan/upload/preview?scan_id=<scan_id>`

## 常用接口

- `POST /api/v1/scan/upload`
- `POST /api/v1/scan/url`
- `GET /api/v1/scan/upload/preview`
- `POST /api/v1/scan`
- `POST /api/v1/predict`
- `POST /api/v1/batch`
- `POST /api/v1/graph/graph/operations/extract`

## LLM 配置（OpenAI 兼容，如 glm-5）

请使用环境变量，不要把密钥提交到仓库：

```bash
set OPENAI_API_KEY=<your_api_key>
set OPENAI_MODEL=glm-5
set OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

Linux/macOS：

```bash
export OPENAI_API_KEY=<your_api_key>
export OPENAI_MODEL=glm-5
export OPENAI_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
```

## 测试

```bash
pytest tests/test_viz_zip_upload.py tests/test_simple.py -q
```

## 文档说明

- 对外文档：`README.md`、`README_EN.md`、`README_ZH.md`
- 过程/阶段/研究类 Markdown 文档已整理到 `docs/process/`
