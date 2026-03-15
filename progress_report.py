"""
项目进度报告生成器
每小时运行一次，生成开发进度报告
"""
import os
import sys
from datetime import datetime
import subprocess

def get_git_status():
    """获取git状态"""
    try:
        status = subprocess.check_output(['git', 'status', '--short'],
                                         stderr=subprocess.DEVNULL).decode('utf-8')
        return status.strip()
    except:
        return "N/A"

def get_git_log():
    """获取最近的git提交"""
    try:
        log = subprocess.check_output(['git', 'log', '--oneline', '-5'],
                                      stderr=subprocess.DEVNULL).decode('utf-8')
        return log.strip()
    except:
        return "N/A"

def get_file_stats():
    """获取文件统计"""
    py_files = 0
    md_files = 0
    other_files = 0

    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'memory' in root:
            continue
        for file in files:
            if file.endswith('.py'):
                py_files += 1
            elif file.endswith('.md'):
                md_files += 1
            else:
                other_files += 1

    return py_files, md_files, other_files

def check_tests():
    """检查测试状态"""
    try:
        result = subprocess.run([sys.executable, 'test_cleanup.py'],
                               capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return "PASS"
        else:
            return f"FAIL (exit code {result.returncode})"
    except Exception as e:
        return f"ERROR: {str(e)}"

def generate_report():
    """生成进度报告"""
    now = datetime.now()
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    py_files, md_files, other_files = get_file_stats()
    git_status = get_git_status()
    git_log = get_git_log()
    test_status = check_tests()

    report = f"""
{'='*60}
Project Progress Report
{'='*60}
Time: {timestamp}

[STATS] Code Statistics
- Python files: {py_files}
- Markdown docs: {md_files}
- Other files: {other_files}

[TEST] Test Status
- Auto tests: {test_status}

[GIT] Git Status
- Working tree: {'Clean' if not git_status else 'Uncommitted changes'}

[COMMITS] Recent commits
{git_log}

{'='*60}
"""
    return report

def main():
    """主函数"""
    report = generate_report()
    print(report)

    # 保存到文件
    report_file = "PROGRESS_REPORT.md"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n报告已保存到: {report_file}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
