# SkillGraph 技能图谱

> **Map the Hidden Risks** - AI Agent Skills 安全检测工具

<p align="center">
  <img src="https://img.shields.io/badge/python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/status-alpha-orange.svg" alt="Status">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
</p>

基于 **GraphRAG + GNN** 的 AI Agent Skills 安全扫描器。 在使用从网上下载的 skills 之前，检测其中的隐藏风险。

## 为什么选择 SkillGraph？

从网上下载的 Agent Skills 可能包含：
- 隐藏的数据窃取指令
- 凭证盗窃指令
- 系统破坏命令
- 安全绕过尝试

SkillGraph 通过图谱分析帮你**看穿**这些风险。

## 功能特性

- 🔍 **Skill Parser** - 解析 Markdown skills 为结构化数据
- ⚠️ **Risk Detection** - 基于规则的安全风险检测
- 📊 **Graph Visualization** - 交互式知识图谱展示
- 💻 **CLI Tool** - 命令行快速扫描工具
- 🌐 **Web UI** - Streamlit 可视化应用

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/goldzzmj/skillgraph.git
cd skillgraph

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 安装包
pip install -e .
```

### CLI 使用

```bash
# 扫描 skill 文件
skillgraph scan path/to/skill.md

# JSON 格式输出
skillgraph scan skill.md -f json -o report.json

# 解析 skill 结构
skillgraph parse skill.md -o parsed.json
```

### Web UI

```bash
# 启动可视化应用
skillgraph viz

# 或直接运行
streamlit run src/skillgraph/viz/app.py
```

在浏览器中打开 http://localhost:8501

## 风险等级

| 等级 | 分数 | 描述 |
|------|------|------|
| 🔴 Critical | 0.8-1.0 | 数据窃取、系统破坏 |
| 🟠 High | 0.6-0.8 | 敏感访问、网络请求 |
| 🟡 Medium | 0.4-0.6 | 代码执行、配置修改 |
| 🟢 Low | 0.2-0.4 | 一般文件操作 |
| ✅ Safe | 0-0.2 | 未检测到风险 |

## 系统架构

```
┌─────────────────────────────────────────────────────┐
│                   SkillGraph System                  │
├─────────────────────────────────────────────────────┤
│  输入层          │  核心引擎        │  输出层         │
│  - Markdown      │  - Parser        │  - Web UI       │
│  - YAML          │  - Rules Engine  │  - CLI          │
│  - Scripts       │  - Graph Builder │  - API          │
└─────────────────────────────────────────────────────┘
```

## 项目结构

```
skillgraph/
├── src/skillgraph/
│   ├── parser/          # Markdown 解析
│   ├── rules/           # 风险检测规则
│   ├── graph/           # NetworkX 图谱构建
│   ├── viz/             # Streamlit 可视化
│   └── cli.py           # 命令行接口
├── tests/               # 单元测试
├── examples/            # 示例 skill 文件
├── requirements.txt
└── setup.py
```

## 开发路线

- [x] MVP: Parser + Rules + CLI
- [x] Streamlit Visualization
- [ ] GraphRAG 集成
- [ ] GNN 风险模型
- [ ] FastAPI 服务
- [ ] Claude Code 插件

## 贡献

欢迎贡献代码！ 请随时提交 Pull Request。

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

**SkillGraph** - 洞察你的 Agent Skills 中的隐藏风险 🔍
