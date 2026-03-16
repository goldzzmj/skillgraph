# 📋 Phase 5 v1.0.1 - Task 2.1: Static Security Tools Integration

## 📊 Task Overview

**Task:** Task 2.1 - Static Security Tools Integration  
**Priority:** P0 (Critical)  
**Estimated Time:** 2-3 days  
**Status:** 🚀 Starting

---

## 🎯 Task Objectives

### 1. Integrate Semgrep (Code Pattern Matching)

**Goals:**
- ✅ Integrate Semgrep for code pattern matching
- ✅ Create custom security rules
- ✅ Add to CI/CD pipeline
- ✅ Scan for code injection vulnerabilities

**Expected Results:**
- Static analysis coverage: 20% → 50% (+30%)
- Code injection detection: New feature
- Custom security rules: Complete
- CI/CD integration: Complete

---

### 2. Integrate Bandit (Python Security Checker)

**Goals:**
- ✅ Integrate Bandit for Python security checks
- ✅ Create custom security rules
- ✅ Add to CI/CD pipeline
- ✅ Scan for Python-specific vulnerabilities

**Expected Results:**
- Python security coverage: 20% → 60% (+40%)
- Python vulnerabilities detection: Complete
- Custom security rules: Complete
- CI/CD integration: Complete

---

### 3. Integrate CodeQL (Deep Analysis)

**Goals:**
- ✅ Integrate CodeQL for deep code analysis
- ✅ Create custom security rules
- ✅ Add to CI/CD pipeline
- ✅ Scan for complex vulnerabilities

**Expected Results:**
- Deep analysis coverage: 20% → 40% (+20%)
- Complex vulnerability detection: Complete
- Custom security rules: Complete
- CI/CD integration: Complete

---

## 📋 Implementation Plan

### Step 1: Semgrep Integration (Day 1)

**Actions:**
1. Install Semgrep
2. Create Semgrep rules
3. Add Semgrep to CI/CD
4. Test Semgrep scanning
5. Generate security reports

**Files:**
- `.semgrep/rules/` - Custom security rules
- `.github/workflows/semgrep-scan.yml` - Semgrep CI/CD workflow
- `src/skillgraph/security/semgrep_scanner.py` - Semgrep scanner wrapper

**Expected Time:** 1 day

---

### Step 2: Bandit Integration (Day 1)

**Actions:**
1. Install Bandit
2. Create Bandit configuration
3. Add Bandit to CI/CD
4. Test Bandit scanning
5. Generate security reports

**Files:**
- `.bandit` - Bandit configuration
- `.github/workflows/bandit-scan.yml` - Bandit CI/CD workflow
- `src/skillgraph/security/bandit_scanner.py` - Bandit scanner wrapper

**Expected Time:** 1 day

---

### Step 3: CodeQL Integration (Day 2-3)

**Actions:**
1. Install CodeQL CLI
2. Create CodeQL queries
3. Add CodeQL to CI/CD
4. Test CodeQL scanning
5. Generate security reports

**Files:**
- `.codeql/queries/` - Custom CodeQL queries
- `.github/workflows/codeql-scan.yml` - CodeQL CI/CD workflow
- `src/skillgraph/security/codeql_scanner.py` - CodeQL scanner wrapper

**Expected Time:** 1-2 days

---

## 📊 Security Rules

### Semgrep Custom Rules

**Code Injection:**
```yaml
rules:
  - id: python-code-injection
    languages: [python]
    message: Detected potential code injection
    severity: ERROR
    patterns:
      - pattern: eval(...)
      - pattern: exec(...)
      - pattern: subprocess.call(..., shell=True)
```

**Command Injection:**
```yaml
rules:
  - id: python-command-injection
    languages: [python]
    message: Detected potential command injection
    severity: ERROR
    patterns:
      - pattern: os.system(...)
      - pattern: subprocess.call(...)
      - pattern: subprocess.Popen(...)
```

