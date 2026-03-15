"""
测试脚本 - 自动化工具测试套件
"""
import os
import sys
import subprocess
import tempfile
import shutil

class TestRunner:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.results = []

    def run_test(self, test_func, test_name):
        """运行单个测试"""
        try:
            test_func()
            self.passed += 1
            self.results.append(f"[PASS] {test_name}")
            print(f"[PASS] {test_name}")
            return True
        except Exception as e:
            self.failed += 1
            self.results.append(f"[FAIL] {test_name}: {str(e)}")
            print(f"[FAIL] {test_name}: {str(e)}")
            return False

    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print(f"测试完成: {self.passed} 通过, {self.failed} 失败")
        print("="*60)
        for result in self.results:
            print(result)
        return self.failed == 0

def test_clean_simple_exists():
    """测试清理脚本是否存在"""
    assert os.path.exists("clean_simple.py"), "clean_simple.py 不存在"
    assert os.path.getsize("clean_simple.py") > 0, "clean_simple.py 为空"

def test_clean_importable():
    """测试清理脚本可以导入"""
    import importlib.util
    spec = importlib.util.spec_from_file_location("clean_simple", "clean_simple.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

def test_wechat_automation_exists():
    """测试微信自动化脚本是否存在"""
    assert os.path.exists("wechat_automation.py"), "wechat_automation.py 不存在"

def test_mouse_helper_exists():
    """测试鼠标辅助脚本是否存在"""
    assert os.path.exists("mouse_helper.py"), "mouse_helper.py 不存在"

def test_project_structure():
    """测试项目结构"""
    required_files = [
        "AGENTS.md",
        "SOUL.md",
        "TOOLS.md",
        "USER.md",
        "AUTOMATION_DEPLOYMENT.md"
    ]
    for file in required_files:
        assert os.path.exists(file), f"{file} 不存在"

def test_directory_structure():
    """测试目录结构"""
    assert os.path.exists("memory"), "memory 目录不存在"
    assert os.path.exists("skills"), "skills 目录不存在"

def main():
    """主测试函数"""
    print("开始测试...")
    print("="*60)

    runner = TestRunner()

    # 基础测试
    runner.run_test(test_clean_simple_exists, "清理脚本存在性")
    runner.run_test(test_clean_importable, "清理脚本可导入")
    runner.run_test(test_wechat_automation_exists, "微信自动化脚本存在性")
    runner.run_test(test_mouse_helper_exists, "鼠标辅助脚本存在性")
    runner.run_test(test_project_structure, "项目结构完整性")
    runner.run_test(test_directory_structure, "目录结构完整性")

    success = runner.print_summary()

    if success:
        print("\n[OK] All tests passed! Ready for development.")
        return 0
    else:
        print("\n[ERROR] Some tests failed. Please fix them before continuing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
