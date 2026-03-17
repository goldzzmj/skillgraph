#!/bin/bash

# Windows 自动化工具集 - 快速启动脚本 (Linux/Mac)

set -e

echo "========================================"
echo "   Windows 自动化工具集 - 快速启动"
echo "========================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查 Python 是否安装
echo -e "[1/4] 检查 Python 环境..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[错误]${NC} 未检测到 Python3，请先安装 Python 3.7 或更高版本"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macOS 安装: brew install python3"
    else
        echo "Linux 安装: sudo apt-get install python3 或使用其他包管理器"
    fi
    exit 1
fi
echo -e "${GREEN}[✓]${NC} Python 环境正常: $(python3 --version)"
echo ""

# 检查是否在虚拟环境中
echo -e "[2/4] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}[!]${NC} 未找到虚拟环境，正在创建..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "${RED}[错误]${NC} 创建虚拟环境失败"
        exit 1
    fi
    echo -e "${GREEN}[✓]${NC} 虚拟环境创建成功"
else
    echo -e "${GREEN}[✓]${NC} 虚拟环境已存在"
fi
echo ""

# 激活虚拟环境
source venv/bin/activate

# 检查并安装依赖
echo -e "[3/4] 检查并安装依赖..."
pip install --upgrade pip -q
pip install pyautogui pygetwindow pyperclip pywinauto pillow -q
if [ $? -ne 0 ]; then
    echo -e "${RED}[错误]${NC} 依赖安装失败"
    deactivate
    exit 1
fi
echo -e "${GREEN}[✓]${NC} 依赖安装完成"
echo ""

# 显示菜单
echo "========================================"
echo "           功能选择菜单"
echo "========================================"
echo ""
echo "  [1] 运行鼠标测试"
echo "  [2] 运行磁盘清理"
echo "  [3] 启动微信自动化"
echo "  [4] 运行截图工具"
echo "  [5] 运行完整测试套件"
echo "  [6] 进入交互式 Python 环境"
echo "  [0] 退出"
echo ""
echo "========================================"
read -p "请选择功能 (0-6): " choice
echo ""

case $choice in
    1)
        echo -e "[*] 启动鼠标测试..."
        python3 test_mouse.py
        ;;
    2)
        echo -e "[*] 启动磁盘清理..."
        python3 clean_simple.py
        ;;
    3)
        echo -e "[*] 启动微信自动化..."
        python3 wechat_automation.py
        ;;
    4)
        echo -e "[*] 启动截图工具..."
        python3 screenshot.py
        ;;
    5)
        echo -e "[*] 运行完整测试套件..."
        python3 test_cleanup.py
        ;;
    6)
        echo -e "[*] 进入交互式 Python 环境..."
        python3 -i
        ;;
    0)
        echo -e "[*] 退出程序..."
        deactivate
        exit 0
        ;;
    *)
        echo -e "${RED}[错误]${NC} 无效的选择"
        deactivate
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}[✓]${NC} 程序执行完成"
deactivate