**SQL Injection:**
```yaml
rules:
  - id: python-sql-injection
    languages: [python]
    message: Detected potential SQL injection
    severity: ERROR
    patterns:
      - pattern: execute(f"SELECT * FROM ...")
      - pattern: execute(f"INSERT INTO ...")
      - pattern: execute(f"UPDATE ... SET ...")
```

---

### Bandit Configuration

```ini
[bandit]
exclude_dirs = ['/venv/', '/tests/']
tests = ['B201', 'B301', 'B302', 'B303', 'B304', 'B305', 'B306', 'B307', 'B308', 'B309', 'B310', 'B311', 'B312', 'B313', 'B401', 'B402', 'B403', 'B404', 'B501', 'B502', 'B503', 'B504', 'B505', 'B506', 'B601', 'B602', 'B603', 'B604', 'B605', 'B606', 'B607', 'B608', 'B609', 'B610', 'B611']
skips = ['B101', 'B601']
```

---

### CodeQL Queries

**Python Code Injection:**
```ql
import python
from CodeQL

select * where exists(
  eval($expr),
  exec($expr)
)
```

**Python Command Injection:**
```ql
import python
from CodeQL

select * where exists(
  os.system($cmd),
  subprocess.call($cmd, shell=True),
  subprocess.Popen($cmd, shell=True)
)
```

---

## 📊 Implementation Details

### Semgrep Scanner

**Functionality:**
- Scan code for security vulnerabilities
- Detect code injection patterns
- Detect command injection patterns
- Detect SQL injection patterns
- Generate detailed reports

**API:**
```python
def scan_code(code_path: str, rules: List[str]) -> Dict[str, Any]:
    """Scan code with Semgrep."""
    # Semgrep scanning implementation
    pass

def generate_report(scan_results: Dict[str, Any]) -> str:
    """Generate security report."""
    # Report generation
    pass
```

---

### Bandit Scanner

**Functionality:**
- Scan Python code for security issues
- Detect common Python vulnerabilities
- Check for hardcoded passwords
- Check for insecure random usage
- Check for SQL injection

**API:**
```python
def scan_python(code_path: str) -> Dict[str, Any]:
    """Scan Python code with Bandit."""
    # Bandit scanning implementation
    pass

def generate_report(scan_results: Dict[str, Any]) -> str:
    """Generate security report."""
    # Report generation
    pass
```

---

### CodeQL Scanner

**Functionality:**
- Deep code analysis
- Detect complex vulnerabilities
- Find code paths to vulnerabilities
- Analyze data flow

**API:**
```python
def analyze_codeql(code_path: str) -> Dict[str, Any]:
    """Analyze code with CodeQL."""
    # CodeQL analysis implementation
    pass

def generate_report(analysis_results: Dict[str, Any]) -> str:
    """Generate security report."""
    # Report generation
    pass
```

---

## 📊 CI/CD Integration

### GitHub Actions Workflow

**Semgrep Scan:**
```yaml
name: Semgrep Security Scan

on: [push, pull_request]

jobs:
  semgrep-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Semgrep
        run: pip install semgrep
      - name: Scan with Semgrep
        run: semgrep --config=.semgrep/rules/ --verbose --json
```

**Bandit Scan:**
```yaml
name: Bandit Security Scan

on: [push, pull_request]

jobs:
  bandit-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install Bandit
        run: pip install bandit[toml]
      - name: Scan with Bandit
        run: bandit -r . -f json
```

**CodeQL Scan:**
```yaml
name: CodeQL Security Scan

on: [push, pull_request]

jobs:
  codeql-scan:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
    strategy:
      fail-fast: false
      matrix:
        language: ['python']
    steps:
      - uses: actions/checkout@v3
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: ${{ matrix.language }}
          queries: .codeql/queries/
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2
        with:
          queries: .codeql/queries/
```

---

## 📊 Expected Results

### Static Analysis Coverage

| Tool | v1.0.0 | v1.0.1 | Improvement |
|------|--------|----------|-------------|
| Semgrep Coverage | 20% | 50% | +30% |
| Bandit Coverage | 20% | 60% | +40% |
| CodeQL Coverage | 0% | 40% | +40% |
| Total Coverage | 20% | 70% | +50% |

