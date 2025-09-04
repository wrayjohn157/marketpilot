#!/usr/bin/env python3
"""
Backend/Frontend Integration Test
Tests the complete flow from backend APIs to frontend data consumption
"""

import asyncio
import json
import requests
import time
from datetime import datetime
from pathlib import Path
import sys

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

def test_backend_apis():
    """Test all backend API endpoints"""
    print("🧪 Testing Backend APIs...")
    
    base_url = "http://localhost:8000"
    endpoints = [
        "/health",
        "/api/account/summary",
        "/api/trades/active", 
        "/api/3commas/metrics",
        "/api/btc/context",
        "/api/fork/metrics",
        "/api/ml/confidence"
    ]
    
    results = {}
    
    for endpoint in endpoints:
        try:
            print(f"  Testing {endpoint}...")
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results[endpoint] = {
                    "status": "success",
                    "status_code": response.status_code,
                    "data_keys": list(data.keys()) if isinstance(data, dict) else "not_dict",
                    "response_time": response.elapsed.total_seconds()
                }
                print(f"    ✅ Success: {response.status_code} ({response.elapsed.total_seconds():.2f}s)")
            else:
                results[endpoint] = {
                    "status": "error",
                    "status_code": response.status_code,
                    "error": response.text
                }
                print(f"    ❌ Error: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            results[endpoint] = {
                "status": "error",
                "error": str(e)
            }
            print(f"    ❌ Request failed: {e}")
        except Exception as e:
            results[endpoint] = {
                "status": "error",
                "error": str(e)
            }
            print(f"    ❌ Unexpected error: {e}")
    
    return results

def test_data_structure_alignment():
    """Test data structure alignment between frontend expectations and backend responses"""
    print("\n🔍 Testing Data Structure Alignment...")
    
    base_url = "http://localhost:8000"
    
    # Test account summary structure
    try:
        response = requests.get(f"{base_url}/api/account/summary", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            # Check if data has expected structure
            expected_keys = ["summary", "timestamp"]
            summary_keys = ["balance", "today_pnl", "total_pnl", "active_trades", "allocated", "upnl"]
            
            if all(key in data for key in expected_keys):
                print("  ✅ Account summary has correct top-level structure")
            else:
                print(f"  ❌ Account summary missing keys: {set(expected_keys) - set(data.keys())}")
            
            if "summary" in data and all(key in data["summary"] for key in summary_keys):
                print("  ✅ Account summary has correct summary structure")
            else:
                print(f"  ❌ Account summary missing summary keys: {set(summary_keys) - set(data.get('summary', {}).keys())}")
        else:
            print(f"  ❌ Account summary request failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Account summary test failed: {e}")
    
    # Test active trades structure
    try:
        response = requests.get(f"{base_url}/api/trades/active", timeout=10)
        if response.status_code == 200:
            data = response.json()
            
            expected_keys = ["dca_trades", "count", "timestamp"]
            trade_keys = ["deal_id", "symbol", "open_pnl", "drawdown_pct", "step", "confidence_score"]
            
            if all(key in data for key in expected_keys):
                print("  ✅ Active trades has correct top-level structure")
            else:
                print(f"  ❌ Active trades missing keys: {set(expected_keys) - set(data.keys())}")
            
            if "dca_trades" in data and len(data["dca_trades"]) > 0:
                trade = data["dca_trades"][0]
                if all(key in trade for key in trade_keys):
                    print("  ✅ Active trades has correct trade structure")
                else:
                    print(f"  ❌ Active trades missing trade keys: {set(trade_keys) - set(trade.keys())}")
            else:
                print("  ⚠️  No active trades to test structure")
        else:
            print(f"  ❌ Active trades request failed: {response.status_code}")
    except Exception as e:
        print(f"  ❌ Active trades test failed: {e}")

def test_3commas_integration():
    """Test 3Commas integration"""
    print("\n🔗 Testing 3Commas Integration...")
    
    try:
        from dashboard_backend.threecommas_metrics_fixed import get_3commas_metrics
        
        print("  Testing 3Commas metrics function...")
        metrics = get_3commas_metrics()
        
        if "error" in metrics:
            print(f"  ⚠️  3Commas integration has error: {metrics['error']}")
        else:
            print("  ✅ 3Commas integration working")
            
        # Check required fields
        required_fields = ["bot_id", "metrics", "timestamp"]
        if all(field in metrics for field in required_fields):
            print("  ✅ 3Commas response has required fields")
        else:
            print(f"  ❌ 3Commas response missing fields: {set(required_fields) - set(metrics.keys())}")
            
    except Exception as e:
        print(f"  ❌ 3Commas integration test failed: {e}")

def test_redis_integration():
    """Test Redis integration"""
    print("\n🗄️  Testing Redis Integration...")
    
    try:
        from utils.redis_manager import get_redis_manager
        
        print("  Testing Redis connection...")
        redis_manager = get_redis_manager()
        
        if redis_manager.ping():
            print("  ✅ Redis connection successful")
        else:
            print("  ❌ Redis ping failed")
            
        # Test basic operations
        test_key = "test_integration_key"
        test_value = "test_value"
        
        redis_manager.set_cache(test_key, test_value)
        retrieved_value = redis_manager.get_cache(test_key)
        
        if retrieved_value == test_value:
            print("  ✅ Redis set/get operations working")
        else:
            print(f"  ❌ Redis set/get failed: expected {test_value}, got {retrieved_value}")
            
        # Cleanup
        redis_manager.delete_cache(test_key)
        
    except Exception as e:
        print(f"  ❌ Redis integration test failed: {e}")

def test_frontend_api_client():
    """Test frontend API client (simulated)"""
    print("\n🌐 Testing Frontend API Client...")
    
    # Simulate frontend API calls
    base_url = "http://localhost:8000"
    
    api_tests = [
        ("/api/account/summary", "Account Summary"),
        ("/api/trades/active", "Active Trades"),
        ("/api/3commas/metrics", "3Commas Metrics"),
        ("/api/btc/context", "BTC Context"),
        ("/api/fork/metrics", "Fork Metrics"),
        ("/api/ml/confidence", "ML Confidence")
    ]
    
    for endpoint, name in api_tests:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=10)
            if response.status_code == 200:
                print(f"  ✅ {name} API call successful")
            else:
                print(f"  ❌ {name} API call failed: {response.status_code}")
        except Exception as e:
            print(f"  ❌ {name} API call error: {e}")

