# Windows 自动化工具集

一个强大的Windows系统自动化工具集合，专注于磁盘清理、微信自动化和桌面控制。

## 🚀 功能特性

### 磁盘清理
- 清理浏览器缓存（Chrome, Edge）
- 清理系统临时文件
- 清理Windows缓存（Prefetch, ReportQueue等）
- 清理开发工具缓存（NPM, pip, Conda）

### 微信自动化
- 自动搜索联系人
- 自动发送消息
- 窗口定位和控制
- 截图功能

### 桌面控制
- 鼠标自动化（点击、移动、拖拽）
- 键盘自动化（输入、快捷键）
- 窗口管理
- 截图工具

## 📦 安装

### 依赖要求
- Python 3.7+
- Windows 10/11

### 安装依赖

```bash
# 使用pip安装
pip install pyautogui pygetwindow pyperclip pywinauto pillow

# 或使用conda
conda install -c conda-forge pyautogui pygetwindow pyperclip
```

## 🛠️ 使用方法

### 磁盘清理

```bash
# 运行清理脚本
python clean_simple.py
```

### 微信自动化

```bash
# 启动微信
python auto_launch_wechat.py

# 自动发送消息
python wechat_automation.py
```

### 桌面控制

```bash
# 测试鼠标控制
python test_mouse.py

# 截图
python screenshot.py
```

## 📁 项目结构

```
workspace/
├── clean_simple.py              # 磁盘清理脚本
├── wechat_automation.py          # 微信自动化
├── mouse_helper.py              # 鼠标辅助工具
├── test_cleanup.py              # 测试脚本
├── AUTOMATION_DEPLOYMENT.md     # 部署文档
├── README.md                    # 本文件
├── memory/                      # 记忆文件
└── skills/                      # 技能扩展
```

## 🧪 测试

运行测试套件：

```bash
python test_cleanup.py
```

## 📝 开发流程

1. 修改代码
2. 运行测试：`python test_cleanup.py`
3. 确保测试通过
4. 提交到git：`git add . && git commit -m "描述"`
5. 推送到远程仓库（已配置）

## 🔧 配置

编辑 `tools` 目录中的配置文件来设置：
- 鼠标点击位置
- 窗口标题
- 清理路径

## 📄 许可证

MIT License

## 👤 作者

GX - 自动化工具开发者

## 🤝 贡献

欢迎提交问题和拉取请求！

---

**注意：** 这些工具仅用于学习和个人使用。使用前请备份重要数据。
