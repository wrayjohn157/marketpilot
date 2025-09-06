# 🔍 Code Quality Guide - MarketPilot

## 📋 **OVERVIEW**

This guide explains the robust code quality system implemented for MarketPilot, designed to catch issues early and maintain high code standards.

---

## 🚀 **QUICK START**

### **Setup Code Quality System**
```bash
# One-time setup
./setup_quality.sh

# Or manually
make setup
```

### **Daily Development Workflow**
```bash
# Before committing
make quick-smoke

# Before pushing
make ci-fast

# Full check before release
make ci-full
```

---

## 🛠️ **QUALITY TOOLS**

### **Code Formatting**
- **Black**: Python code formatting
- **isort**: Import sorting
- **Prettier**: Frontend formatting (if configured)

### **Linting**
- **Ruff**: Fast Python linting (replaces flake8)
- **ESLint**: Frontend linting (if configured)

### **Type Checking**
- **mypy**: Static type checking for Python

### **Security**
- **Bandit**: Security vulnerability scanning
- **Safety**: Dependency vulnerability checking

### **Testing**
- **pytest**: Test framework
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities

---

## 📊 **MAKEFILE COMMANDS**

### **Code Quality**
```bash
make format          # Format code with black and isort
make lint            # Run linting checks
make type            # Run type checking
make check-syntax    # Check Python syntax
make fix-syntax      # Fix common syntax issues
```

### **Testing**
```bash
make test            # Run all tests
make test-smoke      # Run smoke tests only
make test-unit       # Run unit tests only
make test-integration # Run integration tests only
make test-coverage   # Run tests with coverage
```

### **CI/CD**
```bash
make ci-fast         # Fast CI checks (lint + type + smoke)
make ci-full         # Full CI checks (all quality + all tests)
make ci-backend      # Backend CI checks
make ci-frontend     # Frontend CI checks
make ci-lint         # Linting CI checks
make ci-security     # Security CI checks
```

### **Development**
```bash
make setup           # Complete development setup
make install         # Install production dependencies
make install-dev     # Install development dependencies
make clean           # Clean up temporary files
make health          # Check system health
```

---

## 🔄 **PRE-COMMIT HOOKS**

### **Automatic Checks**
Pre-commit hooks run automatically on every commit:

1. **Syntax Check**: Python syntax validation
2. **Formatting**: Black and isort formatting
3. **Linting**: Ruff linting
4. **Type Checking**: mypy type checking
5. **Security**: Bandit and Safety scans
6. **Tests**: Smoke tests

### **Install Hooks**
```bash
make hooks
# or
pre-commit install
```

### **Run Hooks Manually**
```bash
make precommit
# or
pre-commit run --all-files
```

---

## 🧪 **TESTING STRATEGY**

### **Test Categories**

#### **Smoke Tests** (`@pytest.mark.smoke`)
- Quick tests that verify basic functionality
- Run on every commit
- Should complete in <30 seconds

#### **Unit Tests** (`@pytest.mark.unit`)
- Test individual functions and classes
- Fast, isolated tests
- High coverage

#### **Integration Tests** (`@pytest.mark.integration`)
- Test component interactions
- May require external services
- Slower but more comprehensive

### **Test Structure**
```
tests/
├── __init__.py
├── conftest.py          # Pytest configuration
├── test_smoke.py        # Smoke tests
├── unit/                # Unit tests
│   ├── test_config.py
│   ├── test_redis.py
│   └── test_dca.py
└── integration/         # Integration tests
    ├── test_pipeline.py
    └── test_api.py
```

### **Running Tests**
```bash
# All tests
make test

# Specific categories
make test-smoke
make test-unit
make test-integration

# With coverage
make test-coverage
```

---

## 🔒 **SECURITY CHECKS**

### **Dependency Scanning**
```bash
make ci-security
# or
safety check --file requirements.txt
```

### **Code Security Scanning**
```bash
bandit -r core dca fork indicators ml pipeline utils data dashboard_backend
```

### **Security in CI/CD**
Security checks run automatically in CI/CD pipeline:
- Dependency vulnerability scanning
- Code security analysis
- Secret detection

---