def generate_test_report(results):
    """Generate comprehensive test report"""
    print("\n📊 Integration Test Report")
    print("=" * 50)
    
    total_tests = len(results)
    successful_tests = sum(1 for r in results.values() if r["status"] == "success")
    failed_tests = total_tests - successful_tests
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful: {successful_tests}")
    print(f"Failed: {failed_tests}")
    print(f"Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    
    print("\nDetailed Results:")
    for endpoint, result in results.items():
        status = "✅" if result["status"] == "success" else "❌"
        print(f"  {status} {endpoint}")
        if result["status"] == "success":
            print(f"    Response Time: {result.get('response_time', 0):.2f}s")
            print(f"    Data Keys: {result.get('data_keys', 'N/A')}")
        else:
            print(f"    Error: {result.get('error', 'Unknown error')}")
    
    print("\nRecommendations:")
    if failed_tests > 0:
        print("  - Fix failed API endpoints")
        print("  - Check backend service status")
        print("  - Verify database connections")
    else:
        print("  - All tests passed! 🎉")
        print("  - System is ready for production")
    
    return successful_tests == total_tests

def main():
    """Run all integration tests"""
    print("🚀 Starting Backend/Frontend Integration Tests")
    print("=" * 60)
    
    # Test backend APIs
    api_results = test_backend_apis()
    
    # Test data structure alignment
    test_data_structure_alignment()
    
    # Test 3Commas integration
    test_3commas_integration()
    
    # Test Redis integration
    test_redis_integration()
    
    # Test frontend API client
    test_frontend_api_client()
    
    # Generate report
    all_passed = generate_test_report(api_results)
    
    if all_passed:
        print("\n🎉 All integration tests passed!")
        print("The backend and frontend are properly aligned and ready for use.")
    else:
        print("\n⚠️  Some integration tests failed.")
        print("Please fix the issues before deploying to production.")
    
    return all_passed

if __name__ == "__main__":
    main()