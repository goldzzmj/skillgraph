# SkillGraph

SkillGraph 是一个面向 AI Agent Skills 的安全分析与关系图谱平台。  
它提供 FastAPI 接口与 Streamlit 前端，支持从 Markdown 技能文件中提取实体、关系、风险，并可视化展示可追踪的图谱。

## 快速开始

### 1) 安装依赖

```bash
pip install -r requirements.txt
```

### 2) 启动 FastAPI

```bash
uvicorn skillgraph.api.main:app --host 0.0.0.0 --port 8000
```

- API 文档：`http://localhost:8000/docs`
- 健康检查：`http://localhost:8000/health`

### 3) 启动 Streamlit 前端

```bash
streamlit run src/skillgraph/viz/app.py
```

- 默认地址：`http://localhost:8501`

## 核心能力

- 多输入方式：拖拽/上传多个 markdown 文件、上传 ZIP 文件夹、粘贴 markdown 文本
- 风险分析：输出风险等级、风险分布、风险建议
- 图谱可视化：文件/章节/实体/风险多类型节点 + 语义边
- 定位能力：点击图谱节点可查看文件路径、段落、行号、内容块与建议
- LLM 操作流提取：支持通过 OpenAI 兼容接口提取操作与关系（可配置 `glm-5`）

## API 速览

### 扫描与可视化

- `POST /api/v1/scan`：扫描单段 markdown
- `POST /api/v1/scan/upload`：上传文件/文件夹 ZIP 进行扫描并返回图谱
- `GET /api/v1/scan/upload/preview`：返回某次上传扫描的可访问 HTML 图谱

### 图谱操作

- `POST /api/v1/graph/nodes/entity`
- `POST /api/v1/graph/nodes/operation`
- `POST /api/v1/graph/edges/dependency`
- `GET /api/v1/graph/nodes`
- `GET /api/v1/graph/edges`
- `POST /api/v1/graph/graph/operations/extract`

### 其他

- `POST /api/v1/predict`
- `POST /api/v1/batch`

## 常用调用示例

### 1) 上传 ZIP 文件夹扫描

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/scan/upload" \
  -F "skill_folder_zip=@C:/path/skills.zip" \
  -F "include_graph=true"
```

### 2) 打开图谱预览

```bash
http://127.0.0.1:8000/api/v1/scan/upload/preview?scan_id=<scan_id>
```

### 3) LLM 操作流提取（OpenAI 兼容）

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/graph/graph/operations/extract" \
  --get \
  --data-urlencode "skill_content=# demo skill" \
  --data-urlencode "create_nodes=false"
```

## LLM 配置（支持 glm-5）

请通过环境变量配置，不要把密钥写入代码或提交到仓库：

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

接口也支持覆盖参数：

- `llm_model`
- `llm_base_url`

## 开发与测试

```bash
pytest -q
```

推荐至少执行：

```bash
pytest tests/test_viz_zip_upload.py tests/test_simple.py -q
```

## 安全说明

- 不要将 API Key、Token、私钥、`.env` 等敏感信息提交到 Git
- 如密钥有泄露风险，请立即轮换

## License

Apache-2.0