### Vulnerability Detection

| Vulnerability Type | v1.0.0 | v1.0.1 | Improvement |
|----------------|--------|----------|-------------|
| Code Injection | No | Yes | New feature |
| Command Injection | No | Yes | New feature |
| SQL Injection | No | Yes | New feature |
| Python Security | No | Yes | New feature |
| Complex Vulnerabilities | No | Yes | New feature |

---

## 📋 Next Steps

### Immediate Actions (Day 1)

1. **Install Semgrep** ⏳
   ```bash
   pip install semgrep
   ```

2. **Install Bandit** ⏳
   ```bash
   pip install bandit[toml]
   ```

3. **Install CodeQL CLI** ⏳
   ```bash
   # Download from GitHub releases
   ```

4. **Create Semgrep rules** ⏳
   - Code injection rules
   - Command injection rules
   - SQL injection rules

5. **Create CI/CD workflows** ⏳
   - Semgrep workflow
   - Bandit workflow
   - CodeQL workflow

---

## 📊 Success Criteria

### Task 2.1 Success Criteria

- [ ] Semgrep integrated and tested
- [ ] Bandit integrated and tested
- [ ] CodeQL integrated and tested
- [ ] Custom security rules created
- [ ] CI/CD workflows created
- [ ] Security scan reports generated
- [ ] Static analysis coverage: 70%

---

## 📊 Task Dependencies

**Depends on:** Task 2.2 (LLM Security Tools Integration)

**Blocks:** Task 2.3 (Agent Security Tools Integration)
**Blocked by:** None

---

## 📊 Risk Assessment

**Risk Level:** Low  
**Risks:**
- Semgrep false positives: Medium
- Bandit false positives: Low
- CodeQL complexity: Medium
- CI/CD performance impact: Low

**Mitigation:**
- Gradual rollout
- Extensive testing
- Performance monitoring

---

## 📊 Timeline

### Day 1 (2026-03-17)
- Install Semgrep, Bandit, CodeQL
- Create Semgrep rules
- Create Bandit configuration
- Create CodeQL queries

### Day 2 (2026-03-18)
- Integrate Semgrep scanner
- Integrate Bandit scanner
- Create CI/CD workflows
- Test security scanners

### Day 3 (2026-03-19)
- Integrate CodeQL scanner
- Complete CI/CD integration
- Generate security reports
- Final validation

---

## 📊 Files to be Created

**Security Scanner Files:**
- `src/skillgraph/security/__init__.py`
- `src/skillgraph/security/semgrep_scanner.py`
- `src/skillgraph/security/bandit_scanner.py`
- `src/skillgraph/security/codeql_scanner.py`
- `src/skillgraph/security/report_generator.py`

**Security Rules:**
- `.semgrep/rules/code-injection.yaml`
- `.semgrep/rules/command-injection.yaml`
- `.semgrep/rules/sql-injection.yaml`

**CI/CD Workflows:**
- `.github/workflows/semgrep-scan.yml`
- `.github/workflows/bandit-scan.yml`
- `.github/workflows/codeql-scan.yml`

---

## 📊 Expected Impact

### Static Analysis Coverage

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Static Analysis Coverage | 20% | 70% | +50% |
| Security Tools | 0 | 3 | +3 |
| Security Rules | 0 | 15+ | +15+ |
| CI/CD Workflows | 0 | 3 | +3 |

---

**Task Status:** 🚀 Starting  
**Expected Time:** 2-3 days  
**Priority:** P0 (Critical)

---

**Next Steps:**
1. ⏳ Install security tools (Semgrep, Bandit, CodeQL)
2. ⏳ Create custom security rules
3. ⏳ Integrate security scanners
4. ⏳ Create CI/CD workflows
5. ⏳ Test and validate

---

**需要我：**
1. 开始实现Semgrep集成？
2. 还是创建更详细的实施计划？
3. 或者有其他需求？

**告诉我下一步做什么！**