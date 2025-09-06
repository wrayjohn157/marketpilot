#!/usr/bin/env python3
"""
MarketPilot Health Check Script
Used by Docker containers for health monitoring
"""

import sys
import time
import requests
from pathlib import Path

def check_redis():
    """Check Redis connectivity"""
    try:
        from utils.redis_manager import get_redis_manager
        r = get_redis_manager()
        r.ping()
        return True
    except Exception as e:
        print(f"❌ Redis check failed: {e}")
        return False

def check_api_server():
    """Check if FastAPI server is responding"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ API server check failed: {e}")
        return False

def check_critical_files():
    """Check if critical configuration files exist"""
    critical_files = [
        "config/unified_config_manager.py",
        "requirements.txt",
        "ml/unified_ml_pipeline.py"
    ]
    
    for file_path in critical_files:
        if not Path(file_path).exists():
            print(f"❌ Critical file missing: {file_path}")
            return False
    
    return True

def check_ml_models():
    """Check if ML models are available"""
    try:
        model_dir = Path("ml/models")
        if not model_dir.exists():
            print("⚠️  ML models directory not found, continuing without ML")
            return True
        
        # Check for key models
        key_models = [
            "xgb_recovery_model.pkl",
            "safu_exit_model.pkl",
            "confidence_model.pkl"
        ]
        
        available_models = list(model_dir.glob("*.pkl"))
        if len(available_models) == 0:
            print("⚠️  No ML models found, continuing without ML predictions")
        else:
            print(f"✅ Found {len(available_models)} ML models")
        
        return True
    except Exception as e:
        print(f"⚠️  ML model check error: {e}")
        return True  # Non-critical

def main():
    """Main health check function"""
    print("🔍 Running MarketPilot health checks...")
    
    checks = [
        ("Critical Files", check_critical_files),
        ("Redis Connection", check_redis),
        ("ML Models", check_ml_models),
        # ("API Server", check_api_server),  # Only check if server is supposed to be running
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {check_name}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"❌ FAIL {check_name}: {e}")
            all_passed = False
    
    if all_passed:
        print("🎉 All health checks passed!")
        sys.exit(0)
    else:
        print("⚠️  Some health checks failed")
        sys.exit(1)

if __name__ == "__main__":
    main()

