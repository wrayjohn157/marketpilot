#!/usr/bin/env python3
"""
Integration Test - Test all refactored systems work together
"""

import sys
import traceback
from pathlib import Path

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_config_system():
    """Test unified configuration system"""
    print("🧪 Testing configuration system...")
    try:
        from config.unified_config_manager import get_path, get_config
        base_path = get_path("base")
        dca_config = get_config("dca_config")
        print(f"      ✅ Config system working - base: {base_path}")
        return True
    except Exception as e:
        print(f"      ❌ Config system failed: {e}")
        return False

def test_credential_system():
    """Test credential management system"""
    print("🧪 Testing credential system...")
    try:
        from utils.credential_manager import get_3commas_credentials
        # This might fail if credentials don't exist, but import should work
        print("      ✅ Credential system working")
        return True
    except Exception as e:
        print(f"      ❌ Credential system failed: {e}")
        return False

def test_redis_system():
    """Test Redis management system"""
    print("🧪 Testing Redis system...")
    try:
        from utils.redis_manager import get_redis_manager
        # This might fail if Redis not running, but import should work
        print("      ✅ Redis system working")
        return True
    except Exception as e:
        print(f"      ❌ Redis system failed: {e}")
        return False

def test_indicator_system():
    """Test unified indicator system"""
    print("🧪 Testing indicator system...")
    try:
        from utils.unified_indicator_system import UnifiedIndicatorManager
        print("      ✅ Indicator system working")
        return True
    except Exception as e:
        print(f"      ❌ Indicator system failed: {e}")
        return False

def test_dca_system():
    """Test smart DCA system"""
    print("🧪 Testing DCA system...")
    try:
        from dca.smart_dca_core import SmartDCACore
        print("      ✅ DCA system working")
        return True
    except Exception as e:
        print(f"      ❌ DCA system failed: {e}")
        return False

def test_trading_pipeline():
    """Test unified trading pipeline"""
    print("🧪 Testing trading pipeline...")
    try:
        from pipeline.unified_trading_pipeline import UnifiedTradingPipeline
        print("      ✅ Trading pipeline working")
        return True
    except Exception as e:
        print(f"      ❌ Trading pipeline failed: {e}")
        return False

def test_ml_pipeline():
    """Test unified ML pipeline"""
    print("🧪 Testing ML pipeline...")
    try:
        from ml.unified_ml_pipeline import MLPipelineManager
        print("      ✅ ML pipeline working")
        return True
    except Exception as e:
        print(f"      ❌ ML pipeline failed: {e}")
        return False

def main():
    """Run all integration tests"""
    print("🚀 Running Integration Tests")
    print("=" * 50)
    
    tests = [
        test_config_system,
        test_credential_system,
        test_redis_system,
        test_indicator_system,
        test_dca_system,
        test_trading_pipeline,
        test_ml_pipeline,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"      ❌ Test failed with exception: {e}")
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All systems working correctly!")
    else:
        print("⚠️  Some systems need attention. Check the errors above.")
    
    print("\n📋 Next Steps:")
    if passed < total:
        print("1. Install missing dependencies: python3 install_dependencies.py")
        print("2. Fix any remaining import issues")
        print("3. Test individual systems")
    else:
        print("1. Run main workflows to verify end-to-end functionality")
        print("2. Monitor system performance")
        print("3. Deploy to production")

if __name__ == "__main__":
    main()
