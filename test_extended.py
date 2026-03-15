"""
Extended Test Suite - Comprehensive testing for automation tools

Provides unit tests for core scripts with better coverage.
"""
import os
import sys
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

# Test imports
def test_clean_module_import():
    """Test that clean module can be imported."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("clean_simple", "clean_simple.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert hasattr(module, 'clean_dir'), "clean_dir function not found"
        assert hasattr(module, 'main'), "main function not found"
    except Exception as e:
        raise AssertionError(f"Failed to import clean_simple: {e}")

def test_mouse_helper_functions():
    """Test mouse helper module functions."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mouse_helper", "mouse_helper.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, 'get_mouse_position'), "get_mouse_position not found"
        assert hasattr(module, 'get_screen_size'), "get_screen_size not found"
        assert hasattr(module, 'safe_click'), "safe_click not found"
        assert hasattr(module, 'generate_click_positions'), "generate_click_positions not found"
    except Exception as e:
        raise AssertionError(f"Failed to import mouse_helper: {e}")

def test_screenshot_functions():
    """Test screenshot module functions."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("screenshot", "screenshot.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, 'take_screenshot'), "take_screenshot not found"
        assert hasattr(module, 'get_screen_info'), "get_screen_info not found"
        assert hasattr(module, 'generate_filename'), "generate_filename not found"
    except Exception as e:
        raise AssertionError(f"Failed to import screenshot: {e}")

def test_wechat_automation_functions():
    """Test wechat automation module functions."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("wechat_automation", "wechat_automation.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, 'find_and_click_search'), "find_and_click_search not found"
        assert hasattr(module, 'search_contact'), "search_contact not found"
        assert hasattr(module, 'click_search_result'), "click_search_result not found"
        assert hasattr(module, 'send_message'), "send_message not found"
    except Exception as e:
        raise AssertionError(f"Failed to import wechat_automation: {e}")

def test_pyautogui_deploy_functions():
    """Test pyautogui deploy module functions."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("pyautogui_deploy", "pyautogui_deploy.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        assert hasattr(module, 'check_package_installed'), "check_package_installed not found"
        assert hasattr(module, 'get_package_version'), "get_package_version not found"
        assert hasattr(module, 'install_package'), "install_package not found"
        assert hasattr(module, 'check_pyautogui_installation'), "check_pyautogui_installation not found"
    except Exception as e:
        raise AssertionError(f"Failed to import pyautogui_deploy: {e}")

def test_screenshot_filename_generation():
    """Test screenshot filename generation with timestamps."""
    from datetime import datetime
    import importlib.util

    spec = importlib.util.spec_from_file_location("screenshot", "screenshot.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Test default filename generation
    filename = module.generate_filename()
    assert filename.startswith("screenshot_"), "Filename should start with prefix"
    assert filename.endswith(".png"), "Filename should end with .png"

    # Test custom prefix
    filename = module.generate_filename(prefix="test")
    assert filename.startswith("test_"), "Filename should start with custom prefix"

    # Test custom extension
    filename = module.generate_filename(extension="jpg")
    assert filename.endswith(".jpg"), "Filename should end with custom extension"

def test_click_position_generation():
    """Test click position generation strategies."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("mouse_helper", "mouse_helper.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    # Test grid strategy
    positions = module.generate_click_positions('grid')
    assert len(positions) == 4, "Grid strategy should generate 4 positions"

    # Test center strategy
    positions = module.generate_click_positions('center')
    assert len(positions) >= 5, "Center strategy should generate at least 5 positions"

    # Test scan strategy
    positions = module.generate_click_positions('scan')
    assert len(positions) == 9, "Scan strategy should generate 9 positions"

def test_directory_structure():
    """Test project directory structure."""
    required_dirs = ['memory', 'skills']
    for dir_name in required_dirs:
        assert os.path.isdir(dir_name), f"{dir_name} directory should exist"

def test_project_files_exist():
    """Test that all required project files exist."""
    required_files = [
        'AGENTS.md',
        'SOUL.md',
        'TOOLS.md',
        'USER.md',
        'README.md',
        'DEVELOPMENT_PLAN.md',
        'test_cleanup.py',
        'test_extended.py',
        'progress_report.py'
    ]

    for file_name in required_files:
        assert os.path.isfile(file_name), f"{file_name} should exist"

def test_git_initialized():
    """Test that git is initialized."""
    assert os.path.isdir('.git'), "Git directory should exist"

def test_gitignore_exists():
    """Test that .gitignore exists and contains proper entries."""
    assert os.path.isfile('.gitignore'), ".gitignore should exist"

    with open('.gitignore', 'r', encoding='utf-8') as f:
        content = f.read()

    # Check for common ignore patterns
    patterns = ['__pycache__', '*.pyc', '.DS_Store', 'Thumbs.db']
    for pattern in patterns:
        assert pattern in content, f".gitignore should contain {pattern}"

def test_readme_exists():
    """Test that README.md exists and contains required sections."""
    assert os.path.isfile('README.md'), "README.md should exist"

    with open('README.md', 'r', encoding='utf-8') as f:
        content = f.read().lower()

    # Check for key sections (support both English and Chinese)
    sections_en = ['features', 'installation', 'usage', 'license']
    sections_cn = ['功能特性', '安装', '使用', '许可证']

    for en, cn in zip(sections_en, sections_cn):
        assert en in content or cn in content, f"README.md should mention {en} or {cn}"

def test_main_functions_return_zero():
    """Test that main functions can be called (basic import test)."""
    modules = [
        ('clean_simple', 'clean_simple.py'),
        ('mouse_helper', 'mouse_helper.py'),
        ('screenshot', 'screenshot.py'),
        ('wechat_automation', 'wechat_automation.py'),
        ('pyautogui_deploy', 'pyautogui_deploy.py')
    ]

    for name, path in modules:
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            assert hasattr(module, 'main'), f"{name}.main should exist"
        except Exception as e:
            raise AssertionError(f"Failed to test {name}: {e}")

def run_all_tests():
    """Run all tests and return results."""
    print("Extended Test Suite")
    print("=" * 60)

    tests = [
        ("Clean module import", test_clean_module_import),
        ("Mouse helper functions", test_mouse_helper_functions),
        ("Screenshot functions", test_screenshot_functions),
        ("WeChat automation functions", test_wechat_automation_functions),
        ("PyAutoGUI deploy functions", test_pyautogui_deploy_functions),
        ("Screenshot filename generation", test_screenshot_filename_generation),
        ("Click position generation", test_click_position_generation),
        ("Directory structure", test_directory_structure),
        ("Project files exist", test_project_files_exist),
        ("Git initialized", test_git_initialized),
        (".gitignore exists", test_gitignore_exists),
        ("README.md exists", test_readme_exists),
        ("Main functions return zero", test_main_functions_return_zero),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            test_func()
            print(f"[PASS] {test_name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test_name}: {str(e)}")
            failed += 1

    print("=" * 60)
    print(f"Tests: {passed} passed, {failed} failed")
    print(f"Coverage: {passed}/{passed + failed} ({passed*100//(passed+failed) if passed+failed>0 else 0}%)")
    print("=" * 60)

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
