@echo off
chcp 65001 >nul
title Windows 自动化工具集 - 快速启动

echo ========================================
echo    Windows 自动化工具集 - 快速启动
echo ========================================
echo.

:: 检查 Python 是否安装
echo [1/4] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请先安装 Python 3.7 或更高版本
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [✓] Python 环境正常
echo.

:: 检查是否在虚拟环境中
echo [2/4] 检查虚拟环境...
if not exist "venv\Scripts\activate.bat" (
    echo [!] 未找到虚拟环境，正在创建...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
    echo [✓] 虚拟环境创建成功
) else (
    echo [✓] 虚拟环境已存在
)
echo.

:: 激活虚拟环境
call venv\Scripts\activate.bat

:: 检查并安装依赖
echo [3/4] 检查并安装依赖...
pip install --upgrade pip >nul 2>&1
pip install pyautogui pygetwindow pyperclip pywinauto pillow
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)
echo [✓] 依赖安装完成
echo.

:: 显示菜单
echo ========================================
echo            功能选择菜单
echo ========================================
echo.
echo  [1] 运行鼠标测试
echo  [2] 运行磁盘清理
echo  [3] 启动微信自动化
echo  [4] 运行截图工具
echo  [5] 运行完整测试套件
echo  [6] 进入交互式 Python 环境
echo  [0] 退出
echo.
echo ========================================
set /p choice="请选择功能 (0-6): "

echo.
if "%choice%"=="1" (
    echo [*] 启动鼠标测试...
    python test_mouse.py
) else if "%choice%"=="2" (
    echo [*] 启动磁盘清理...
    python clean_simple.py
) else if "%choice%"=="3" (
    echo [*] 启动微信自动化...
    python wechat_automation.py
) else if "%choice%"=="4" (
    echo [*] 启动截图工具...
    python screenshot.py
) else if "%choice%"=="5" (
    echo [*] 运行完整测试套件...
    python test_cleanup.py
) else if "%choice%"=="6" (
    echo [*] 进入交互式 Python 环境...
    python -i
) else if "%choice%"=="0" (
    echo [*] 退出程序...
    exit /b 0
) else (
    echo [错误] 无效的选择
    pause
    exit /b 1
)

echo.
echo [✓] 程序执行完成
pause
