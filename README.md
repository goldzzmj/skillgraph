# 🚀 Windows 自动化工具集

<div align="center">

一个功能强大、易于使用的 Windows 系统自动化工具集合，专注于磁盘清理、微信自动化和桌面控制。

[![Python](https://img.shields.io/badge/Python-3.7%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)](https://www.microsoft.com/windows)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [安装](#-安装) • [使用方法](#-使用方法) • [开发](#-开发) • [贡献](#-贡献)

</div>

---

## ✨ 功能特性

### 🧹 磁盘清理
- **浏览器缓存清理** - Chrome、Edge 等主流浏览器
- **系统临时文件清理** - 自动识别并清理临时文件夹
- **Windows 缓存清理** - Prefetch、ReportQueue、Thumbnail Cache 等
- **开发工具缓存清理** - NPM、pip、Conda 包管理器缓存
- **智能扫描** - 快速扫描大文件和占用空间的目录

### 💬 微信自动化
- **自动搜索联系人** - 支持精确匹配和模糊搜索
- **自动发送消息** - 批量发送、定时发送
- **窗口定位和控制** - 智能识别微信窗口位置
- **截图功能** - 自动截取微信界面并保存
- **多账号支持** - 支持多个微信账号的自动化操作

### 🖱️ 桌面控制
- **鼠标自动化** - 点击、移动、拖拽、双击、右键
- **键盘自动化** - 文本输入、快捷键、组合键
- **窗口管理** - 激活、最小化、最大化、关闭窗口
- **截图工具** - 全屏、指定区域、应用窗口截图
- **跨应用操作** - 支持多个应用的协同自动化

### 🔧 其他工具
- **小红书工具** - 下载、搜索、内容分析
- **代理工具** - 代理配置、网络请求
- **配置管理** - 环境配置、参数设置
- **日志记录** - 完整的操作日志和错误追踪

---

## 🎯 快速开始

### 30 秒快速体验

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd workspace

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行示例
python test_mouse.py
```

### 最小化依赖安装

```bash
pip install pyautogui pygetwindow pyperclip pywinauto pillow
```

---

## 📦 安装

### 系统要求
- **操作系统**: Windows 10 / Windows 11
- **Python 版本**: Python 3.7 或更高版本
- **额外要求**: 管理员权限（部分功能需要）

### 完整安装步骤

#### 1. 克隆项目

```bash
git clone <your-repo-url>
cd workspace
```

#### 2. 创建虚拟环境（推荐）

```bash
# 使用 venv
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac (如适用)
```

#### 3. 安装依赖

```bash
# 方式一：使用 requirements.txt（推荐）
pip install -r requirements.txt

# 方式二：逐个安装
pip install pyautogui pygetwindow pyperclip pywinauto pillow

# 方式三：使用 conda
conda install -c conda-forge pyautogui pygetwindow pyperclip
conda install pillow
```

#### 4. 验证安装

```bash
# 运行测试脚本
python test_mouse.py

# 如果鼠标移动到指定位置，说明安装成功
```

### 可选依赖

```bash
# 小红书相关功能
pip install xiaohongshu-py

# 高级窗口控制
pip install uiautomation

# 日志增强
pip install colorlog
```

---

## 🛠️ 使用方法

### 磁盘清理

#### 基础清理

```bash
# 运行简化版清理脚本
python clean_simple.py

# 运行完整清理（包括扫描）
python quick_scan.py
```

#### 高级清理

```bash
# 扫描大文件
python find_large_dirs.py

# 扫描临时文件
python scan_appdata.py

# 生成清理报告
python cleanup_report.md
```

#### 清理示例

```python
from clean_simple import CleanUp

# 创建清理实例
cleaner = CleanUp()

# 运行所有清理任务
cleaner.run_all()

# 运行特定清理任务
cleaner.clean_browser_cache()
cleaner.clean_temp_files()
```

### 微信自动化

#### 启动微信

```bash
# 启动微信应用
python auto_launch_wechat.py

# 查找微信窗口
python find_wechat.py
```

#### 自动发送消息

```bash
# 完整自动化流程
python wechat_automation.py

# 搜索并发送
python wechat_search_send.py

# 带截图的流程
python wechat_steps_with_screenshots.py
```

#### 编程示例

```python
from wechat_automation import WeChatAutomation

# 创建自动化实例
wechat = WeChatAutomation()

# 发送消息
wechat.send_message(
    contact="郑政隆",
    message="你好，这是自动发送的消息"
)

# 批量发送
contacts = ["张三", "李四", "王五"]
wechat.send_batch_message(contacts, "批量消息")
```

### 桌面控制

#### 基础操作

```bash
# 测试鼠标控制
python test_mouse.py

# 截图
python screenshot.py

# 鼠标辅助工具
python mouse_helper.py
```

#### 高级操作

```python
import pyautogui
import pygetwindow

# 移动鼠标
pyautogui.moveTo(100, 100, duration=0.5)

# 点击
pyautogui.click(x=200, y=300)

# 输入文本
pyautogui.write("Hello World", interval=0.1)

# 组合键
pyautogui.hotkey('ctrl', 'c')

# 获取窗口
windows = pygetwindow.getAllTitles()
wechat = pygetwindow.getWindowsWithTitle('WeChat')[0]

# 窗口操作
wechat.activate()
wechat.minimize()
wechat.maximize()
```

#### 截图功能

```python
import pyautogui

# 全屏截图
screenshot = pyautogui.screenshot('full_screen.png')

# 指定区域截图
region = (100, 100, 500, 500)
screenshot = pyautogui.screenshot(region=region)
screenshot.save('region.png')

# 窗口截图
window = pygetwindow.getWindowsWithTitle('WeChat')[0]
screenshot = pyautogui.screenshot(region=(
    window.left, window.top,
    window.width, window.height
))
```

---

## 📁 项目结构

```
workspace/
├── 📂 core/                      # 核心功能模块
│   ├── clean_simple.py          # 磁盘清理核心
│   ├── wechat_automation.py    # 微信自动化
│   ├── mouse_helper.py          # 鼠标控制
│   └── screenshot.py            # 截图功能
│
├── 📂 tools/                     # 工具脚本
│   ├── find_large_dirs.py       # 查找大文件
│   ├── scan_appdata.py          # 扫描 AppData
│   └── quick_scan.py            # 快速扫描
│
├── 📂 tests/                     # 测试脚本
│   ├── test_cleanup.py          # 清理测试
│   ├── test_mouse.py            # 鼠标测试
│   └── test_extended.py         # 扩展测试
│
├── 📂 docs/                      # 文档
│   ├── README.md                # 项目说明
│   ├── DEVELOPMENT_PLAN.md      # 开发计划
│   ├── AUTOMATION_DEPLOYMENT.md # 部署文档
│   └── STATUS_REPORT.md         # 状态报告
│
├── 📂 memory/                    # 记忆文件
│   └── 2026-03-16.md            # 每日记录
│
├── 📂 skills/                    # 技能扩展
│   └── ...                       # OpenClaw 技能
│
├── 📄 requirements.txt           # Python 依赖
├── 📄 .gitignore                # Git 忽略文件
├── 📄 AGENTS.md                 # Agent 配置
└── 📄 SOUL.md                   # 项目灵魂
```

---

## 🧪 测试

### 运行所有测试

```bash
# 运行测试套件
python test_cleanup.py

# 运行扩展测试
python test_extended.py

# 运行鼠标测试
python test_mouse.py
```

### 测试覆盖

- ✅ 磁盘清理功能测试
- ✅ 微信自动化测试
- ✅ 鼠标控制测试
- ✅ 截图功能测试
- ✅ 窗口管理测试

---

## 🚧 开发

### 开发环境设置

```bash
# 1. 克隆仓库
git clone <your-repo-url>
cd workspace

# 2. 创建开发环境
python -m venv venv
venv\Scripts\activate

# 3. 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8

# 4. 配置 pre-commit（可选）
pip install pre-commit
pre-commit install
```

### 代码规范

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查（如使用 mypy）
mypy .
```

### Git 工作流

```bash
# 1. 创建新分支
git checkout -b feature/your-feature

# 2. 进行修改
# ... 编写代码 ...

# 3. 运行测试
python test_cleanup.py

# 4. 提交更改
git add .
git commit -m "feat: 添加新功能"

# 5. 推送到远程
git push origin feature/your-feature

# 6. 创建 Pull Request
```

### 提交信息规范

使用 Conventional Commits 规范：

```
feat: 添加新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```

---

## 📋 开发路线图

### 阶段 1: 项目结构化 ✅ 已完成
- ✅ 初始化 Git 仓库
- ✅ 创建项目结构
- ✅ 编写基础文档
- ✅ 创建测试套件

### 阶段 2: 代码规范化 🚧 进行中
- [ ] 添加类型提示
- [ ] 统一代码风格
- [ ] 完善错误处理
- [ ] 添加文档字符串
- [ ] 增强日志记录

### 阶段 3: 测试覆盖 📋 待开始
- [ ] 增加单元测试
- [ ] 添加集成测试
- [ ] 设置 CI/CD
- [ ] 配置自动化测试

### 阶段 4: 部署自动化 📋 待开始
- [ ] 创建安装脚本
- [ ] 完善用户文档
- [ ] 准备发布版本
- [ ] 配置自动化部署

---

## 🔧 配置

### 环境变量

创建 `.env` 文件：

```bash
# 微信配置
WECHAT_WINDOW_TITLE=WeChat
WECHAT_SEARCH_BOX_X=2940
WECHAT_SEARCH_BOX_Y=100

# 清理配置
CLEANUP_BROWSER_CACHE=true
CLEANUP_TEMP_FILES=true
CLEANUP_WINDOWS_CACHE=true

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=automation.log
```

### 配置文件

在项目根目录创建 `config.json`：

```json
{
  "wechat": {
    "contact": "郑政隆",
    "message": "自动发送的消息",
    "delay": 0.5
  },
  "cleanup": {
    "browser": ["Chrome", "Edge"],
    "temp_dirs": ["C:\\Windows\\Temp", "%TEMP%"],
    "exclude_dirs": ["C:\\Windows\\System32"]
  },
  "mouse": {
    "default_duration": 0.5,
    "safe_mode": true
  }
}
```

---

## ❓ 常见问题 (FAQ)

### 1. PyAutoGUI 导入错误

**问题**: `ModuleNotFoundError: No module named 'pyautogui'`

**解决**:
```bash
pip install pyautogui
```

### 2. 微信窗口找不到

**问题**: `IndexError: list index out of range`

**解决**:
- 确保微信已启动
- 检查窗口标题是否正确
- 使用 `find_wechat.py` 查找窗口

### 3. 鼠标点击位置不对

**问题**: 鼠标点击位置不准确

**解决**:
- 使用 `screenshot.py` 截图确认位置
- 调整分辨率和缩放设置
- 使用相对坐标而非绝对坐标

### 4. 清理权限不足

**问题**: `PermissionError: [Errno 13] Permission denied`

**解决**:
- 以管理员身份运行脚本
- 检查文件是否被占用
- 跳过系统关键目录

### 5. matplotlib 依赖错误

**问题**: `ImportError: Matplotlib requires numpy>=1.23`

**解决**:
```bash
pip install --upgrade numpy
```

---

## 🤝 贡献

我们欢迎所有形式的贡献！

### 如何贡献

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'feat: 添加某个功能'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

### 贡献指南

- 遵循现有代码风格
- 添加必要的测试
- 更新相关文档
- 保持提交信息清晰

### 报告问题

使用 GitHub Issues 报告 bug 或提出功能建议：

- 描述问题或功能请求
- 提供复现步骤
- 附上相关截图或日志
- 标注适当的标签

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

```
MIT License

Copyright (c) 2026 GX

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

---

## 👥 作者

**GX** - *主要开发者* - [GitHub Profile](https://github.com/yourusername)

---

## 🙏 致谢

- [PyAutoGUI](https://pyautogui.readthedocs.io/) - 强大的 GUI 自动化库
- [PyGetWindow](https://pygetwindow.readthedocs.io/) - 跨平台窗口管理
- [Pywinauto](https://pywinauto.readthedocs.io/) - Windows UI 自动化
- [Pillow](https://pillow.readthedocs.io/) - Python 图像处理库

---

## 📊 项目统计

| 指标 | 数量 |
|------|------|
| Python 文件 | 55+ |
| Markdown 文档 | 27+ |
| 测试用例 | 6+ |
| 功能模块 | 10+ |

---

## 🔗 相关链接

- [项目文档](./docs/)
- [开发计划](./DEVELOPMENT_PLAN.md)
- [部署指南](./AUTOMATION_DEPLOYMENT.md)
- [状态报告](./STATUS_REPORT.md)

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给它一个星标！**

Made with ❤️ by GX

[返回顶部](#-windows-自动化工具集)

</div>
