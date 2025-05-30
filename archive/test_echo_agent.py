#!/usr/bin/env python3
"""
Test script for the Echo Agent Service
Tests all Masumi Agentic Service API endpoints
"""

import requests
import time
import json
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"

def test_endpoint(name: str, method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint and return the response"""
    print(f"\n🧪 Testing {name}")
    print(f"📍 {method} {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Success: {json.dumps(result, indent=2)}")
            return result
        else:
            print(f"❌ Error: {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return None

def main():
    """Run all tests for the Echo Agent Service"""
    print("🎯 Echo Agent Service Test Suite")
    print("=" * 50)
    
    # Test 1: Root endpoint
    test_endpoint("Root Endpoint", "GET", f"{BASE_URL}/")
    
    # Test 2: Availability check
    test_endpoint("Availability Check", "GET", f"{BASE_URL}/availability")
    
    # Test 3: Input schema
    test_endpoint("Input Schema", "GET", f"{BASE_URL}/input_schema")
    
    # Test 4: Start a job
    job_data = {
        "input_data": [
            {"key": "text", "value": "Hello, Echo Agent! This is a test message."}
        ]
    }
    
    job_response = test_endpoint("Start Job", "POST", f"{BASE_URL}/start_job", job_data)
    
    if job_response and "job_id" in job_response:
        job_id = job_response["job_id"]
        print(f"\n🆔 Job ID: {job_id}")
        
        # Test 5: Check job status
        test_endpoint("Job Status", "GET", f"{BASE_URL}/status?job_id={job_id}")
        
        # Test 6: Check status again (should be completed)
        print("\n⏳ Waiting 2 seconds before checking status again...")
        time.sleep(2)
        test_endpoint("Job Status (Again)", "GET", f"{BASE_URL}/status?job_id={job_id}")
    
    # Test 7: Health check
    test_endpoint("Health Check", "GET", f"{BASE_URL}/health")
    
    # Test 8: List all jobs
    test_endpoint("List Jobs", "GET", f"{BASE_URL}/jobs")
    
    print("\n🎉 Test suite completed!")
    print("\n💡 Next steps:")
    print("   1. Install dependencies: pip install -e .")
    print("   2. Start the service: python echo_agent.py")
    print("   3. Run this test: python test_echo_agent.py")
    print("   4. Register with Masumi Registry")

if __name__ == "__main__":
    main() 