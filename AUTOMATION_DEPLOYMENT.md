# Python Automation Tools Deployment

## Installation Status

### Installed in Conda Environment (D:\anaconda3)

| Tool | Version | Status | Purpose |
|------|---------|--------|---------|
| **PyAutoGUI** | 0.9.54 | ✅ Installed | Mouse/keyboard automation |
| **PyGetWindow** | Latest | ✅ Installed | Window management |
| **Pyperclip** | Latest | ✅ Installed | Clipboard operations |
| **Pywinauto** | 0.6.9 | ✅ Installed | Windows automation |
| **Pillow** | Installed | ✅ Available | Screenshot/image processing |

### Note About "pyautoagui"

The package "pyautoagui" does not exist on PyPI. You likely mean one of:
- **PyAutoGUI** - Main automation library
- **Pywinauto** - Windows UI automation
- **uiautomation** - UI automation framework

All these tools are now installed and ready to use.

## Available Automation Capabilities

### 1. PyAutoGUI
```python
import pyautogui

# Mouse
pyautogui.moveTo(100, 100)
pyautogui.click()
pyautogui.doubleClick()
pyautogui.rightClick()

# Keyboard
pyautogui.write("Hello World")
pyautogui.press('enter')
pyautogui.hotkey('ctrl', 'c')

# Screen
pyautogui.screenshot('screen.png')
width, height = pyautogui.size()
```

### 2. PyGetWindow
```python
import pygetwindow

# Get active window
active_window = pygetwindow.getActiveWindow()
print(active_window.title)

# Get all windows
windows = pygetwindow.getAllTitles()
print(windows)

# Get specific window
window = pygetwindow.getWindowsWithTitle('WeChat')[0]
window.activate()
```

### 3. Pyperclip
```python
import pyperclip

# Copy text
pyperclip.copy("Hello")

# Paste text
text = pyperclip.paste()

# Get clipboard
current = pyperclip.paste()
```

### 4. Pywinauto
```python
from pywinauto import Application

# Connect to application
app = Application(backend="uia").connect(title="WeChat")
wechat = app.window(title="WeChat")

# Type text
wechat.type_keys("%Hello World%")

# Click button
wechat.button.click()

# Get window info
print(wechat.rectangle())
```

## Usage Examples

### WeChat Automation
```python
import pyautogui
import pygetwindow
import time

# Method 1: Using PyAutoGUI only
def wechat_automation_simple():
    # Click search box
    pyautogui.click(width-500, 100)
    time.sleep(0.5)

    # Type search
    pyautogui.write("郑政隆")
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)

    # Click result and send message
    pyautogui.click(width-500, 180)
    time.sleep(1)
    pyautogui.click(width//2, height-150)
    time.sleep(0.5)
    pyautogui.write("我是openclaw")
    time.sleep(0.5)
    pyautogui.press('enter')

# Method 2: Using PyGetWindow + PyAutoGUI
def wechat_automation_with_window():
    # Get WeChat window
    wechat = pygetwindow.getWindowsWithTitle('WeChat')[0]
    wechat.activate()
    time.sleep(1)

    # Now use PyAutoGUI relative to window
    # (Need to get window position first)
    rect = wechat.left, wechat.top, wechat.width, wechat.height
    # Click relative to window position
    pyautogui.click(rect[0] + 200, rect[1] + 100)
```

### Desktop Control
```python
import pyautogui
import time

def control_app(app_name, actions):
    """Generic app controller"""
    for action in actions:
        if action['type'] == 'click':
            pyautogui.click(action['x'], action['y'])
        elif action['type'] == 'type':
            pyautogui.write(action['text'])
        elif action['type'] == 'press':
            pyautogui.press(action['key'])
        elif action['type'] == 'hotkey':
            pyautogui.hotkey(*action['keys'])
        time.sleep(action.get('delay', 0.5))

# Example: Control WeChat
wechat_actions = [
    {'type': 'click', 'x': 2940, 'y': 100, 'delay': 0.5},
    {'type': 'type', 'text': '郑政隆', 'delay': 0.5},
    {'type': 'press', 'key': 'enter', 'delay': 2},
    {'type': 'click', 'x': 2940, 'y': 180, 'delay': 1},
    {'type': 'click', 'x': 1720, 'y': 1290, 'delay': 0.5},
    {'type': 'type', 'text': '我是openclaw', 'delay': 0.5},
    {'type': 'press', 'key': 'enter', 'delay': 1},
]

control_app('WeChat', wechat_actions)
```

## Test Scripts

### Simple Test
```python
python -c "import pyautogui; pyautogui.moveTo(100, 100); print('Moved mouse')"
```

### WeChat Launcher
```bash
python auto_launch_wechat.py
```

### WeChat Full Automation
```python
python wechat_automation.py
```

## Environment Variables

```bash
# Add to activate scripts
# D:\anaconda3\Scripts\
```

## Next Steps

1. ✅ All automation tools are installed
2. ✅ Ready for WeChat automation
3. ✅ Ready for Windows app automation
4. ✅ Clipboard operations available
5. ✅ Window management available

## Notes

- PyAutoGUI is the main tool for mouse/keyboard control
- PyGetWindow helps manage and find windows
- Pyperclip handles clipboard operations
- Pywinauto provides advanced Windows UI automation
- All tools are compatible with each other

## Quick Reference

| Task | Tool | Command |
|-------|-------|----------|
| Click | PyAutoGUI | `pyautogui.click(x, y)` |
| Type | PyAutoGUI | `pyautogui.write('text')` |
| Hotkey | PyAutoGUI | `pyautogui.hotkey('ctrl', 'c')` |
| Screenshot | PyAutoGUI | `pyautogui.screenshot('file.png')` |
| Get Window | PyGetWindow | `pygetwindow.getActiveWindow()` |
| Clipboard | Pyperclip | `pyperclip.copy('text')` |