## 📈 **COVERAGE REPORTING**

### **Generate Coverage Report**
```bash
make test-coverage
```

### **Coverage Targets**
- **Minimum**: 80% overall coverage
- **Critical modules**: 90% coverage
- **New code**: 100% coverage

### **Coverage Reports**
- **Terminal**: Shows coverage summary
- **HTML**: Detailed report in `htmlcov/`
- **XML**: For CI/CD integration

---

## 🚨 **CI/CD PIPELINE**

### **Pipeline Stages**

#### **1. Backend Tests**
- Python syntax check
- Unit and integration tests
- Coverage reporting

#### **2. Frontend Tests**
- Node.js dependency installation
- Frontend tests
- Build verification

#### **3. Linting & Formatting**
- Python: black, isort, ruff, mypy
- Frontend: ESLint (if configured)

#### **4. Security Scanning**
- Dependency vulnerability check
- Code security analysis

#### **5. Build & Deploy** (main branch only)
- Docker image building
- Deployment to staging
- Smoke tests

### **Pipeline Status**
Check pipeline status at: `https://github.com/wrayjohn157/marketpilot/actions`

---

## 🐛 **TROUBLESHOOTING**

### **Common Issues**

#### **1. Syntax Errors**
```bash
# Check syntax
make check-syntax

# Fix common issues
make fix-syntax

# Format code
make format
```

#### **2. Import Errors**
```bash
# Check if all dependencies are installed
make install-dev

# Check Python path
python3 -c "import sys; print(sys.path)"
```

#### **3. Test Failures**
```bash
# Run specific test
pytest tests/test_specific.py -v

# Run with more verbose output
pytest tests/ -v -s

# Run only failed tests
pytest --lf
```

#### **4. Pre-commit Failures**
```bash
# Run pre-commit manually
pre-commit run --all-files

# Skip pre-commit for specific commit
git commit --no-verify -m "message"
```

#### **5. CI/CD Failures**
```bash
# Run CI checks locally
make ci-fast

# Check specific CI job
make ci-backend
make ci-frontend
make ci-lint
make ci-security
```

---

## 📋 **BEST PRACTICES**

### **Before Committing**
1. Run `make quick-smoke`
2. Fix any issues
3. Commit with descriptive message

### **Before Pushing**
1. Run `make ci-fast`
2. Ensure all checks pass
3. Push to feature branch

### **Before Merging**
1. Run `make ci-full`
2. Ensure all tests pass
3. Check coverage requirements
4. Merge to main branch

### **Code Quality Standards**
- **Formatting**: Use black and isort
- **Linting**: Fix all ruff warnings
- **Type Checking**: Add type hints, fix mypy errors
- **Testing**: Write tests for new features
- **Documentation**: Update docstrings and comments

---

## 🎯 **QUALITY METRICS**

### **Target Metrics**
- **Code Coverage**: >80%
- **Type Coverage**: >90%
- **Lint Issues**: 0
- **Security Issues**: 0
- **Test Pass Rate**: 100%

### **Monitoring**
- **CI/CD Pipeline**: Automated checks
- **Coverage Reports**: HTML and XML
- **Security Reports**: Bandit and Safety
- **Quality Gates**: Pre-commit hooks

---

## 🚀 **CONTINUOUS IMPROVEMENT**

### **Regular Tasks**
- **Weekly**: Review and update dependencies
- **Monthly**: Review coverage reports
- **Quarterly**: Update quality tools and standards

### **Adding New Checks**
1. Add tool to `requirements-dev.txt`
2. Add command to `Makefile`
3. Add hook to `.pre-commit-config.yaml`
4. Update CI/CD pipeline
5. Document in this guide

---

## 📞 **SUPPORT**

### **Getting Help**
1. **Check logs**: `tail -f logs/*.log`
2. **Run diagnostics**: `make health`
3. **Check documentation**: This guide
4. **Review CI/CD**: GitHub Actions

### **Common Commands**
```bash
# Quick health check
make health

# Full system check
make ci-full

# Clean and restart
make clean && make setup
```

**This robust quality system ensures MarketPilot maintains high code standards while being easy to use and refactor!** 🎯
