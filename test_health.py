"""
Test script to diagnose health check issues
"""

import requests
import json

def test_health_endpoints():
    """Test all health check endpoints."""
    base_url = "http://localhost:8000"
    
    endpoints = [
        "/health/live",
        "/health/ready",
        "/health",
        "/health/metrics"
    ]
    
    for endpoint in endpoints:
        url = f"{base_url}{endpoint}"
        print(f"\nTesting {endpoint}...")
        
        try:
            response = requests.get(url)
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"Response: {json.dumps(data, indent=2)}")
            else:
                print(f"Error Response: {response.text}")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_health_endpoints()
