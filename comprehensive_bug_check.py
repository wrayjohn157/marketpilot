#!/usr/bin/env python3
"""
Comprehensive bug check and dependency validation script
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path

def check_python_syntax():
    """Check Python syntax for all .py files"""
    print("🔍 Checking Python syntax...")
    
    syntax_errors = []
    python_files = []
    
    # Find all Python files
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        if any(skip in root for skip in [".git", "__pycache__", "venv", ".pytest_cache"]):
            continue
            
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    
    print(f"Found {len(python_files)} Python files to check")
    
    for file_path in python_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                compile(f.read(), file_path, 'exec')
        except SyntaxError as e:
            syntax_errors.append(f"{file_path}:{e.lineno}: {e.msg}")
        except Exception as e:
            syntax_errors.append(f"{file_path}: {str(e)}")
    
    if syntax_errors:
        print("❌ Syntax errors found:")
        for error in syntax_errors:
            print(f"  {error}")
        return False
    else:
        print("✅ All Python files have valid syntax")
        return True

def check_imports():
    """Check if all required modules can be imported"""
    print("\n🔍 Checking imports...")
    
    # Add current directory to path
    sys.path.insert(0, ".")
    
    import_tests = [
        ("config.unified_config_manager", "get_path"),
        ("utils.credential_manager", "get_credential_manager"),
        ("utils.redis_manager", "get_redis_manager"),
        ("dca.smart_dca_core", "SmartDCACore"),
        ("ml.unified_ml_pipeline", "MLPipelineManager"),
        ("utils.unified_indicator_system", "UnifiedIndicatorManager"),
        ("pipeline.unified_trading_pipeline", "UnifiedTradingPipeline"),
        ("dashboard_backend.main", "app"),
    ]
    
    missing_modules = []
    import_errors = []
    
    for module_name, function_name in import_tests:
        try:
            module = importlib.import_module(module_name)
            if hasattr(module, function_name):
                print(f"✅ {module_name}.{function_name}")
            else:
                import_errors.append(f"{module_name} missing {function_name}")
        except ImportError as e:
            missing_modules.append(f"{module_name}: {str(e)}")
        except Exception as e:
            import_errors.append(f"{module_name}: {str(e)}")
    
    if missing_modules:
        print("\n❌ Missing dependencies:")
        for missing in missing_modules:
            print(f"  {missing}")
    
    if import_errors:
        print("\n❌ Import errors:")
        for error in import_errors:
            print(f"  {error}")
    
    return len(missing_modules) == 0 and len(import_errors) == 0

def check_requirements():
    """Check if requirements.txt has all needed dependencies"""
    print("\n🔍 Checking requirements.txt...")
    
    # Read current requirements
    with open("requirements.txt", "r") as f:
        current_reqs = f.read()
    
    # Required packages that might be missing
    required_packages = [
        "ta",  # Technical Analysis
        "influxdb-client",  # InfluxDB client
        "psycopg2-binary",  # PostgreSQL
        "matplotlib",  # Plotting
        "seaborn",  # Statistical plotting
        "plotly",  # Interactive plots
        "dash",  # Dashboard framework
        "dash-bootstrap-components",  # Bootstrap components
        "cryptography",  # Security
        "python-jose[cryptography]",  # JWT tokens
        "passlib[bcrypt]",  # Password hashing
        "python-multipart",  # File uploads
        "uvicorn[standard]",  # ASGI server
        "gunicorn",  # WSGI server
        "celery",  # Task queue
        "flower",  # Celery monitoring
        "prometheus-client",  # Prometheus metrics
        "structlog",  # Structured logging
        "sentry-sdk[fastapi]",  # Error tracking
    ]
    
    missing_packages = []
    for package in required_packages:
        if package not in current_reqs:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing packages in requirements.txt:")
        for package in missing_packages:
            print(f"  {package}")
        return False
    else:
        print("✅ All required packages are in requirements.txt")
        return True

def check_file_structure():
    """Check if all expected files and directories exist"""
    print("\n🔍 Checking file structure...")
    
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        "pytest.ini",
        ".flake8",
        ".pre-commit-config.yaml",
        "Makefile",
        "README.md",
        "deploy.sh",
        "main_orchestrator.py",
    ]
    
    required_dirs = [
        "config",
        "utils", 
        "dca",
        "ml",
        "pipeline",
        "indicators",
        "dashboard_backend",
        "dashboard_frontend",
        "monitoring",
        "tests",
        "docs",
    ]
    
    missing_files = []
    missing_dirs = []
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    for dir_path in required_dirs:
        if not os.path.isdir(dir_path):
            missing_dirs.append(dir_path)
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  {file_path}")
    
    if missing_dirs:
        print("❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"  {dir_path}")
    
    return len(missing_files) == 0 and len(missing_dirs) == 0

def check_config_files():
    """Check if all config files are valid"""
    print("\n🔍 Checking config files...")
    
    config_files = [
        "config/unified_config_manager.py",
        "config/paths_config.yaml",
        "config/smart_dca_config.yaml",
        "config/unified_pipeline_config.yaml",
        "config/ml_pipeline_config.yaml",
    ]
    
    config_errors = []
    
    for config_file in config_files:
        if not os.path.exists(config_file):
            config_errors.append(f"Missing: {config_file}")
            continue
            
        try:
            if config_file.endswith('.yaml') or config_file.endswith('.yml'):
                import yaml
                with open(config_file, 'r') as f:
                    yaml.safe_load(f)
            elif config_file.endswith('.json'):
                import json
                with open(config_file, 'r') as f:
                    json.load(f)
        except Exception as e:
            config_errors.append(f"Invalid {config_file}: {str(e)}")
    
    if config_errors:
        print("❌ Config file errors:")
        for error in config_errors:
            print(f"  {error}")
        return False
    else:
        print("✅ All config files are valid")
        return True

def run_pre_commit_checks():
    """Run pre-commit hooks"""
    print("\n🔍 Running pre-commit checks...")
    
    try:
        # Check if pre-commit is installed
        result = subprocess.run(["pre-commit", "--version"], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ pre-commit not installed")
            return False
        
        # Run pre-commit on all files
        result = subprocess.run(["pre-commit", "run", "--all-files"], 
                              capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ Pre-commit checks failed:")
            print(result.stdout)
            print(result.stderr)
            return False
        else:
            print("✅ All pre-commit checks passed")
            return True
            
    except FileNotFoundError:
        print("❌ pre-commit not found in PATH")
        return False

def main():
    """Run comprehensive bug check"""
    print("🔍 COMPREHENSIVE BUG CHECK")
    print("=" * 50)
    
    checks = [
        ("Python Syntax", check_python_syntax),
        ("File Structure", check_file_structure),
        ("Config Files", check_config_files),
        ("Requirements", check_requirements),
        ("Imports", check_imports),
        ("Pre-commit", run_pre_commit_checks),
    ]
    
    results = {}
    
    for check_name, check_func in checks:
        print(f"\n{'='*20} {check_name} {'='*20}")
        try:
            results[check_name] = check_func()
        except Exception as e:
            print(f"❌ {check_name} check failed with error: {e}")
            results[check_name] = False
    
    # Summary
    print(f"\n{'='*50}")
    print("📊 CHECK SUMMARY")
    print(f"{'='*50}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for check_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{check_name:20} {status}")
    
    print(f"\nOverall: {passed}/{total} checks passed")
    
    if passed == total:
        print("🎉 All checks passed! Repository is ready.")
        return True
    else:
        print("⚠️  Some checks failed. Please fix the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)