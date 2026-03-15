#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单的微信消息发送脚本
通过模拟键盘输入来发送消息
"""
import subprocess
import time
import sys

def send_message(message):
    """
    通过模拟键盘输入发送消息到微信
    """
    print(f"正在发送消息: {message}")
    
    try:
        # 等待一下确保微信窗口在前台
        time.sleep(2)
        
        # 搜索联系人（Ctrl+F）
        subprocess.run([
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            f"$wshell = New-Object -ComObject WScript.Shell; $wshell.AppActivate('WeChat'); $wshell.SendKeys('^f')"
        ], check=True)
        time.sleep(2)
        
        # 输入"郑政隆"
        subprocess.run([
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            "$wshell.SendKeys('郑政隆')"
        ], check=True)
        time.sleep(1)
        
        # 按 Enter
        subprocess.run([
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            "$wshell.SendKeys('{ENTER}')"
        ], check=True)
        time.sleep(2)
        
        # 输入"我是openclaw，你好"
        subprocess.run([
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            "$wshell.SendKeys('我是openclaw，你好')"
        ], check=True)
        time.sleep(1)
        
        # 按 Enter 发送
        subprocess.run([
            'powershell.exe',
            '-NoProfile',
            '-ExecutionPolicy', 'Bypass',
            '-Command',
            "$wshell.SendKeys('{ENTER}')"
        ], check=True)
        
        print(f"消息发送完成!")
        return True
        
    except Exception as e:
        print(f"发送失败: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        message = ' '.join(sys.argv[1:])
    else:
        message = "我是openclaw，你好"
    
    send_message(message)
