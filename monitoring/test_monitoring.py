#!/usr/bin/env python3
"""
Test script for Market7 monitoring setup
"""

import requests
import time
import json
from datetime import datetime

def test_service(url, service_name, expected_status=200):
    """Test if a service is responding"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == expected_status:
            print(f"✅ {service_name}: OK ({response.status_code})")
            return True
        else:
            print(f"❌ {service_name}: FAILED ({response.status_code})")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {service_name}: ERROR - {e}")
        return False

def test_grafana_dashboards(base_url, admin_password):
    """Test Grafana dashboards"""
    try:
        # Login to Grafana
        session = requests.Session()
        login_data = {
            "user": "admin",
            "password": admin_password
        }
        
        response = session.post(f"{base_url}/login", json=login_data)
        if response.status_code != 200:
            print("❌ Grafana: Login failed")
            return False
        
        # Test dashboard access
        dashboards = [
            "market7-overview",
            "market7-trading"
        ]
        
        for dashboard in dashboards:
            response = session.get(f"{base_url}/api/dashboards/uid/{dashboard}")
            if response.status_code == 200:
                print(f"✅ Grafana Dashboard {dashboard}: OK")
            else:
                print(f"❌ Grafana Dashboard {dashboard}: FAILED")
        
        return True
    except Exception as e:
        print(f"❌ Grafana Dashboard Test: ERROR - {e}")
        return False

def test_prometheus_targets(base_url):
    """Test Prometheus targets"""
    try:
        response = requests.get(f"{base_url}/api/v1/targets")
        if response.status_code == 200:
            data = response.json()
            targets = data.get('data', {}).get('activeTargets', [])
            
            print(f"📊 Prometheus Targets ({len(targets)} total):")
            for target in targets:
                status = "✅" if target['health'] == 'up' else "❌"
                print(f"  {status} {target['job']}: {target['scrapeUrl']}")
            
            return True
        else:
            print(f"❌ Prometheus Targets: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Prometheus Targets: ERROR - {e}")
        return False

def test_alertmanager_config(base_url):
    """Test Alertmanager configuration"""
    try:
        response = requests.get(f"{base_url}/api/v1/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Alertmanager: OK")
            print(f"  Version: {data.get('version', 'Unknown')}")
            print(f"  Uptime: {data.get('uptime', 'Unknown')}")
            return True
        else:
            print(f"❌ Alertmanager: FAILED ({response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Alertmanager: ERROR - {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Testing Market7 Monitoring Stack")
    print("=" * 50)
    
    # Configuration
    services = {
        "Grafana": "http://localhost:3001",
        "Prometheus": "http://localhost:9090",
        "Alertmanager": "http://localhost:9093",
        "Traefik": "http://localhost:8080"
    }
    
    results = {}
    
    # Test basic service availability
    print("\n🔍 Testing Service Availability:")
    for service, url in services.items():
        results[service] = test_service(url, service)
    
    # Test Prometheus targets
    print("\n📊 Testing Prometheus Targets:")
    if results.get("Prometheus"):
        test_prometheus_targets(services["Prometheus"])
    
    # Test Alertmanager
    print("\n🔔 Testing Alertmanager:")
    if results.get("Alertmanager"):
        test_alertmanager_config(services["Alertmanager"])
    
    # Test Grafana dashboards
    print("\n📈 Testing Grafana Dashboards:")
    if results.get("Grafana"):
        test_grafana_dashboards(services["Grafana"], "admin123")
    
    # Summary
    print("\n📋 Test Summary:")
    print("=" * 50)
    
    total_services = len(services)
    working_services = sum(1 for result in results.values() if result)
    
    print(f"Services Working: {working_services}/{total_services}")
    
    if working_services == total_services:
        print("🎉 All services are working correctly!")
        print("\n🌐 Access URLs:")
        print("  • Grafana: http://localhost:3001 (admin/admin123)")
        print("  • Prometheus: http://localhost:9090")
        print("  • Alertmanager: http://localhost:9093")
        print("  • Traefik Dashboard: http://localhost:8080")
    else:
        print("⚠️  Some services are not working. Check the logs above.")
        print("\n🔧 Troubleshooting:")
        print("  1. Check if Docker containers are running:")
        print("     docker-compose -f docker-compose.monitoring.yml ps")
        print("  2. Check service logs:")
        print("     docker-compose -f docker-compose.monitoring.yml logs")
        print("  3. Restart services:")
        print("     docker-compose -f docker-compose.monitoring.yml restart")

if __name__ == "__main__":
    main()